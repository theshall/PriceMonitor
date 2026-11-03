import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import src.offers as offers
import src.products as products
from src.main import app
from src.database import test_engine
from decimal import Decimal

import src.price_history as history
client = TestClient(app)


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    monkeypatch.setattr(
        products,
        "engine",
        test_engine
    )
    monkeypatch.setattr(
        offers,
        "engine",
        test_engine
    )
    # Redireciona as consultas e gravações de histórico durante os testes.
    monkeypatch.setattr(history, "engine", test_engine)

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
            with test_engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": product_id},
                )

def test_list_offers():
    response = client.get("/api/offers")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_create_offer_with_negative_price():
    response = client.post(
        "/api/offers",
        json={
            "product_id": 1,
            "store_name": "Loja de Teste",
            "price": "-50.00",
            "product_url": "https://example.com/produto"
        }
    )

    assert response.status_code == 422


def test_create_product_and_offer():
    product_id = None
    offer_id = None

    try:
        # Cadastrar produto temporário
        product_response = client.post(
            "/api/products",
            json={
                "name": "Produto Integração Teste",
                "brand": "Marca Teste",
                "model": "INT-001"
            }
        )

        assert product_response.status_code == 201

        product_id = product_response.json()["id"]

        # Cria uma oferta vinculada ao produto temporário.
        offer_response = client.post(
            "/api/offers",
            json={
                "product_id": product_id,
                "store_name": "Loja Integração",
                "price": "99.90",
                "product_url": "https://example.com/teste",
            },
        )

        assert offer_response.status_code == 201

        # Guarda o ID da oferta antes de registrar seu histórico.
        offer_id = offer_response.json()["id"]

        # Registra um preço para a oferta criada.
        history_url = f"/api/offers/{offer_id}/price-history"
        price_response = client.post(
            history_url,
            json={"price": "89.90"},
        )
        assert price_response.status_code == 201

        # Consulta e confere o registro salvo no banco de testes.
        history_response = client.get(history_url)
        assert history_response.status_code == 200

        records = history_response.json()
        assert len(records) == 1
        assert records[0]["id"] == price_response.json()["id"]
        assert records[0]["offer_id"] == offer_id
        assert Decimal(str(records[0]["price"])) == Decimal("89.90")
        assert records[0]["checked_at"] is not None

        # Verifica se a oferta aparece na listagem.
        list_response = client.get("/api/offers")
        assert list_response.status_code == 200

        offers_data = list_response.json()

        assert any(
            offer["id"] == offer_id
            and offer["product_id"] == product_id
            for offer in offers_data
        )

    finally:
        # Remove os dados temporários respeitando as chaves estrangeiras.
        with test_engine.begin() as connection:
            if offer_id is not None:
                # Exclui primeiro o histórico vinculado à oferta.
                connection.execute(
                    text("DELETE FROM price_history WHERE offer_id = :id"),
                    {"id": offer_id},
                )

                # Exclui a oferta depois de remover seu histórico.
                connection.execute(
                    text("DELETE FROM offers WHERE id = :id"),
                    {"id": offer_id},
                )

            if product_id is not None:
                # Exclui o produto depois de remover a oferta.
                connection.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": product_id},
                )