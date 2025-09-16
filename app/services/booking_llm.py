from app.services.groq_llm import chat_completion
import datetime 
today_date = datetime.date.today()
print(today_date)
BOOKING_EXTRACTION_PROMPT = f"""
 Detect if the user wants to book an interview.
If yes, extract name, email, date, and time. The time must be in 24-hour HH:MM:SS format (e.g., 15:00:00).
If the time and date are not in HH:MM:SS format, try to normalize it to that format. For example, "tomorrow 3pm". the date becomes todays YYYY-MM-DD + 1, and time becomes 15:00:00.
Today's date is {today_date}.
Rules:
- If all fields are present and valid, respond exactly:
  BOOKING_READY: {{"name": "...", "email": "...", "date": "YYYY-MM-DD", "time": "HH:MM:SS"}}
- If booking intent is present but any field is missing or ambiguous, ask a single, clear question for the missing piece(s).
  Example: "Please provide your email."
- If there is no booking intent, respond exactly: NO_BOOKING

Don't do anyother thing just follow the above rules.
"""

def extract_booking_info(user_message: str) -> dict:
    messages = [
        {"role": "system", "content": BOOKING_EXTRACTION_PROMPT},
        {"role": "user", "content": user_message},
    ]
    response = chat_completion(messages)
    return response