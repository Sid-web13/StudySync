from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.deps import get_current_student
from app.models import Student, Subject, SyllabusTopic, TopicStatus
from app.schemas import StudentCreate, LoginRequest, Token, StudentOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

STARTER_CURRICULUM = [
    {
        "code": "CS501",
        "name": "Database Management Systems",
        "topics": [
            ("Relational Data Model & ER Diagrams", "Module 1"),
            ("Functional Dependencies & Normalization", "Module 2"),
            ("Transaction Management & Concurrency Control", "Module 3"),
        ],
    },
    {
        "code": "CS502",
        "name": "Operating Systems",
        "topics": [
            ("Process Management & CPU Scheduling", "Module 1"),
            ("Concurrency: Semaphores & Deadlocks", "Module 2"),
            ("Memory Management & Virtual Paging", "Module 3"),
        ],
    },
    {
        "code": "CS503",
        "name": "Computer Networks",
        "topics": [
            ("OSI & TCP/IP Protocol Architectures", "Module 1"),
            ("Data Link Layer & IP Subnetting", "Module 2"),
            ("Transport Protocols: TCP Congestion Control", "Module 3"),
        ],
    },
]


def seed_starter_subjects_for_student(db: Session, student_id: int):
    """Auto-seeds core standard curriculum so each student starts with active subjects."""
    for sub_data in STARTER_CURRICULUM:
        subject = Subject(
            student_id=student_id,
            code=sub_data["code"],
            name=sub_data["name"],
        )
        db.add(subject)
        db.flush()  # Populates subject.id

        for idx, (title, module_num) in enumerate(sub_data["topics"]):
            topic = SyllabusTopic(
                subject_id=subject.id,
                title=title,
                module_number=module_num,
                status=TopicStatus.NOT_STARTED,
                order_index=idx,
            )
            db.add(topic)
    db.commit()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(payload: StudentCreate, db: Session = Depends(get_db)):
    """Registers a new student account, auto-provisions starter curriculum, and returns JWT."""
    existing = db.query(Student).filter(Student.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    new_student = Student(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    # Seed starter curriculum
    seed_starter_subjects_for_student(db, new_student.id)

    access_token = create_access_token(data={"sub": str(new_student.id), "email": new_student.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        student=StudentOut.model_validate(new_student),
    )


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates student credentials and returns a signed JWT access token."""
    student = db.query(Student).filter(Student.email == payload.email.lower().strip()).first()
    if not student or not verify_password(payload.password, student.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(student.id), "email": student.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        student=StudentOut.model_validate(student),
    )


@router.get("/me", response_model=StudentOut)
def get_current_user(current_student: Student = Depends(get_current_student)):
    """Returns the authenticated student's profile."""
    return StudentOut.model_validate(current_student)
