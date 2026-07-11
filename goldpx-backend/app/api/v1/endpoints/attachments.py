import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.booking import Booking, BookingAttachment
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.booking import BookingAttachmentOut
from app.api.deps import get_current_user
from app.services.storage_service import upload_file
from app.services.booking_service import add_timeline_event

router = APIRouter()


@router.post("/{booking_id}/attachments", response_model=BookingAttachmentOut, status_code=201)
def upload_booking_attachment(
    booking_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    is_staff = current_user.role in (UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not is_staff and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot upload files to this booking")

    result = upload_file(file, subfolder=f"bookings/{booking_id}")

    attachment = BookingAttachment(
        booking_id=booking.id,
        file_url=result["url"],
        file_name=result["file_name"],
        file_type=result["file_type"],
        uploaded_by_id=current_user.id,
    )
    db.add(attachment)
    add_timeline_event(
        db, booking, event_type="note", title="Attachment uploaded",
        description=result["file_name"], actor_id=current_user.id,
    )
    db.commit()
    db.refresh(attachment)
    return attachment


@router.delete("/{booking_id}/attachments/{attachment_id}", status_code=204)
def delete_booking_attachment(
    booking_id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attachment = db.get(BookingAttachment, attachment_id)
    if not attachment or attachment.booking_id != booking_id:
        raise HTTPException(status_code=404, detail="Attachment not found")

    is_staff = current_user.role in (UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not is_staff and attachment.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot delete this attachment")

    db.delete(attachment)
    db.commit()
    return None
