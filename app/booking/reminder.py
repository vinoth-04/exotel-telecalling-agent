from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.booking.models import Appointment


def send_reminder(appointment: Appointment):
    """
    Send reminder to the patient.
    (Later: replace print with Exotel SMS / Call)
    """
    print(
        f"🔔 Reminder sent to {appointment.phone_number} "
        f"for appointment at {appointment.appointment_datetime}"
    )


def reminder_job():
    """
    Runs every minute.
    Finds appointments happening in next 1 hour.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        one_hour_later = now + timedelta(hours=1)

        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.confirmed == True,
                Appointment.reminder_sent == False,
                Appointment.appointment_datetime <= one_hour_later,
                Appointment.appointment_datetime > now,
            )
            .all()
        )

        for appt in appointments:
            send_reminder(appt)
            appt.reminder_sent = True

        db.commit()

    except Exception as e:
        db.rollback()
        print("❌ Reminder job error:", e)

    finally:
        db.close()


def start_scheduler():
    """
    Start background scheduler.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(reminder_job, "interval", minutes=1)
    scheduler.start()

    print("⏰ Reminder scheduler started")
