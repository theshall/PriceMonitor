from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError


from src.products import create_product, list_products
from src.offers import create_offer, list_offers
from src.schemas import ProductCreate, OfferCreate


app = FastAPI(title="Price Monitor")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "application": "price-monitor",
    }

@app.get("/api/info")
def application_info():
    return {
        "name": "Price Monitor",
        "version": "0.1.0",
        "description": "Monitoramento de preços",
        "features": [
            "Cadastro de produtos",
            "Histórico de preços",
            "Alertas de ofertas",
        ],
    }

@app.get("/api/products")
def get_products():
    return list_products()


@app.post("/api/products", status_code=201)
def post_product(product: ProductCreate):
    product_data = product.model_dump()

    product_id = create_product(product_data)

    return {
        "message": "Produto cadastrado com sucesso",
        "id": product_id,
        **product_data,
    }

@app.get("/api/offers")
def get_offers():
    return list_offers()


@app.post("/api/offers", status_code=201)
def post_offer(offer: OfferCreate):
    offer_data = offer.model_dump(mode="json")

    try:
        offer_id = create_offer(offer_data)

    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Produto inexistente ou dados incompatíveis com o banco."
        )

    return {
        "message": "Oferta cadastrada com sucesso",
        "id": offer_id,
        **offer_data
    }
