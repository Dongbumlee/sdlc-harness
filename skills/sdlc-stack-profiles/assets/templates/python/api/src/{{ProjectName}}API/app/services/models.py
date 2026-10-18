from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
