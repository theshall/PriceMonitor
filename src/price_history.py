from sqlalchemy import text
from src.database import engine


def register_price(offer_id, price):
    query = text("""
        INSERT INTO price_history (offer_id, price)
        VALUES (:offer_id, :price)
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "offer_id": offer_id,
                "price": price
            }
        )

        return result.lastrowid


def list_price_history(offer_id):
    query = text("""
        SELECT
            id,
            offer_id,
            price,
            checked_at
        FROM price_history
        WHERE offer_id = :offer_id
        ORDER BY checked_at ASC, id ASC
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"offer_id": offer_id}
        )

        return [
            dict(row)
            for row in result.mappings()
        ]
