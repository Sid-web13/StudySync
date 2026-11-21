from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_student
from app.models import Student, Subject, SyllabusTopic, Quiz, QuizQuestion, QuizAttempt, TopicStatus
from app.schemas import (
    QuizOut,
    QuizQuestionOut,
    QuizSubmitRequest,
    QuizGradedResponse,
    QuestionGradingResult,
)
from app.services.llm_service import llm_service

router = APIRouter(prefix="/quiz", tags=["Quiz Engine"])


@router.post("/generate/{topic_id}", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def generate_quiz_for_topic(
    topic_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Generates a personalized 3-question MCQ quiz for a given topic using Gemini or fallback.
    Persists the quiz and questions in SQLite, returning the questions with answers omitted.
    """
    topic = (
        db.query(SyllabusTopic)
        .join(Subject)
        .filter(SyllabusTopic.id == topic_id, Subject.student_id == current_student.id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    subject = db.query(Subject).filter(Subject.id == topic.subject_id).first()
    subject_name = subject.name if subject else "Computer Science"

    generated_questions = llm_service.generate_quiz_questions(
        subject_name=subject_name,
        topic_title=topic.title,
        num_questions=3,
    )

    new_quiz = Quiz(
        topic_id=topic.id,
        title=f"Mastery Check: {topic.title}",
    )
    db.add(new_quiz)
    db.flush()

    question_objects = []
    questions_out = []
    for q_data in generated_questions:
        q_obj = QuizQuestion(
            quiz_id=new_quiz.id,
            question_text=q_data["question_text"],
            options=q_data["options"],
            correct_answer=q_data["correct_answer"],
            explanation=q_data["explanation"],
        )
        db.add(q_obj)
        question_objects.append(q_obj)

    db.commit()

    for q in question_objects:
        db.refresh(q)
        questions_out.append(
            QuizQuestionOut(
                id=q.id,
                question_text=q.question_text,
                options=q.options,
            )
        )

    return QuizOut(
        id=new_quiz.id,
        topic_id=topic.id,
        title=new_quiz.title,
        questions=questions_out,
    )


@router.post("/submit", response_model=QuizGradedResponse)
def submit_quiz(
    payload: QuizSubmitRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
):
    """
    Grades user answers server-side, records attempt, and automatically updates
    topic status to 'completed' if the student achieves the 80% mastery threshold.
    """
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    topic = (
        db.query(SyllabusTopic)
        .join(Subject)
        .filter(SyllabusTopic.id == quiz.topic_id, Subject.student_id == current_student.id)
        .first()
    )
    if not topic:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this quiz")

    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).all()
    if not questions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz has no questions")

    # Map student answers by question_id
    user_answers_map = {ans.question_id: ans.selected_answer.strip() for ans in payload.answers}

    score_raw = 0
    total_questions = len(questions)
    grading_results: list[QuestionGradingResult] = []

    for q in questions:
        selected = user_answers_map.get(q.id, "")
        is_correct = selected.lower() == q.correct_answer.strip().lower()
        if is_correct:
            score_raw += 1

        grading_results.append(
            QuestionGradingResult(
                question_id=q.id,
                question_text=q.question_text,
                selected_answer=selected if selected else "(No answer)",
                correct_answer=q.correct_answer,
                is_correct=is_correct,
                explanation=q.explanation,
            )
        )

    score_percentage = round((score_raw / total_questions) * 100, 1)
    passed = score_percentage >= 80.0

    # Auto-update syllabus topic status based on 80% threshold
    if passed:
        topic.status = TopicStatus.COMPLETED
    elif topic.status == TopicStatus.NOT_STARTED:
        topic.status = TopicStatus.IN_PROGRESS

    # Record the quiz attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=current_student.id,
        score_percentage=score_percentage,
        score_raw=score_raw,
        total_questions=total_questions,
        answers_json=user_answers_map,
    )
    db.add(attempt)
    db.commit()

    return QuizGradedResponse(
        quiz_id=quiz.id,
        score_raw=score_raw,
        total_questions=total_questions,
        score_percentage=score_percentage,
        passed=passed,
        topic_status_updated=topic.status.value,
        question_results=grading_results,
    )
