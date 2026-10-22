from pydantic import BaseModel, Field
from decimal import Decimal
from pydantic import HttpUrl

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=150)
    ean: str | None = Field(default=None, max_length=20)
    sku: str | None = Field(default=None, max_length=100)


class OfferCreate(BaseModel):
    product_id: int = Field(gt=0)

    store_name: str = Field(
        min_length=1,
        max_length=150
    )

    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2
    )

    product_url: HttpUrl | None = None
