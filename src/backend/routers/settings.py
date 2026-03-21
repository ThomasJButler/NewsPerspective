import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Setting
from ..schemas import GuardrailsResponse, GuardrailsUpdateRequest
from ..utils.good_news import CUSTOM_GUARDRAILS_SETTING_KEY, load_custom_guardrail_keywords

router = APIRouter(prefix="/api/settings", tags=["settings"])

MAX_CUSTOM_KEYWORDS = 50
MAX_KEYWORD_LENGTH = 100


@router.get("/guardrails", response_model=GuardrailsResponse)
def get_guardrails(db: Session = Depends(get_db)) -> GuardrailsResponse:
    keywords = load_custom_guardrail_keywords(db)
    return GuardrailsResponse(keywords=keywords)


@router.put("/guardrails", response_model=GuardrailsResponse)
def update_guardrails(
    body: GuardrailsUpdateRequest,
    db: Session = Depends(get_db),
) -> GuardrailsResponse:
    # Normalize: strip whitespace, lowercase, deduplicate, drop blanks.
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in body.keywords:
        kw = raw.strip().lower()
        if kw and kw not in seen and len(kw) <= MAX_KEYWORD_LENGTH:
            seen.add(kw)
            cleaned.append(kw)
        if len(cleaned) >= MAX_CUSTOM_KEYWORDS:
            break

    row = db.query(Setting).filter(Setting.key == CUSTOM_GUARDRAILS_SETTING_KEY).first()
    if row is None:
        row = Setting(key=CUSTOM_GUARDRAILS_SETTING_KEY, value=json.dumps(cleaned))
        db.add(row)
    else:
        row.value = json.dumps(cleaned)
    db.commit()

    return GuardrailsResponse(keywords=cleaned)
