import src.offers as offers
from src.database import test_engine

# Direciona esta verificação ao banco de testes.
offers.engine = test_engine

# Substitua pelo ID encontrado no MySQL.
product_id = 3

offer_data = {
    "product_id": product_id,
    "store_name": "Loja de Teste",
    "price": "129.90",
    "product_url": "https://example.com/produto-teste"
}

offer_id = offers.create_offer(offer_data)

print(f"Oferta cadastrada com ID: {offer_id}")

assert offer_id is not None

print("Cadastro da oferta validado!")
