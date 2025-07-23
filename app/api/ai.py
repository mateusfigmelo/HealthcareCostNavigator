"""AI API router for natural language queries."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.ai_service import AIService

router = APIRouter(prefix="/ask", tags=["ai"])


class QuestionRequest(BaseModel):
    """Request model for natural language questions."""

    question: str


class QuestionResponse(BaseModel):
    """Response model for AI assistant answers."""

    answer: str
    results: list
    out_of_scope: bool
    sql_query: str | None = None
    error: str | None = None


@router.post("/", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest, session: AsyncSession = Depends(get_session)
) -> QuestionResponse:
    """
    Ask a natural language question about hospital pricing and quality.

    Examples:
    - "Who is cheapest for DRG 470 within 25 miles of 10001?"
    - "What's the cheapest hospital for knee replacement near NYC?"
    - "Show me top 3 hospitals by rating for DRG 470 within 50 km of 11211"
    - "What's the average cost of knee replacement in NY?"
    - "What hospital has the lowest total payments for DRG 193 near 10032?"
    """

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    ai_service = AIService(session)

    try:
        result = await ai_service.process_question(request.question)

        return QuestionResponse(
            answer=result["answer"],
            results=result["results"],
            out_of_scope=result["out_of_scope"],
            sql_query=result.get("sql_query"),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process question: {str(e)}"
        ) from e
