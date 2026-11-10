from fastapi import APIRouter, Depends, Header, Request

from app.services.interfaces import IStatementService
from app.services.models import Statement

router = APIRouter(prefix="/statements", tags=["statements"])


def get_statement_service(request: Request) -> IStatementService:
    return request.app.get_app_context().get(IStatementService)


@router.get("/{customer_id}", response_model=Statement)
async def get_statement(
    customer_id: int,
    service: IStatementService = Depends(get_statement_service),
    actor: str = Header(default="anonymous", alias="X-Actor"),
):
    statement = await service.get_statement_async(customer_id)
    # Audit: record who viewed this customer's financial data.
    await service.record_view_async(customer_id, actor)
    return statement
