import asyncio
from datetime import datetime
import sqlite3
# =========================================================
# 🛠️ TOOLS (Dental Business Logic)
# =========================================================

async def check_availability(date: str, time: str):
    """Check if a dental slot is available."""
    def _query():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM appointments WHERE date = ? AND time = ?", (date, time))
        exists = cursor.fetchone()
        conn.close()
        return exists
    
    result = await asyncio.to_thread(_query)
    if result:
        return f"Sorry, {time} on {date} is already booked."
    return f"Yes, {date} at {time} is available."

async def book_appointment(name: str, phone: str, date: str, time: str, reason: str, urgency: str = "normal"):
    """Saves the booking and simulates SMS confirmation."""
    def _insert():
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO appointments (name, phone, date, time, reason, urgency) VALUES (?, ?, ?, ?, ?, ?)",
                (name, phone, date, time, reason, urgency)
            )
            conn.commit()
            conn.close()
            return True
        except Exception: return False

    success = await asyncio.to_thread(_insert)
    if success:
        return f"Confirmed! Booked {name} for {reason} on {date} at {time}. SMS sent."
    return "Error: Slot just became unavailable."

async def cancel_appointment(name: str, phone: str, date: str, reason: str = "Not specified"):
    """Cancels an existing appointment."""
    def _delete():
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE name = ? AND phone = ? AND date = ?", (name, phone, date))
            count = cursor.rowcount
            conn.commit()
            conn.close()
            return count > 0
        except Exception: return False

    success = await asyncio.to_thread(_delete)
    if success:
        return f"Confirmed. Your appointment on {date} has been cancelled. Reason noted: {reason}."
    return "I couldn't find an appointment matching those details to cancel."

async def reschedule_appointment(name: str, phone: str, old_date: str, new_date: str, new_time: str):
    """Updates an existing appointment to a new date and time."""
    def _update():
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM appointments WHERE name = ? AND phone = ? AND date = ?", (name, phone, old_date))
            record = cursor.fetchone()
            if not record:
                conn.close()
                return False, f"I couldn't find an appointment for {name} on {old_date}."
            
            appt_id = record[0]
            cursor.execute("SELECT id FROM appointments WHERE date = ? AND time = ? AND id != ?", (new_date, new_time, appt_id))
            if cursor.fetchone():
                conn.close()
                return False, f"I'm sorry, {new_time} on {new_date} is already taken."

            cursor.execute("UPDATE appointments SET date = ?, time = ?, status = 'rescheduled' WHERE id = ?", (new_date, new_time, appt_id))
            conn.commit()
            conn.close()
            return True, f"Success! The appointment for {name} has been moved to {new_date} at {new_time}."
        except Exception as e:
            return False, f"Database error: {str(e)}"

    success, message = await asyncio.to_thread(_update)
    return message

async def check_insurance(provider_name: str):
    """Verifies insurance acceptance."""
    accepted = ["delta dental", "aetna", "cigna", "metlife"]
    if provider_name.lower() in accepted:
        return f"Yes, we are in-network with {provider_name}. We can verify your specific plan during the visit."
    return f"We are not currently in-network with {provider_name}, but we can provide you with a superbill for out-of-network reimbursement."

async def log_doctor_message(patient_name: str, message: str):
    """Logs a message for the clinical team."""
    print(f"MESSAGE FOR DOCTOR FROM {patient_name}: {message}")
    return "I have logged that message for the doctor. They will review it and we will get back to you if needed."

async def request_human_handoff(reason: str):
    """Escalation trigger for emergencies or complaints."""
    print(f"!!! HANDOFF TRIGGERED: {reason} !!!")
    return "I understand this requires immediate attention. I am connecting you to our office manager now. Please hold."