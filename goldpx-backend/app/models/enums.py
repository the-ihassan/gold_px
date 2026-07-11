import enum


class UserRole(str, enum.Enum):
    GUEST = "guest"
    CUSTOMER = "customer"
    STAFF = "staff"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Roles ranked low -> high for permission comparisons
ROLE_HIERARCHY = {
    UserRole.GUEST: 0,
    UserRole.CUSTOMER: 1,
    UserRole.STAFF: 2,
    UserRole.MANAGER: 3,
    UserRole.ADMIN: 4,
    UserRole.SUPER_ADMIN: 5,
}


class EventType(str, enum.Enum):
    WEDDING = "wedding"
    MEHNDI = "mehndi"
    WALIMA = "walima"
    ENGAGEMENT = "engagement"
    CORPORATE = "corporate"
    CONCERT = "concert"
    BIRTHDAY = "birthday"
    OTHER = "other"


class DecorationType(str, enum.Enum):
    FLORAL = "floral"
    THEMED = "themed"
    STAGE_SETUP = "stage_setup"
    WALKWAY = "walkway"
    OTHER = "other"


class LightingType(str, enum.Enum):
    WEDDING_LIGHTING = "wedding_lighting"
    STAGE_LIGHTING = "stage_lighting"
    ARCHITECTURAL_LIGHTING = "architectural_lighting"
    PIXEL_LED = "pixel_led"
    SMART_RGB = "smart_rgb"
    OTHER = "other"


class BookingStatus(str, enum.Enum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    QUOTATION_SENT = "quotation_sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"


class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
