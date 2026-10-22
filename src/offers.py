from sqlalchemy import text
from src.database import engine


def list_offers():
    query = text("""
        SELECT
            id,
            product_id,
            store_name,
            price,
            product_url,
            created_at
        FROM offers
        ORDER BY id
    """)

    with engine.connect() as connection:
        result = connection.execute(query)

        return [
            dict(row)
            for row in result.mappings()
        ]


def create_offer(offer_data):
    query = text("""
        INSERT INTO offers (
            product_id,
            store_name,
            price,
            product_url
        )
        VALUES (
            :product_id,
            :store_name,
            :price,
            :product_url
        )
    """)

    with engine.begin() as connection:
        result = connection.execute(query, offer_data)

        return result.lastrowid
