from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.deps import get_current_student
from app.models import Student, Subject, SyllabusTopic, Quiz, QuizAttempt, TopicStatus
from app.schemas import (
    SubjectCreate,
    SubjectOut,
    SubjectWithTopicsOut,
    TopicCreate,
    TopicOut,
    TopicStatusUpdate,
)

router = APIRouter(prefix="/syllabus", tags=["Syllabus"])


@router.get("", response_model=list[SubjectWithTopicsOut])
def get_syllabus(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Retrieves all subjects, enrolled topics, and latest quiz performance for the student."""
    subjects = (
        db.query(Subject)
        .filter(Subject.student_id == current_student.id)
        .order_by(Subject.id)
        .all()
    )

    # Pre-fetch all attempts for this student to associate latest score per topic
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == current_student.id)
        .order_by(desc(QuizAttempt.created_at))
        .all()
    )

    topic_latest_scores: dict[int, float] = {}
    for att in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == att.quiz_id).first()
        if quiz and quiz.topic_id not in topic_latest_scores:
            topic_latest_scores[quiz.topic_id] = att.score_percentage

    result = []
    for sub in subjects:
        topics_out = []
        completed_count = 0
        for topic in sub.topics:
            if topic.status == TopicStatus.COMPLETED:
                completed_count += 1
            t_dict = TopicOut(
                id=topic.id,
                subject_id=topic.subject_id,
                title=topic.title,
                module_number=topic.module_number,
                status=topic.status,
                order_index=topic.order_index,
                created_at=topic.created_at,
                latest_score=topic_latest_scores.get(topic.id),
            )
            topics_out.append(t_dict)

        total_topics = len(topics_out)
        completion_rate = (
            round((completed_count / total_topics) * 100, 1) if total_topics > 0 else 0.0
        )

        result.append(
            SubjectWithTopicsOut(
                id=sub.id,
                student_id=sub.student_id,
                code=sub.code,
                name=sub.name,
                created_at=sub.created_at,
                topics=topics_out,
                completion_rate=completion_rate,
            )
        )
    return result


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Creates a new subject under the student's curriculum."""
    new_sub = Subject(
        student_id=current_student.id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return SubjectOut.model_validate(new_sub)


@router.post("/subjects/{subject_id}/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
def add_topic_to_subject(
    subject_id: int,
    payload: TopicCreate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Adds a new module topic to an existing enrolled subject."""
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.student_id == current_student.id)
        .first()
    )
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    new_topic = SyllabusTopic(
        subject_id=subject.id,
        title=payload.title.strip(),
        module_number=payload.module_number.strip(),
        status=TopicStatus.NOT_STARTED,
        order_index=payload.order_index,
    )
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return TopicOut.model_validate(new_topic)


@router.patch("/topics/{topic_id}/status", response_model=TopicOut)
def update_topic_status(
    topic_id: int,
    payload: TopicStatusUpdate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """Updates the progress status of a specific syllabus topic."""
    topic = (
        db.query(SyllabusTopic)
        .join(Subject)
        .filter(SyllabusTopic.id == topic_id, Subject.student_id == current_student.id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    topic.status = payload.status
    db.commit()
    db.refresh(topic)

    # Retrieve latest score if any
    latest_att = (
        db.query(QuizAttempt)
        .join(Quiz)
        .filter(Quiz.topic_id == topic.id, QuizAttempt.student_id == current_student.id)
        .order_by(desc(QuizAttempt.created_at))
        .first()
    )
    latest_score = latest_att.score_percentage if latest_att else None

    return TopicOut(
        id=topic.id,
        subject_id=topic.subject_id,
        title=topic.title,
        module_number=topic.module_number,
        status=topic.status,
        order_index=topic.order_index,
        created_at=topic.created_at,
        latest_score=latest_score,
    )
