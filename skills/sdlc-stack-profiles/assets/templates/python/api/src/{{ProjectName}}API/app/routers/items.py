from fastapi import APIRouter, Depends, Request, status

from app.services.interfaces import IItemService
from app.services.models import Item, ItemCreate

router = APIRouter(prefix="/items", tags=["items"])


def get_item_service(request: Request) -> IItemService:
    return request.app.get_app_context().get(IItemService)


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate, service: IItemService = Depends(get_item_service)
):
    return await service.create_item_async(payload)


@router.get("", response_model=list[Item])
async def list_items(service: IItemService = Depends(get_item_service)):
    return await service.list_items_async()


@router.get("/{item_id}", response_model=Item)
async def get_item(
    item_id: int, service: IItemService = Depends(get_item_service)
):
    # A missing item raises NotFoundError in the service; the
    # composition root's handler maps it to 404.
    return await service.get_item_async(item_id)
