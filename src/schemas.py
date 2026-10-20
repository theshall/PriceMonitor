from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=150)
    ean: str | None = Field(default=None, max_length=20)
    sku: str | None = Field(default=None, max_length=100)
