"""Verifica a gravação de uma coleta real no banco de testes."""

import argparse
from pathlib import Path

from sqlalchemy import text

import src.price_history as history
from check_bright_data_result import read_pilot_price
from src.database import test_engine
from src.monitoring import monitor_offer
from contextlib import contextmanager

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()

    # Valida a oferta e o preço antes de criar dados temporários.
    price = read_pilot_price(args.json_path)
    verify_pilot_history([price])


@contextmanager
def temporary_pilot_offer(initial_price):

    # Confere o banco configurado e o banco selecionado pelo MySQL.
    if test_engine.url.database != "price_monitor_test":
        raise RuntimeError("A configuração deve apontar para price_monitor_test.")

    with test_engine.connect() as connection:
        database_name = connection.execute(text("SELECT DATABASE()")).scalar_one()

    if database_name != "price_monitor_test":
        raise RuntimeError("O MySQL selecionou um banco diferente do esperado.")

    # Direciona as funções de histórico para o banco de testes neste processo.
    history.engine = test_engine
    product_id = None
    offer_id = None

    try:
        # Cria um produto e uma oferta exclusivos deste teste.
        with test_engine.begin() as connection:
            product_id = connection.execute(
                text("INSERT INTO products (name, brand) VALUES (:name, :brand)"),
                {"name": "TESTE - Piloto Bright Data", "brand": "LG"},
            ).lastrowid

            offer_id = connection.execute(
                text("""
                    INSERT INTO offers (product_id, store_name, price)
                    VALUES (:product_id, :store_name, :price)
                """),
                {
                    "product_id": product_id,
                    "store_name": "TESTE - Mega Byte",
                    "price": initial_price,
                },
            ).lastrowid

        yield offer_id
    finally:
        # Remove os dados temporários na ordem das chaves estrangeiras.
        with test_engine.begin() as connection:
            if offer_id is not None:
                connection.execute(
                    text("DELETE FROM price_history WHERE offer_id = :id"),
                    {"id": offer_id},
                )
                connection.execute(
                    text("DELETE FROM offers WHERE id = :id"),
                    {"id": offer_id},
                )

            if product_id is not None:
                connection.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": product_id},
                )

        print("Dados temporários removidos do banco de testes.")


def verify_pilot_history(prices):
    # Reutiliza a oferta temporária no teste feito com o JSON salvo.
    with temporary_pilot_offer(prices[0]) as offer_id:
        saved_ids = [
            history.register_price(offer_id, price)
            for price in prices
        ]
        records = history.list_price_history(offer_id)

        if (
            [record["id"] for record in records] != saved_ids
            or [record["price"] for record in records] != prices
        ):
            raise RuntimeError("O histórico não corresponde aos preços coletados.")

        print(f"Histórico conferido em price_monitor_test. Registros: {len(records)}.")


if __name__ == "__main__":
    main()