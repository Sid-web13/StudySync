import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Student, Subject, SyllabusTopic, TopicStatus
from app.core.security import hash_password

# Isolated in-memory SQLite database for test suite
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_health_check():
    """1. Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "StudySync API"
    assert "database" in data
    assert "ai_engine" in data


def test_student_signup_and_duplicate():
    """2. Test student signup with automatic starter curriculum and duplicate email rejection."""
    payload = {
        "name": "Aarav Sharma",
        "email": "aarav@studysync.edu",
        "password": "SecurePassword123",
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["student"]["email"] == "aarav@studysync.edu"
    assert data["student"]["name"] == "Aarav Sharma"

    # Attempt duplicate signup
    dup_res = client.post("/auth/signup", json=payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]


def test_student_login_and_auth_me():
    """3. Test student login, JWT token decoding, and GET /auth/me."""
    signup_payload = {
        "name": "Priya Patel",
        "email": "priya@studysync.edu",
        "password": "Password123",
    }
    client.post("/auth/signup", json=signup_payload)

    # Valid Login
    login_res = client.post(
        "/auth/login",
        json={"email": "priya@studysync.edu", "password": "Password123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid Login
    invalid_res = client.post(
        "/auth/login",
        json={"email": "priya@studysync.edu", "password": "WrongPassword"},
    )
    assert invalid_res.status_code == 401

    # Verify Profile via /auth/me
    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "priya@studysync.edu"
    assert me_res.json()["name"] == "Priya Patel"


def test_syllabus_crud_and_status_patch():
    """4. Test syllabus retrieval, custom subject/topic addition, and status updates."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Rohan", "email": "rohan@studysync.edu", "password": "Pass123456"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch auto-seeded curriculum
    res = client.get("/syllabus", headers=headers)
    assert res.status_code == 200
    curriculum = res.json()
    assert len(curriculum) == 3  # DBMS, OS, CN
    first_subject = curriculum[0]
    assert len(first_subject["topics"]) == 3
    first_topic = first_subject["topics"][0]
    assert first_topic["status"] == "not_started"

    # Add custom subject
    new_sub_res = client.post(
        "/syllabus/subjects",
        json={"code": "CS504", "name": "Compiler Design"},
        headers=headers,
    )
    assert new_sub_res.status_code == 201
    new_sub = new_sub_res.json()
    assert new_sub["code"] == "CS504"

    # Add custom topic to new subject
    new_topic_res = client.post(
        f"/syllabus/subjects/{new_sub['id']}/topics",
        json={"title": "Lexical Analysis & Flex", "module_number": "Module 1", "order_index": 0},
        headers=headers,
    )
    assert new_topic_res.status_code == 201
    new_topic = new_topic_res.json()
    assert new_topic["title"] == "Lexical Analysis & Flex"

    # Patch topic status to 'in_progress'
    patch_res = client.patch(
        f"/syllabus/topics/{new_topic['id']}/status",
        json={"status": "in_progress"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "in_progress"

    # Patch topic status to 'completed'
    patch_comp_res = client.patch(
        f"/syllabus/topics/{new_topic['id']}/status",
        json={"status": "completed"},
        headers=headers,
    )
    assert patch_comp_res.status_code == 200
    assert patch_comp_res.json()["status"] == "completed"


def test_ai_quiz_generation_anti_cheat():
    """5. Test AI quiz generation and ensure correct_answer is strictly omitted in client schema."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Dev", "email": "dev@studysync.edu", "password": "Password123"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    syl_res = client.get("/syllabus", headers=headers)
    first_topic_id = syl_res.json()[0]["topics"][0]["id"]

    # Generate Quiz
    quiz_res = client.post(f"/quiz/generate/{first_topic_id}", headers=headers)
    assert quiz_res.status_code == 201
    quiz_data = quiz_res.json()
    assert "id" in quiz_data
    assert quiz_data["topic_id"] == first_topic_id
    assert len(quiz_data["questions"]) == 3

    # CRUCIAL ANTI-CHEAT VERIFICATION:
    for q in quiz_data["questions"]:
        assert len(q["options"]) == 4
        assert "correct_answer" not in q, "Anti-cheat failed: correct_answer leaked to client!"
        assert "explanation" not in q, "Anti-cheat failed: explanation leaked before submission!"


def test_quiz_submit_mastery_and_topic_auto_promotion():
    """6. Test server-side grading and automatic topic status promotion on >= 80% mastery."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Kavya", "email": "kavya@studysync.edu", "password": "Password123"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    syl_res = client.get("/syllabus", headers=headers)
    topic_id = syl_res.json()[0]["topics"][0]["id"]

    # Generate quiz
    quiz_res = client.post(f"/quiz/generate/{topic_id}", headers=headers)
    quiz_data = quiz_res.json()
    quiz_id = quiz_data["id"]
    q_ids = [q["id"] for q in quiz_data["questions"]]

    # Submit with intentional wrong answers to test failure (< 80%)
    fail_submission = {
        "quiz_id": quiz_id,
        "answers": [
            {"question_id": q_ids[0], "selected_answer": "Definitely Wrong Answer"},
            {"question_id": q_ids[1], "selected_answer": "Another Wrong Answer"},
            {"question_id": q_ids[2], "selected_answer": "Third Wrong Answer"},
        ],
    }
    fail_res = client.post("/quiz/submit", json=fail_submission, headers=headers)
    assert fail_res.status_code == 200
    fail_data = fail_res.json()
    assert fail_data["score_raw"] == 0
    assert fail_data["score_percentage"] == 0.0
    assert fail_data["passed"] is False
    assert fail_data["topic_status_updated"] == "in_progress"

    # Verify topic is now 'in_progress'
    syl_check = client.get("/syllabus", headers=headers)
    assert syl_check.json()[0]["topics"][0]["status"] == "in_progress"

    # Now inspect internal DB questions to submit 100% correct answers to verify >= 80% promotion
    db = TestingSessionLocal()
    from app.models import QuizQuestion
    db_questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
    correct_submission = {
        "quiz_id": quiz_id,
        "answers": [
            {"question_id": q.id, "selected_answer": q.correct_answer}
            for q in db_questions
        ],
    }
    db.close()

    pass_res = client.post("/quiz/submit", json=correct_submission, headers=headers)
    assert pass_res.status_code == 200
    pass_data = pass_res.json()
    assert pass_data["score_raw"] == 3
    assert pass_data["score_percentage"] == 100.0
    assert pass_data["passed"] is True
    assert pass_data["topic_status_updated"] == "completed"

    # Verify topic is now auto-promoted to 'completed'
    syl_check2 = client.get("/syllabus", headers=headers)
    assert syl_check2.json()[0]["topics"][0]["status"] == "completed"


def test_grounded_mentor_chat_and_telemetry():
    """7. Test grounded AI mentor chat, word limit (<150 words), and telemetry metadata."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Siddharth", "email": "sid@studysync.edu", "password": "Password@123"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query mentor
    chat_payload = {"message": "How do I prepare for Database Normalization?"}
    chat_res = client.post("/mentor/chat", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    reply = chat_data["reply"]
    telemetry = chat_data["telemetry"]

    # Constraints verification
    assert len(reply.split()) <= 150, f"Mentor reply exceeded 150 words: {len(reply.split())}"
    assert "•" in reply or "-" in reply, "Mentor reply must be formatted in bullet points"
    assert "80%" in reply, "Mentor reply must encourage reaching the 80% mastery mark"

    # Grounding telemetry verification
    assert len(telemetry["enrolled_subjects"]) == 3
    assert telemetry["total_topics_count"] == 9
    assert "weak_topics" in telemetry

    # Verify history
    hist_res = client.get("/mentor/history", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2
    assert history[-2]["sender"] == "student"
    assert history[-1]["sender"] == "mentor"


def test_analytics_breakdown():
    """8. Test analytics summary endpoint for weak vs strong topic categorization."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Neha", "email": "neha@studysync.edu", "password": "Password123"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    analytics_res = client.get("/analytics", headers=headers)
    assert analytics_res.status_code == 200
    data = analytics_res.json()
    assert "overall_completion_pct" in data
    assert "total_quizzes" in data
    assert "mean_score" in data
    assert len(data["subjects"]) == 3
    assert isinstance(data["weak_topics"], list)
    assert isinstance(data["strong_topics"], list)


def test_unauthorized_endpoints():
    """9. Test that secure endpoints strictly reject requests without Bearer authorization."""
    unauth_headers = {}
    assert client.get("/auth/me", headers=unauth_headers).status_code == 401
    assert client.get("/syllabus", headers=unauth_headers).status_code == 401
    assert client.get("/mentor/history", headers=unauth_headers).status_code == 401
    assert client.get("/analytics", headers=unauth_headers).status_code == 401


def test_topic_not_found_isolation():
    """10. Test cross-tenant security: requesting or modifying non-existent or other user topics returns 404."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Karan", "email": "karan@studysync.edu", "password": "Password123"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to generate quiz for non-existent topic ID 99999
    res = client.post("/quiz/generate/99999", headers=headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "Topic not found"

    # Attempt to patch non-existent topic ID 99999
    patch_res = client.patch(
        "/syllabus/topics/99999/status",
        json={"status": "completed"},
        headers=headers,
    )
    assert patch_res.status_code == 404


def test_offline_fallback_determinism():
    """11. Test deterministic fallback questions adhere to 4 unique options and exact correct_answer match."""
    from app.services.llm_service import llm_service

    # Test DBMS fallback
    questions = llm_service.generate_quiz_questions(
        subject_name="Database Management Systems",
        topic_title="Functional Dependencies & Normalization",
        num_questions=3,
    )
    assert len(questions) == 3
    for q in questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert q["correct_answer"] in q["options"]
        assert len(q["explanation"]) > 10

    # Test Generic fallback
    gen_questions = llm_service.generate_quiz_questions(
        subject_name="Distributed Cloud Computing",
        topic_title="Raft Consensus Algorithm",
        num_questions=3,
    )
    assert len(gen_questions) == 3
    for q in gen_questions:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert q["correct_answer"] in q["options"]


def test_cascading_deletes_integrity():
    """12. Test database cascading deletes on student deletion."""
    signup_res = client.post(
        "/auth/signup",
        json={"name": "Tanvi", "email": "tanvi@studysync.edu", "password": "Password123"},
    )
    student_id = signup_res.json()["student"]["id"]

    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.id == student_id).first()
    assert student is not None
    # Verify child subjects were created
    subs = db.query(Subject).filter(Subject.student_id == student_id).all()
    assert len(subs) == 3
    sub_ids = [s.id for s in subs]

    # Delete student
    db.delete(student)
    db.commit()

    # Verify cascading deletion of subjects and topics
    orphaned_subs = db.query(Subject).filter(Subject.student_id == student_id).all()
    assert len(orphaned_subs) == 0

    orphaned_topics = (
        db.query(SyllabusTopic)
        .filter(SyllabusTopic.subject_id.in_(sub_ids))
        .all()
    )
    assert len(orphaned_topics) == 0
    db.close()

