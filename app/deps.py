from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Student

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Student:
    """Dependency to retrieve the authenticated student from a valid JWT Bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    student_id = payload.get("sub")
    if student_id is None:
        raise credentials_exception

    try:
        student_id_int = int(student_id)
    except (ValueError, TypeError):
        raise credentials_exception

    student = db.query(Student).filter(Student.id == student_id_int).first()
    if student is None:
        raise credentials_exception

    return student
