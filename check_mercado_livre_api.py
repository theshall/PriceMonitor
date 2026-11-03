"""Consulta os detalhes e o preço de um anúncio pela API."""

import json
import time
from decimal import Decimal

import httpx
from dotenv import dotenv_values

from src.mercado_livre_config import PROJECT_ROOT


ITEM_ID = "MLB7756640194"


def main():
    # Lê os tokens diretamente do arquivo atualizado.
    settings = dotenv_values(PROJECT_ROOT / ".env")
    saved_tokens = settings.get("ML_TOKEN_JSON")

    if not saved_tokens:
        print("Tokens ausentes. Execute a autorização primeiro.")
        return

    tokens = json.loads(saved_tokens)

    # Verifica a expiração antes de fazer a consulta.
    if time.time() >= tokens["expires_at"]:
        print("Token expirado. Precisamos renovar a autorização.")
        return

    # Envia o token no cabeçalho, sem exibi-lo no terminal.
    with httpx.Client(
        base_url="https://api.mercadolibre.com",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        timeout=20,
    ) as client:
        # Consulta a identificação e os atributos do anúncio.
        item_response = client.get(f"/items/{ITEM_ID}")
        print("Consulta do anúncio — HTTP:", item_response.status_code)

        if item_response.status_code != 200:
            print("A API não disponibilizou os detalhes do anúncio.")
            return

        item = item_response.json()

        print("Anúncio:", item.get("id"))
        print("Título:", item.get("title"))
        print("Status:", item.get("status"))
        print("ID do vendedor:", item.get("seller_id"))
        print("Produto de catálogo:", item.get("catalog_product_id"))

        # Exibe a voltagem caso esteja nos atributos principais.
        for attribute in item.get("attributes", []):
            if attribute.get("id") == "VOLTAGE":
                print("Voltagem:", attribute.get("value_name"))

        # Consulta o preço no contexto do marketplace.
        price_response = client.get(
            f"/items/{ITEM_ID}/sale_price",
            params={"context": "channel_marketplace"},
        )
        print("Consulta do preço — HTTP:", price_response.status_code)

        if price_response.status_code != 200:
            print("A API não disponibilizou o preço para esta aplicação.")
            return

        # Usa Decimal para preservar a representação monetária.
        price_data = json.loads(
            price_response.text,
            parse_float=Decimal,
        )

        print("Preço retornado:", price_data.get("amount"))
        print("Moeda:", price_data.get("currency_id"))
        print("Preço regular:", price_data.get("regular_amount"))


if __name__ == "__main__":
    try:
        main()
    except httpx.RequestError:
        print("Falha de conexão com a API. Tente novamente.")
    except (ValueError, KeyError, TypeError):
        print("As configurações ou a resposta da API têm formato inesperado.")