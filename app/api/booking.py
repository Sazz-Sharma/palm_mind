from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db.session import get_session
from app.models.schemas import BookingCreate, BookingResponse
from app.models.db_models import InterviewBooking

router = APIRouter(prefix="/booking", tags=["booking"])

@router.post("", response_model=BookingResponse)
def create_booking(payload: BookingCreate, session: Session = Depends(get_session)) -> BookingResponse:
    booking = InterviewBooking(
        name=payload.name,
        email=payload.email,
        date=payload.date,
        time=payload.time,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return BookingResponse(
        id=booking.id,
        name=booking.name,
        email=booking.email,
        date=booking.date,
        time=booking.time,
    )