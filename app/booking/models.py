from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database import Base



class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, index=True)

    appointment_datetime = Column(DateTime, nullable=False)

    confirmed = Column(Boolean, default=True)
    reminder_sent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Appointment("
            f"id={self.id}, "
            f"patient_name={self.patient_name}, "
            f"appointment_datetime={self.appointment_datetime}"
            f")>"
        )
