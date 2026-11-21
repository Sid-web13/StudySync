from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.deps import get_current_student
from app.models import Student, Subject, SyllabusTopic, Quiz, QuizAttempt, TopicStatus
from app.schemas import (
    AnalyticsSummary,
    SubjectAnalytics,
    TopicPerformance,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsSummary)
def get_analytics(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Computes real-time progress KPIs, subject breakdown, and categorizes
    topics into Weak (<70%) and Strong (>=70%) based on latest quiz mastery attempts.
    """
    subjects = (
        db.query(Subject)
        .filter(Subject.student_id == current_student.id)
        .order_by(Subject.id)
        .all()
    )

    all_topics = (
        db.query(SyllabusTopic)
        .join(Subject)
        .filter(Subject.student_id == current_student.id)
        .all()
    )
    total_topics_count = len(all_topics)
    completed_topics_count = sum(1 for t in all_topics if t.status == TopicStatus.COMPLETED)
    overall_completion_pct = (
        round((completed_topics_count / total_topics_count) * 100, 1)
        if total_topics_count > 0
        else 0.0
    )

    # Fetch attempts
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == current_student.id)
        .order_by(desc(QuizAttempt.created_at))
        .all()
    )

    total_quizzes = len(attempts)
    mean_score = (
        round(sum(a.score_percentage for a in attempts) / total_quizzes, 1)
        if total_quizzes > 0
        else 0.0
    )

    # Topic lookup map
    topic_map = {t.id: t for t in all_topics}
    subject_map = {s.id: s for s in subjects}

    # Latest quiz score per topic
    topic_latest_attempt: dict[int, QuizAttempt] = {}
    for att in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == att.quiz_id).first()
        if quiz and quiz.topic_id not in topic_latest_attempt:
            topic_latest_attempt[quiz.topic_id] = att

    weak_topics: list[TopicPerformance] = []
    strong_topics: list[TopicPerformance] = []

    for topic_id, att in topic_latest_attempt.items():
        topic = topic_map.get(topic_id)
        if not topic:
            continue
        sub = subject_map.get(topic.subject_id)
        sub_code = sub.code if sub else "GEN"
        sub_name = sub.name if sub else "General"

        perf = TopicPerformance(
            topic_id=topic.id,
            topic_title=topic.title,
            subject_code=sub_code,
            subject_name=sub_name,
            score_percentage=att.score_percentage,
            status=topic.status.value,
        )

        if att.score_percentage < 70.0:
            weak_topics.append(perf)
        else:
            strong_topics.append(perf)

    # Subject-wise analytics
    subject_analytics_list: list[SubjectAnalytics] = []
    for s in subjects:
        sub_topics = [t for t in all_topics if t.subject_id == s.id]
        total_sub_topics = len(sub_topics)
        comp_sub_topics = sum(1 for t in sub_topics if t.status == TopicStatus.COMPLETED)
        comp_pct = (
            round((comp_sub_topics / total_sub_topics) * 100, 1) if total_sub_topics > 0 else 0.0
        )

        # Calculate mean quiz score for this subject
        sub_topic_ids = {t.id for t in sub_topics}
        sub_attempts = [
            att
            for att in attempts
            if att.quiz and att.quiz.topic_id in sub_topic_ids
        ]
        sub_mean_score = (
            round(sum(a.score_percentage for a in sub_attempts) / len(sub_attempts), 1)
            if sub_attempts
            else None
        )

        subject_analytics_list.append(
            SubjectAnalytics(
                subject_id=s.id,
                code=s.code,
                name=s.name,
                total_topics=total_sub_topics,
                completed_topics=comp_sub_topics,
                completion_pct=comp_pct,
                mean_quiz_score=sub_mean_score,
            )
        )

    return AnalyticsSummary(
        overall_completion_pct=overall_completion_pct,
        total_quizzes=total_quizzes,
        mean_score=mean_score,
        subjects=subject_analytics_list,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
    )
