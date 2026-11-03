"""Verifica quando o monitor deve impedir a gravação de preços."""

from unittest.mock import Mock

import pytest

from src.monitoring import monitor_offer


def test_unavailable_offer_is_not_registered():
    # Simula um produto indisponível.
    collector = Mock(
        return_value={
            "available": False,
            "price": None,
            "currency": "BRL",
        }
    )
    register_price = Mock()

    result = monitor_offer(
        offer_id=1,
        collector=collector,
        register_price=register_price,
    )

    # Confirma que a coleta ocorreu, mas nenhuma gravação foi solicitada.
    collector.assert_called_once_with()
    assert result is None
    register_price.assert_not_called()


def test_collection_failure_is_not_registered():
    # Simula uma falha de conexão durante a coleta.
    collector = Mock(side_effect=TimeoutError("Tempo de espera excedido."))
    register_price = Mock()

    with pytest.raises(TimeoutError):
        monitor_offer(
            offer_id=1,
            collector=collector,
            register_price=register_price,
        )

    # A falha deve interromper o fluxo antes da gravação.
    register_price.assert_not_called()


@pytest.mark.parametrize(
    "price, currency",
    [
        ("-10.00", "BRL"),
        ("100.00", "USD"),
    ],
)
def test_invalid_price_or_currency_is_not_registered(price, currency):
    # Simula um preço negativo ou uma moeda não aceita.
    collector = Mock(
        return_value={
            "available": True,
            "price": price,
            "currency": currency,
        }
    )
    register_price = Mock()

    with pytest.raises(ValueError):
        monitor_offer(
            offer_id=1,
            collector=collector,
            register_price=register_price,
        )

    # Confirma que os dados rejeitados não chegaram à gravação.
    register_price.assert_not_called()