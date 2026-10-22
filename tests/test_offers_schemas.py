from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.schemas import OfferCreate



def test_offer_with_valid_data():
    offer = OfferCreate(
        product_id=1,
        store_name="Loja de Teste",
        price="129.90",
        product_url="https://example.com/produto"
    )

    assert offer.product_id == 1
    assert offer.store_name == "Loja de Teste"
    assert offer.price == Decimal("129.90")


def test_offer_rejects_negative_price():
    with pytest.raises(ValidationError):
        OfferCreate(
            product_id=1,
            store_name="Loja de Teste",
            price="-50.00"
        )


def test_offer_requires_store_name():
    with pytest.raises(ValidationError):
        OfferCreate(
            product_id=1,
            price="129.90"
        )


def test_offer_rejects_invalid_url():
    with pytest.raises(ValidationError):
        OfferCreate(
            product_id=1,
            store_name="Loja de Teste",
            price="129.90",
            product_url="endereco-invalido"
        )
