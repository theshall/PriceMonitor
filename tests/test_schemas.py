import pytest
from pydantic import ValidationError

from src.schemas import ProductCreate


def test_product_with_valid_name():
    product = ProductCreate(name="Teclado de teste")

    assert product.name == "Teclado de teste"


def test_product_rejects_empty_name():
    with pytest.raises(ValidationError):
        ProductCreate(name="")


def test_product_requires_name():
    with pytest.raises(ValidationError):
        ProductCreate()
