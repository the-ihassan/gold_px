import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.auth_tokens import OTPCode, EmailVerificationToken, PasswordResetToken, RefreshToken
from app.models.enums import UserRole
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token,
)
from app.schemas.auth import (
    SignupRequest, LoginRequest, GoogleLoginRequest, OTPRequestSchema, OTPVerifySchema,
    ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest,
    TokenResponse, RefreshTokenRequest, UserOut,
)
from app.api.deps import get_current_user
from app.services.email_service import send_email
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

OTP_EXPIRE_MINUTES = 10
RESET_TOKEN_EXPIRE_MINUTES = 30


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access = create_access_token(user.id, user.role.value)
    refresh = create_refresh_token(user.id)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=pwd_context.hash(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    ))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Fire-and-forget verification email (logs only until SMTP configured)
    background_tasks.add_task(
        lambda: None  # placeholder hook; wire to send_verification_email() once SMTP is live
    )

    return _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    return _issue_tokens(db, user)


@router.post("/google", response_model=TokenResponse)
async def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Verifies the Google ID token against Google's tokeninfo endpoint and
    creates/logs in the corresponding user. No server-side Google client
    secret is required for ID-token verification.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo", params={"id_token": payload.id_token}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    data = resp.json()
    google_id = data.get("sub")
    email = data.get("email")
    full_name = data.get("name", email)
    avatar_url = data.get("picture")

    if not google_id or not email:
        raise HTTPException(status_code=401, detail="Google token missing required claims")

    user = db.scalar(select(User).where(User.google_id == google_id))
    if not user:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.google_id = google_id
        else:
            user = User(
                full_name=full_name,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                role=UserRole.CUSTOMER,
                is_email_verified=True,
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    return _issue_tokens(db, user)


@router.post("/otp/request")
def request_otp(payload: OTPRequestSchema, db: Session = Depends(get_db)):
    code = f"{random.randint(0, 999999):06d}"
    otp = OTPCode(
        identifier=payload.identifier,
        code_hash=pwd_context.hash(code),
        purpose="login",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(otp)
    db.commit()

    # No SMS/WhatsApp API key configured yet -> log the code server-side.
    # Swap this for a real SMS/WhatsApp API send once credentials exist.
    import logging
    logging.getLogger("goldpx.otp").warning(
        "OTP for %s is %s (valid %s minutes) - SMS provider not configured, logging instead",
        payload.identifier, code, OTP_EXPIRE_MINUTES,
    )
    return {"message": "OTP generated. Check server logs (SMS/WhatsApp provider not yet configured)."}


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(payload: OTPVerifySchema, db: Session = Depends(get_db)):
    otp = db.scalar(
        select(OTPCode)
        .where(OTPCode.identifier == payload.identifier, OTPCode.is_used == False)  # noqa: E712
        .order_by(OTPCode.created_at.desc())
    )
    if not otp or otp.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired or not found")
    if otp.attempts >= 5:
        raise HTTPException(status_code=429, detail="Too many attempts, request a new OTP")
    if not pwd_context.verify(payload.code, otp.code_hash):
        otp.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    otp.is_used = True

    user = db.scalar(select(User).where(
        (User.email == payload.identifier) | (User.phone == payload.identifier)
    ))
    if not user:
        user = User(
            full_name=payload.identifier,
            email=payload.identifier if "@" in payload.identifier else f"{payload.identifier}@placeholder.goldpx.com",
            phone=payload.identifier if "@" not in payload.identifier else None,
            role=UserRole.CUSTOMER,
            is_phone_verified="@" not in payload.identifier,
        )
        db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(db, user)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    # Always return 200 to avoid leaking which emails are registered
    if user:
        raw_token = uuid.uuid4().hex
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=pwd_context.hash(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
        ))
        db.commit()
        import logging
        logging.getLogger("goldpx.auth").warning(
            "Password reset token for %s: %s (SMTP not configured, logging instead)",
            user.email, raw_token,
        )
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    candidates = db.scalars(
        select(PasswordResetToken)
        .where(PasswordResetToken.is_used == False)  # noqa: E712
        .order_by(PasswordResetToken.created_at.desc())
    ).all()

    match = next(
        (t for t in candidates if t.expires_at > datetime.now(timezone.utc) and pwd_context.verify(payload.token, t.token_hash)),
        None,
    )
    if not match:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.get(User, match.user_id)
    user.hashed_password = hash_password(payload.new_password)
    match.is_used = True
    db.commit()
    return {"message": "Password reset successful"}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    candidates = db.scalars(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.is_used == False)  # noqa: E712
    ).all()
    match = next(
        (t for t in candidates if t.expires_at > datetime.now(timezone.utc) and pwd_context.verify(payload.token, t.token_hash)),
        None,
    )
    if not match:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user = db.get(User, match.user_id)
    user.is_email_verified = True
    match.is_used = True
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = db.get(User, uuid.UUID(decoded["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return _issue_tokens(db, user)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
