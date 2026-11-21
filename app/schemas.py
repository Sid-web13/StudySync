from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import TopicStatus


# ==========================================
# Authentication & Student Schemas
# ==========================================

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentOut


class TokenData(BaseModel):
    email: Optional[str] = None
    student_id: Optional[int] = None


# ==========================================
# Syllabus & Topic Schemas
# ==========================================

class TopicCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    module_number: str = Field(default="Module 1", max_length=50)
    order_index: int = 0


class TopicStatusUpdate(BaseModel):
    status: TopicStatus


class TopicOut(BaseModel):
    id: int
    subject_id: int
    title: str
    module_number: str
    status: TopicStatus
    order_index: int
    created_at: datetime
    latest_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)


class SubjectOut(BaseModel):
    id: int
    student_id: int
    code: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubjectWithTopicsOut(SubjectOut):
    topics: list[TopicOut] = []
    completion_rate: float = 0.0


# ==========================================
# Quiz Schemas
# ==========================================

class QuizQuestionOut(BaseModel):
    """Client-facing question representation; strictly omits correct_answer and explanation to prevent cheating."""
    id: int
    question_text: str
    options: list[str]

    model_config = ConfigDict(from_attributes=True)


class QuizOut(BaseModel):
    id: int
    topic_id: int
    title: str
    questions: list[QuizQuestionOut]

    model_config = ConfigDict(from_attributes=True)


class QuizSubmitAnswer(BaseModel):
    question_id: int
    selected_answer: str


class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: list[QuizSubmitAnswer]


class QuestionGradingResult(BaseModel):
    question_id: int
    question_text: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class QuizGradedResponse(BaseModel):
    quiz_id: int
    score_raw: int
    total_questions: int
    score_percentage: float
    passed: bool
    topic_status_updated: str
    question_results: list[QuestionGradingResult]


class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    score_percentage: float
    score_raw: int
    total_questions: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Mentor & Chat Schemas
# ==========================================

class MentorMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class MentorMessageOut(BaseModel):
    id: int
    sender: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroundingTelemetry(BaseModel):
    enrolled_subjects: list[str]
    completed_topics_count: int
    total_topics_count: int
    syllabus_completion_pct: float
    weak_topics: list[str]
    quizzes_taken: int
    mean_quiz_score: float


class MentorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class MentorChatResponse(BaseModel):
    reply: str
    telemetry: GroundingTelemetry


# ==========================================
# Analytics Schemas
# ==========================================

class TopicPerformance(BaseModel):
    topic_id: int
    topic_title: str
    subject_code: str
    subject_name: str
    score_percentage: float
    status: str


class SubjectAnalytics(BaseModel):
    subject_id: int
    code: str
    name: str
    total_topics: int
    completed_topics: int
    completion_pct: float
    mean_quiz_score: Optional[float] = None


class AnalyticsSummary(BaseModel):
    overall_completion_pct: float
    total_quizzes: int
    mean_score: float
    subjects: list[SubjectAnalytics]
    weak_topics: list[TopicPerformance]
    strong_topics: list[TopicPerformance]
