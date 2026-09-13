"""HTTP routes for case management."""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.case_service import create_case, get_case, get_cases, update_case


router = APIRouter(prefix="/cases", tags=["cases"])
logger = logging.getLogger(__name__)


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(
    case_data: CaseCreate, db: Session = Depends(get_db)
) -> CaseResponse:
    case = create_case(db, case_data)
    logger.info(
        "case created",
        extra={"event": "case_created", "case_id": case.id},
    )
    return case


@router.get("", response_model=list[CaseResponse])
def list_cases(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1),
    db: Session = Depends(get_db),
) -> list[CaseResponse]:
    cases = get_cases(db, skip=skip, limit=limit)
    logger.info(
        "cases listed",
        extra={"event": "cases_listed", "count": len(cases)},
    )
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
def read_case(case_id: int, db: Session = Depends(get_db)) -> CaseResponse:
    case = get_case(db, case_id)
    logger.info(
        "case retrieved",
        extra={"event": "case_retrieved", "case_id": case_id},
    )
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
def edit_case(
    case_id: int, case_data: CaseUpdate, db: Session = Depends(get_db)
) -> CaseResponse:
    case = update_case(db, case_id, case_data)
    logger.info(
        "case updated",
        extra={
            "event": "case_updated",
            "case_id": case_id,
            "fields": list(case_data.model_dump(exclude_unset=True)),
        },
    )
    return case