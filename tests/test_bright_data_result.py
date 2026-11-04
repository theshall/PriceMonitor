"""Verifica quais resultados da Bright Data podem entrar no histórico."""

from decimal import Decimal

import pytest

from check_bright_data_result import validate_pilot_price


@pytest.fixture
def pilot_record():
    # Reproduz os campos usados na validação, sem chamar a API.
    return {
        "catalog_product_id": "MLB66277100",
        "seller_id": "167787623",
        "product_features": [
            {
                "type": "Voltagem da unidade externa",
                "value": "220V",
            },
        ],
        "in_stock": True,
        "currency": "BRL",
        "final_price": Decimal("2599.90"),
    }


def test_accepts_pilot_price(pilot_record):
    # Confirma o preço da oferta esperada.
    assert validate_pilot_price([pilot_record]) == Decimal("2599.90")


@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("seller_id", "999999999", "vendedor"),
        ("product_features", [], "voltagem"),
        ("in_stock", False, "estoque"),
    ],
)
def test_rejects_mismatched_or_unavailable_offer(
    pilot_record, field, value, expected_error
):
    # Altera um campo por vez para verificar a causa da rejeição.
    pilot_record[field] = value

    with pytest.raises(ValueError, match=expected_error):
        validate_pilot_price([pilot_record])