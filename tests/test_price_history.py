"""Testa o histórico com preços simulados no banco exclusivo de testes."""

from decimal import Decimal

from sqlalchemy import text

from functools import partial
from src.monitoring import monitor_offer
import src.price_history as history
from src.database import test_engine
from src.simulated_collector import collect_simulated_price


def test_register_and_list_price_history(monkeypatch):
    # Interrompe o teste se a conexão apontar para outro banco.
    assert test_engine.url.database == "price_monitor_test", (
        "Este teste deve usar exclusivamente price_monitor_test."
    )

    # Direciona as funções de histórico para o banco de testes.
    monkeypatch.setattr(history, "engine", test_engine)

    product_id = None
    offer_id = None

    try:
        # Cria os dados temporários em uma única transação.
        with test_engine.begin() as connection:
            product_result = connection.execute(
                text("""
                    INSERT INTO products (name, brand)
                    VALUES (:name, :brand)
                """),
                {
                    "name": "SIMULADO - Ar-condicionado 9000 BTUs 220 V",
                    "brand": "Marca de Teste",
                },
            )
            product_id = product_result.lastrowid

            offer_result = connection.execute(
                text("""
                    INSERT INTO offers (
                        product_id, store_name, price
                    )
                    VALUES (
                        :product_id, :store_name, :price
                    )
                """),
                {
                    "product_id": product_id,
                    "store_name": "SIMULADO - Loja de Teste",
                    "price": Decimal("2599.90"),
                },
            )
            offer_id = offer_result.lastrowid

        # Simula três consultas consecutivas da mesma oferta.
        scenarios = ["normal", "price_drop", "unavailable"]
        saved_ids = []

        for scenario in scenarios:
            # Prepara o coletor para executar o cenário desta rodada.
            collector = partial(collect_simulated_price, scenario)

            # Executa a rotina que será usada pelo monitor.
            history_id = monitor_offer(
                offer_id=offer_id,
                collector=collector,
                register_price=history.register_price,
            )

            # Ofertas indisponíveis retornam None.
            if history_id is not None:
                saved_ids.append(history_id)
                
        # Consulta o histórico pela função usada na aplicação.
        records = history.list_price_history(offer_id)

        # A indisponibilidade deve deixar apenas os dois preços válidos.
        assert len(records) == 2
        assert [record["id"] for record in records] == saved_ids
        assert [record["price"] for record in records] == [
            Decimal("2599.90"),
            Decimal("2399.90"),
        ]

        # Confere a oferta e a data preenchida pelo MySQL.
        assert all(record["offer_id"] == offer_id for record in records)
        assert all(record["checked_at"] is not None for record in records)

    finally:
        # Remove os registros temporários mesmo se uma verificação falhar.
        with test_engine.begin() as connection:
            if offer_id is not None:
                # Remove o histórico antes da oferta.
                connection.execute(
                    text("DELETE FROM price_history WHERE offer_id = :id"),
                    {"id": offer_id},
                )
                connection.execute(
                    text("DELETE FROM offers WHERE id = :id"),
                    {"id": offer_id},
                )

            if product_id is not None:
                # Remove o produto depois da oferta.
                connection.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": product_id},
                )