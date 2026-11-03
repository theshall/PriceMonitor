"""Testa o coletor simulado sem acessar a internet ou o banco."""

from decimal import Decimal

import pytest

from src.simulated_collector import collect_simulated_price


@pytest.mark.parametrize(
    "scenario, expected_price, expected_available",
    [
        ("normal", Decimal("2599.90"), True),
        ("price_drop", Decimal("2399.90"), True),
        ("unavailable", None, False),
    ],
)
def test_collect_simulated_price(
    scenario,
    expected_price,
    expected_available,
):
    # Executa a coleta para cada cenário definido acima.
    result = collect_simulated_price(scenario)

    # Confere o preço, a disponibilidade e a identificação de teste.
    assert result["price"] == expected_price
    assert result["available"] is expected_available
    assert result["source"] == "simulated"
    assert result["external_id"] == "SIMULATED-001"
    assert result["currency"] == "BRL"


def test_simulated_connection_error():
    # Confirma que uma falha de conexão gera uma exceção.
    with pytest.raises(TimeoutError, match="Falha de conexão simulada"):
        collect_simulated_price("connection_error")


def test_unknown_scenario():
    # Confirma que um cenário inválido é rejeitado.
    with pytest.raises(ValueError, match="Cenário desconhecido"):
        collect_simulated_price("cenario_inexistente")