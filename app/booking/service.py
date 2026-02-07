from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.booking.models import Appointment


def get_db() -> Session:
    """
    Create and return a new database session.
    Caller is responsible for closing it.
    """
    return SessionLocal()


def save_appointment(
    patient_name: str,
    phone_number: str,
    appointment_datetime: datetime,
) -> Appointment:
    """
    Save a confirmed appointment to the database.
    """
    db = get_db()
    try:
        appointment = Appointment(
            patient_name=patient_name,
            phone_number=phone_number,
            appointment_datetime=appointment_datetime,
            confirmed=True,
            reminder_sent=False,
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return appointment

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()


def is_slot_available(appointment_datetime: datetime) -> bool:
    """
    Check if an appointment slot is available.
    """
    db = get_db()
    try:
        existing = (
            db.query(Appointment)
            .filter(
                Appointment.appointment_datetime == appointment_datetime,
                Appointment.confirmed == True,
            )
            .first()
        )

        return existing is None

    finally:
        db.close()
