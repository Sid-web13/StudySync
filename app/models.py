from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TopicStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships with cascading deletes
    subjects = relationship(
        "Subject",
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    quiz_attempts = relationship(
        "QuizAttempt",
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    mentor_messages = relationship(
        "MentorMessage",
        back_populates="student",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="subjects")
    topics = relationship(
        "SyllabusTopic",
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SyllabusTopic.order_index",
    )


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(200), nullable=False)
    module_number = Column(String(50), default="Module 1", nullable=False)
    status = Column(
        SQLEnum(TopicStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=TopicStatus.NOT_STARTED,
        nullable=False,
    )
    order_index = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    subject = relationship("Subject", back_populates="topics")
    quizzes = relationship(
        "Quiz",
        back_populates="topic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(
        Integer,
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    topic = relationship("SyllabusTopic", back_populates="quizzes")
    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attempts = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(
        Integer,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # JSON Array of 4 string options
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(
        Integer,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score_percentage = Column(Float, nullable=False)
    score_raw = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    answers_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")


class MentorMessage(Base):
    __tablename__ = "mentor_messages"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender = Column(String(20), nullable=False)  # 'student' or 'mentor'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="mentor_messages")
