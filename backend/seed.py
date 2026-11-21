import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models import Student, Subject, SyllabusTopic, Quiz, QuizQuestion, QuizAttempt, MentorMessage, TopicStatus


def seed_database():
    """
    Idempotent database seeder for StudySync.
    Seeds the evaluator demo account:
    siddharth@studysync.edu / Password@123
    with 3 subjects, 9 topics (3 completed, 3 in_progress, 3 not_started),
    1 pre-recorded quiz attempt on Normalization at 66.7%, and initial mentor guidance.
    """
    print("[StudySync Seed] Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        demo_email = "siddharth@studysync.edu"
        existing_student = db.query(Student).filter(Student.email == demo_email).first()

        if existing_student:
            print(f"[StudySync Seed] Student {demo_email} already exists. Removing old data for clean idempotent seed...")
            db.delete(existing_student)
            db.commit()

        print("[StudySync Seed] Creating evaluator account: Siddharth (B.Tech CSE, Sem 5)...")
        student = Student(
            name="Siddharth",
            email=demo_email,
            hashed_password=hash_password("Password@123"),
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # 1. Subject CS501: Database Management Systems
        sub_dbms = Subject(
            student_id=student.id,
            code="CS501",
            name="Database Management Systems",
        )
        db.add(sub_dbms)

        # 2. Subject CS502: Operating Systems
        sub_os = Subject(
            student_id=student.id,
            code="CS502",
            name="Operating Systems",
        )
        db.add(sub_os)

        # 3. Subject CS503: Computer Networks
        sub_cn = Subject(
            student_id=student.id,
            code="CS503",
            name="Computer Networks",
        )
        db.add(sub_cn)

        db.flush()

        # Seed 9 Topics across 3 subjects: exactly 3 completed, 3 in_progress, 3 not_started
        # CS501 Topics
        t_dbms_1 = SyllabusTopic(
            subject_id=sub_dbms.id,
            title="Relational Data Model & ER Diagrams",
            module_number="Module 1",
            status=TopicStatus.COMPLETED,
            order_index=0,
        )
        t_dbms_2 = SyllabusTopic(
            subject_id=sub_dbms.id,
            title="Functional Dependencies & Normalization",
            module_number="Module 2",
            status=TopicStatus.IN_PROGRESS,
            order_index=1,
        )
        t_dbms_3 = SyllabusTopic(
            subject_id=sub_dbms.id,
            title="Transaction Management & Concurrency Control",
            module_number="Module 3",
            status=TopicStatus.NOT_STARTED,
            order_index=2,
        )

        # CS502 Topics
        t_os_1 = SyllabusTopic(
            subject_id=sub_os.id,
            title="Process Management & CPU Scheduling",
            module_number="Module 1",
            status=TopicStatus.COMPLETED,
            order_index=0,
        )
        t_os_2 = SyllabusTopic(
            subject_id=sub_os.id,
            title="Concurrency: Semaphores & Deadlocks",
            module_number="Module 2",
            status=TopicStatus.IN_PROGRESS,
            order_index=1,
        )
        t_os_3 = SyllabusTopic(
            subject_id=sub_os.id,
            title="Memory Management & Virtual Paging",
            module_number="Module 3",
            status=TopicStatus.NOT_STARTED,
            order_index=2,
        )

        # CS503 Topics
        t_cn_1 = SyllabusTopic(
            subject_id=sub_cn.id,
            title="OSI & TCP/IP Protocol Architectures",
            module_number="Module 1",
            status=TopicStatus.COMPLETED,
            order_index=0,
        )
        t_cn_2 = SyllabusTopic(
            subject_id=sub_cn.id,
            title="Data Link Layer & IP Subnetting",
            module_number="Module 2",
            status=TopicStatus.IN_PROGRESS,
            order_index=1,
        )
        t_cn_3 = SyllabusTopic(
            subject_id=sub_cn.id,
            title="Transport Protocols: TCP Congestion Control",
            module_number="Module 3",
            status=TopicStatus.NOT_STARTED,
            order_index=2,
        )

        db.add_all([t_dbms_1, t_dbms_2, t_dbms_3, t_os_1, t_os_2, t_os_3, t_cn_1, t_cn_2, t_cn_3])
        db.flush()

        # Seed Pre-recorded Quiz and Attempt on "Functional Dependencies & Normalization"
        # Score = 2 / 3 = 66.7% (< 70%, identifying it as a weak topic)
        quiz_norm = Quiz(
            topic_id=t_dbms_2.id,
            title="Mastery Check: Functional Dependencies & Normalization",
        )
        db.add(quiz_norm)
        db.flush()

        q1 = QuizQuestion(
            quiz_id=quiz_norm.id,
            question_text="In relational database design, which normal form strictly eliminates transitive functional dependencies for non-prime attributes?",
            options=[
                "Third Normal Form (3NF)",
                "First Normal Form (1NF)",
                "Second Normal Form (2NF)",
                "Boyce-Codd Normal Form (BCNF)",
            ],
            correct_answer="Third Normal Form (3NF)",
            explanation="3NF requires relations to be in 2NF with no transitive dependencies between non-prime attributes.",
        )
        q2 = QuizQuestion(
            quiz_id=quiz_norm.id,
            question_text="Given a relation R with functional dependency X -> Y, what condition must hold for R to strictly satisfy Boyce-Codd Normal Form (BCNF)?",
            options=[
                "X must be a superkey of relation R",
                "Y must be a prime attribute part of a candidate key",
                "X must be atomic with zero repeating groups",
                "Relation R must contain no composite primary keys",
            ],
            correct_answer="X must be a superkey of relation R",
            explanation="BCNF dictates that for every non-trivial functional dependency X -> Y, the determinant X must be a superkey.",
        )
        q3 = QuizQuestion(
            quiz_id=quiz_norm.id,
            question_text="What is the primary operational trade-off of decomposing tables into higher normal forms like 3NF or BCNF?",
            options=[
                "Eliminates update anomalies but requires additional JOIN operations during reads",
                "Increases disk storage redundancy while speeding up write throughput",
                "Removes the necessity for foreign key constraint indexing",
                "Forces all numeric columns into floating-point representation",
            ],
            correct_answer="Eliminates update anomalies but requires additional JOIN operations during reads",
            explanation="Decomposition solves data redundancy and anomalies, but queries spanning entities require expensive relational JOINs.",
        )
        db.add_all([q1, q2, q3])
        db.flush()

        # Attempt: Student answered q1 correctly, q2 correctly, but q3 incorrectly -> 2/3 = 66.7%
        attempt = QuizAttempt(
            quiz_id=quiz_norm.id,
            student_id=student.id,
            score_percentage=66.7,
            score_raw=2,
            total_questions=3,
            answers_json={
                str(q1.id): "Third Normal Form (3NF)",
                str(q2.id): "X must be a superkey of relation R",
                str(q3.id): "Increases disk storage redundancy while speeding up write throughput",
            },
        )
        db.add(attempt)

        # Pre-seed initial Mentor conversation history
        mentor_welcome = MentorMessage(
            student_id=student.id,
            sender="mentor",
            content=(
                "• **Welcome Siddharth!** I am your StudySync Academic Mentor, linked directly to your Sem 5 curriculum.\n"
                "• **Live Diagnostic:** You scored **66.7%** on *Functional Dependencies & Normalization*. That makes it your primary target area.\n"
                "• **Immediate Action:** Review 3NF vs BCNF superkey constraints and re-attempt the quiz to hit the **80% mastery mark**!\n"
                "• How can I assist your revision sprint today?"
            ),
        )
        db.add(mentor_welcome)

        db.commit()
        print("[StudySync Seed] Successfully seeded evaluator demo database!")
        print("  - Student: Siddharth (siddharth@studysync.edu / Password@123)")
        print("  - Subjects: 3 (CS501, CS502, CS503)")
        print("  - Topics: 9 (3 Completed, 3 In Progress, 3 Not Started)")
        print("  - Weak Topics: 1 (Functional Dependencies & Normalization @ 66.7%)")
        print("  - Ready for evaluator demonstration!")

    except Exception as e:
        db.rollback()
        print(f"[StudySync Seed] Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
