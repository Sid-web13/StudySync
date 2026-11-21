from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Student, Subject, SyllabusTopic, Quiz, QuizAttempt, TopicStatus


def build_grounded_mentor_prompt(student: Student, db: Session, user_query: str) -> tuple[str, dict]:
    """
    Extracts real-time academic telemetry from SQLite for the authenticated student,
    computes completion ratios, weak topics (<70%), and constructs a grounded prompt
    for the AI Mentor.
    """
    # 1. Fetch enrolled subjects and their topics
    subjects = db.query(Subject).filter(Subject.student_id == student.id).all()
    enrolled_subject_strings = [f"{s.code}: {s.name}" for s in subjects]

    all_topics = (
        db.query(SyllabusTopic)
        .join(Subject)
        .filter(Subject.student_id == student.id)
        .all()
    )
    total_topics_count = len(all_topics)
    completed_topics_count = sum(1 for t in all_topics if t.status == TopicStatus.COMPLETED)
    syllabus_completion_pct = (
        round((completed_topics_count / total_topics_count) * 100, 1)
        if total_topics_count > 0
        else 0.0
    )

    # 2. Fetch quiz attempts to find weak (<70%) and strong (>=70%) topics
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == student.id)
        .order_by(desc(QuizAttempt.created_at))
        .all()
    )

    quizzes_taken = len(attempts)
    mean_quiz_score = (
        round(sum(a.score_percentage for a in attempts) / quizzes_taken, 1)
        if quizzes_taken > 0
        else 0.0
    )

    # Map each topic to its latest quiz attempt score
    topic_latest_scores: dict[int, float] = {}
    topic_lookup = {t.id: t for t in all_topics}

    for att in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == att.quiz_id).first()
        if quiz and quiz.topic_id not in topic_latest_scores:
            topic_latest_scores[quiz.topic_id] = att.score_percentage

    weak_topic_titles: list[str] = []
    strong_topic_titles: list[str] = []

    for topic_id, score in topic_latest_scores.items():
        topic = topic_lookup.get(topic_id)
        if topic:
            if score < 70.0:
                weak_topic_titles.append(f"{topic.title} ({score:.1f}%)")
            else:
                strong_topic_titles.append(f"{topic.title} ({score:.1f}%)")

    # If no quiz score recorded yet, mark any in_progress topics as focus areas
    if not weak_topic_titles:
        for t in all_topics:
            if t.status == TopicStatus.IN_PROGRESS:
                weak_topic_titles.append(f"{t.title} (In Progress)")

    telemetry = {
        "enrolled_subjects": enrolled_subject_strings,
        "completed_topics_count": completed_topics_count,
        "total_topics_count": total_topics_count,
        "syllabus_completion_pct": syllabus_completion_pct,
        "weak_topics": weak_topic_titles,
        "quizzes_taken": quizzes_taken,
        "mean_quiz_score": mean_quiz_score,
    }

    # 3. Build grounded prompt
    grounded_prompt = f"""
Student Academic Telemetry Snapshot:
- Student Name: {student.name}
- Enrolled Courses: {', '.join(enrolled_subject_strings) if enrolled_subject_strings else 'None'}
- Overall Syllabus Progress: {completed_topics_count}/{total_topics_count} topics completed ({syllabus_completion_pct}%)
- Quizzes Completed: {quizzes_taken} | Average Quiz Score: {mean_quiz_score}%
- Identified Weak Topics (<70% or Needs Revision): {', '.join(weak_topic_titles) if weak_topic_titles else 'None flagged yet'}
- Identified Strong Topics (>=70%): {', '.join(strong_topic_titles) if strong_topic_titles else 'None yet'}

Student Query:
"{user_query}"
""".strip()

    return grounded_prompt, telemetry
