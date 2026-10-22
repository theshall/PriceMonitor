from fastapi.testclient import TestClient
from src.main import app
from sqlalchemy import text
from src.database import engine



client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_products():
    response = client.get("/api/products")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_product_without_name():
    response = client.post(
        "/api/products",
        json={"brand": "Marca de teste"}
    )

    assert response.status_code == 422


def test_create_product_with_valid_name():
    product_id = None

    try:
        response = client.post(
            "/api/products",
            json={
                "name": "Produto criado pelo teste automatizado",
                "brand": "Marca de teste",
                "model": "Modelo T100",
            },
        )

        assert response.status_code == 201

        data = response.json()
        product_id = data["id"]

        assert product_id is not None
        assert data["message"] == "Produto cadastrado com sucesso"
        assert data["name"] == "Produto criado pelo teste automatizado"
        assert data["brand"] == "Marca de teste"
        assert data["model"] == "Modelo T100"

    finally:
        if product_id is not None:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": product_id},
                )
