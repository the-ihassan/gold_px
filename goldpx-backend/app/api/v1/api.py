from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, bookings, attachments, quotations, invoices, dashboard, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(attachments.router, prefix="/bookings", tags=["Booking Attachments"])
api_router.include_router(quotations.router, prefix="/bookings", tags=["Quotations"])
api_router.include_router(invoices.router, prefix="/bookings", tags=["Invoices & Payments"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
