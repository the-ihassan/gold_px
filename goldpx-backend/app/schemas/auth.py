import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, min_length=7, max_length=20)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str  # Google-issued ID token, verified server-side


class OTPRequestSchema(BaseModel):
    identifier: str = Field(description="Phone number or email to send the OTP to")


class OTPVerifySchema(BaseModel):
    identifier: str
    code: str = Field(min_length=4, max_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool
    avatar_url: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True
