"""Database-backed service functions for case management."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import CaseNotFoundError, DuplicateCaseNumberError
from app.db.models import Case
from app.schemas.case import CaseCreate, CaseUpdate

def _ensure_case_number_is_available(
    db: Session, case_number: str, current_case_id: int | None = None
) -> None:
    query = select(Case.id).where(Case.case_number == case_number)
    if current_case_id is not None:
        query = query.where(Case.id != current_case_id)

    if db.scalar(query) is not None:
        raise DuplicateCaseNumberError(
            f"Case number '{case_number}' is already in use."
        )


def create_case(db: Session, case_data: CaseCreate) -> Case:
    """Create and return a case from validated input data."""

    _ensure_case_number_is_available(db, case_data.case_number)
    case = Case(**case_data.model_dump())
    db.add(case)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCaseNumberError(
            f"Case number '{case.case_number}' is already in use."
        ) from exc

    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> Case:
    """Return a case by ID or raise CaseNotFoundError."""

    case = db.get(Case, case_id)
    if case is None:
        raise CaseNotFoundError(f"Case with id {case_id} was not found.")
    return case


def get_cases(db: Session, skip: int = 0, limit: int = 100) -> list[Case]:
    """Return cases in ID order with simple offset/limit pagination."""

    if skip < 0 or limit < 1:
        raise ValueError("skip must be non-negative and limit must be positive.")

    statement = select(Case).order_by(Case.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def update_case(db: Session, case_id: int, case_data: CaseUpdate) -> Case:
    """Apply validated partial updates and return the updated case."""

    case = get_case(db, case_id)
    changes = case_data.model_dump(exclude_unset=True)

    for field in ("case_number", "title", "status", "priority"):
        if field in changes and changes[field] is None:
            raise ValueError(f"{field} cannot be null.")

    if "case_number" in changes:
        _ensure_case_number_is_available(db, changes["case_number"], case_id)

    for field, value in changes.items():
        setattr(case, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCaseNumberError(
            f"Case number '{case.case_number}' is already in use."
        ) from exc

    db.refresh(case)
    return case