"""
Testes automatizados do histórico de preços.

Todos os registros são criados no banco price_monitor_test
e removidos ao final do teste.
"""

from decimal import Decimal

from sqlalchemy import text

import src.price_history as history
from src.database import test_engine


def test_register_and_list_price_history(monkeypatch):
    """
    Verifica se um preço pode ser registrado e consultado.

    Cria um produto e uma oferta temporários para satisfazer
    os relacionamentos de chave estrangeira do MySQL.
    """

    # Redireciona o módulo de histórico para o banco de testes.
    monkeypatch.setattr(history, "engine", test_engine)

    # Inicializa os identificadores usados na limpeza.
    product_id = None
    offer_id = None
    history_id = None

    try:
        # Cria um produto temporário no banco de testes.
        with test_engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO products (name, brand)
                    VALUES (:name, :brand)
                """),
                {
                    "name": "Produto Histórico Teste",
                    "brand": "Marca Teste"
                }
            )

            product_id = result.lastrowid

        # Cria uma oferta vinculada ao produto temporário.
        with test_engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO offers (
                        product_id,
                        store_name,
                        price
                    )
                    VALUES (
                        :product_id,
                        :store_name,
                        :price
                    )
                """),
                {
                    "product_id": product_id,
                    "store_name": "Loja Histórico Teste",
                    "price": Decimal("149.90")
                }
            )

            offer_id = result.lastrowid

        # Registra um novo preço no histórico da oferta.
        history_id = history.register_price(
            offer_id,
            Decimal("119.90")
        )

        # Confirma que o registro recebeu um identificador.
        assert history_id is not None

        # Consulta os registros associados à oferta.
        records = history.list_price_history(offer_id)

        # Verifica se o preço registrado aparece na consulta.
        assert any(
            record["id"] == history_id
            and record["offer_id"] == offer_id
            and record["price"] == Decimal("119.90")
            for record in records
        )

    finally:
        # Remove primeiro o histórico, depois a oferta
        # e, por último, o produto.
        # Essa ordem respeita as chaves estrangeiras.
        with test_engine.begin() as connection:
            if history_id is not None:
                connection.execute(
                    text("""
                        DELETE FROM price_history
                        WHERE id = :id
                    """),
                    {"id": history_id}
                )

            if offer_id is not None:
                connection.execute(
                    text("""
                        DELETE FROM offers
                        WHERE id = :id
                    """),
                    {"id": offer_id}
                )

            if product_id is not None:
                connection.execute(
                    text("""
                        DELETE FROM products
                        WHERE id = :id
                    """),
                    {"id": product_id}
                )
