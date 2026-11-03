"""Simula consultas de preços para desenvolver e testar o monitor."""

from decimal import Decimal


def collect_simulated_price(scenario="normal"):
    # Simula uma falha de comunicação com o fornecedor.
    if scenario == "connection_error":
        raise TimeoutError("Falha de conexão simulada.")

    # Usa valores fixos para que os testes sejam reproduzíveis.
    prices = {
        "normal": Decimal("2599.90"),
        "price_drop": Decimal("2399.90"),
        "unavailable": None,
    }

    # Evita aceitar nomes de cenários digitados incorretamente.
    if scenario not in prices:
        raise ValueError(f"Cenário desconhecido: {scenario}")

    price = prices[scenario]

    # Identifica explicitamente a origem fictícia do resultado.
    return {
        "source": "simulated",
        "external_id": "SIMULATED-001",
        "product_name": "Ar-condicionado de teste 9000 BTUs 220 V",
        "store_name": "Loja Simulada",
        "currency": "BRL",
        "available": price is not None,
        "price": price,
    }