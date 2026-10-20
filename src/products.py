from sqlalchemy import text
from src.database import engine

def create_product(product_data):
    query = text("""
        INSERT INTO products (name, brand, model, ean, sku)
        VALUES (:name, :brand, :model, :ean, :sku)
    """)

    with engine.begin() as connection:
        result = connection.execute(query, product_data)
        return result.lastrowid


def list_products():
    query = text("""
        SELECT
            id,
            name,
            brand,
            model,
            ean,
            sku,
            created_at
        FROM products
        ORDER BY id
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
        products = result.mappings().all()

    return [dict(product) for product in products]
