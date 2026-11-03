"""Testa o cálculo de queda de preço."""

from decimal import Decimal

import pytest

from src.price_comparison import calculate_price_drop


def test_calculate_price_drop():
    # Confere a redução usada nos cenários simulados.
    result = calculate_price_drop("2599.90", "2399.90")

    assert result["has_drop"] is True
    assert result["difference"] == Decimal("200.00")
    assert result["percentage"] == Decimal("7.69")


@pytest.mark.parametrize("current_price", ["2599.90", "2799.90"])
def test_price_without_drop(current_price):
    # Preço igual ou maior não deve gerar indicação de queda.
    result = calculate_price_drop("2599.90", current_price)

    assert result["has_drop"] is False
    assert result["difference"] == Decimal("0.00")
    assert result["percentage"] == Decimal("0.00")


@pytest.mark.parametrize(
    "previous_price, current_price",
    [
        ("0.00", "100.00"),
        ("100.00", "-1.00"),
    ],
)
def test_invalid_prices(previous_price, current_price):
    # Impede cálculos com preços inválidos.
    with pytest.raises(ValueError):
        calculate_price_drop(previous_price, current_price)