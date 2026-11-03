"""Calcula a redução entre dois preços."""

from decimal import Decimal, ROUND_HALF_UP

from src.schemas import PriceHistoryCreate


def calculate_price_drop(previous_price, current_price):
    # Reutiliza a validação de valores monetários da aplicação.
    previous = PriceHistoryCreate(price=previous_price).price
    current = PriceHistoryCreate(price=current_price).price

    # Preço igual ou maior representa ausência de queda.
    if current >= previous:
        return {
            "has_drop": False,
            "difference": Decimal("0.00"),
            "percentage": Decimal("0.00"),
        }

    # Calcula a economia em reais e em relação ao preço anterior.
    difference = previous - current
    percentage = difference / previous * Decimal("100")

    return {
        "has_drop": True,
        "difference": difference.quantize(Decimal("0.01")),
        "percentage": percentage.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        ),
    }