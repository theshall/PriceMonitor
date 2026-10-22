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

