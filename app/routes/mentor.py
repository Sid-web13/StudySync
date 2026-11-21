from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.deps import get_current_student
from app.models import Student, MentorMessage
from app.schemas import (
    MentorChatRequest,
    MentorChatResponse,
    MentorMessageOut,
    GroundingTelemetry,
)
from app.services.llm_service import llm_service
from app.services.mentor_context import build_grounded_mentor_prompt

router = APIRouter(prefix="/mentor", tags=["AI Mentor"])


@router.get("/history", response_model=list[MentorMessageOut])
def get_chat_history(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Retrieves all past messages exchanged between the student and the AI Mentor."""
    messages = (
        db.query(MentorMessage)
        .filter(MentorMessage.student_id == current_student.id)
        .order_by(MentorMessage.created_at.asc())
        .all()
    )
    return [MentorMessageOut.model_validate(m) for m in messages]


@router.post("/chat", response_model=MentorChatResponse)
def mentor_chat(
    payload: MentorChatRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Handles student chat interaction with the grounded academic mentor.
    Injects real-time SQLite progress telemetry and conversation history.
    """
    # 1. Save student's query to message log
    user_msg = MentorMessage(
        student_id=current_student.id,
        sender="student",
        content=payload.message.strip(),
    )
    db.add(user_msg)
    db.commit()

    # 2. Extract live telemetry and construct grounded prompt
    grounded_prompt, telemetry = build_grounded_mentor_prompt(current_student, db, payload.message)

    # 3. Fetch last 6 conversation turns
    recent_records = (
        db.query(MentorMessage)
        .filter(MentorMessage.student_id == current_student.id)
        .order_by(desc(MentorMessage.created_at))
        .limit(6)
        .all()
    )
    recent_records.reverse()

    recent_messages = [
        {"role": "user" if m.sender == "student" else "assistant", "content": m.content}
        for m in recent_records
    ]

    # 4. Generate grounded mentor response
    reply_text = llm_service.mentor_chat(
        grounded_prompt=grounded_prompt,
        recent_messages=recent_messages,
        weak_topics=telemetry["weak_topics"],
    )

    # 5. Save assistant reply to message log
    assistant_msg = MentorMessage(
        student_id=current_student.id,
        sender="mentor",
        content=reply_text,
    )
    db.add(assistant_msg)
    db.commit()

    return MentorChatResponse(
        reply=reply_text,
        telemetry=GroundingTelemetry(**telemetry),
    )
