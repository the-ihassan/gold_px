"""
Seeds the database with:
- One Super Admin (credentials from settings / .env)
- One Manager, one Staff member
- A handful of sample customers and bookings across different statuses

Run with: python scripts/seed_data.py
"""
import sys
import random
from datetime import date, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.booking import Booking
from app.models.enums import UserRole, EventType, DecorationType, LightingType, BookingStatus, PaymentStatus
from app.utils.reference import generate_reference


def get_or_create_user(db, email, full_name, role, password="Password123"):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        full_name=full_name, email=email, hashed_password=hash_password(password),
        role=role, is_active=True, is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created {role.value}: {email} / {password}")
    return user


def main():
    db = SessionLocal()
    try:
        super_admin = get_or_create_user(
            db, settings.FIRST_SUPERADMIN_EMAIL, "GOLD Px Super Admin",
            UserRole.SUPER_ADMIN, settings.FIRST_SUPERADMIN_PASSWORD,
        )
        manager = get_or_create_user(db, "manager@goldpx.com", "Operations Manager", UserRole.MANAGER)
        staff = get_or_create_user(db, "staff@goldpx.com", "Lighting Staff", UserRole.STAFF)

        sample_customers = [
            ("Ayesha Khan", "923001234567", "ayesha@example.com", "Lahore"),
            ("Bilal Ahmed", "923011234567", "bilal@example.com", "Islamabad"),
            ("Sana Tariq", "923021234567", "sana@example.com", "Rawalpindi"),
        ]

        event_types = list(EventType)
        statuses = list(BookingStatus)

        if db.query(Booking).count() == 0:
            for i, (name, phone, email, city) in enumerate(sample_customers):
                for j in range(2):
                    booking = Booking(
                        reference_no=generate_reference("GPX"),
                        customer_name=name,
                        phone=phone,
                        email=email,
                        city=city,
                        venue=f"{city} Marquee Hall {j+1}",
                        event_type=random.choice(event_types),
                        event_date=date.today() + timedelta(days=random.randint(5, 90)),
                        budget=random.choice([150000, 300000, 500000, 800000]),
                        decoration_type=random.choice(list(DecorationType)),
                        lighting_type=random.choice(list(LightingType)),
                        pixel_requirement="500 pixels, RGB smart controller",
                        special_notes="Seed sample booking",
                        status=random.choice(statuses[:5]),
                        payment_status=random.choice(list(PaymentStatus)),
                        assigned_staff_id=staff.id,
                    )
                    db.add(booking)
            db.commit()
            print("Seeded sample bookings.")
        else:
            print("Bookings already exist, skipping booking seed.")

        print("\nSeed complete. Login with:")
        print(f"  Super Admin: {settings.FIRST_SUPERADMIN_EMAIL} / {settings.FIRST_SUPERADMIN_PASSWORD}")
        print("  Manager:     manager@goldpx.com / Password123")
        print("  Staff:       staff@goldpx.com / Password123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
