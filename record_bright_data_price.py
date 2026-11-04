"""Registra uma coleta validada no histórico da oferta permanente."""

from pathlib import Path

import httpx
from dotenv import dotenv_values
from sqlalchemy import text

from check_bright_data_api import PILOT_URL, collect_pilot_price
from src.database import engine


OFFER_ID = 1


def main():
    # Confere a configuração do banco principal antes da coleta.
    if engine.url.database != "price_monitor":
        raise SystemExit("A configuração deve apontar para price_monitor.")

    settings = dotenv_values(Path(__file__).with_name(".env"))
    api_key = settings.get("BRIGHT_DATA_API_KEY")
    if not api_key or api_key == "COLE_A_CHAVE_AQUI":
        raise SystemExit("Preencha BRIGHT_DATA_API_KEY no .env.")

    try:
        price = collect_pilot_price(api_key)
    except httpx.RequestError:
        raise SystemExit(
            "Falha de comunicação. Confira Instantâneos antes de repetir."
        ) from None
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"Preço não validado. {error}") from None

    # Confere o banco e a oferta na mesma transação que grava o preço.
    with engine.begin() as connection:
        database_name = connection.execute(
            text("SELECT DATABASE()")
        ).scalar_one()
        if database_name != "price_monitor":
            raise SystemExit("O MySQL selecionou um banco diferente do esperado.")

        offer = connection.execute(
            text("""
                SELECT store_name, product_url
                FROM offers
                WHERE id = :offer_id
                FOR UPDATE
            """),
            {"offer_id": OFFER_ID},
        ).mappings().one_or_none()

        if (
            offer is None
            or offer["store_name"] != "Mega Byte"
            or offer["product_url"] != PILOT_URL
        ):
            raise SystemExit("A oferta cadastrada difere da oferta piloto.")

        # O MySQL preenche checked_at no momento da gravação.
        result = connection.execute(
            text("""
                INSERT INTO price_history (offer_id, price)
                VALUES (:offer_id, :price)
            """),
            {"offer_id": OFFER_ID, "price": price},
        )
        history_id = result.lastrowid

    print(
        f"Histórico permanente registrado. Oferta: {OFFER_ID}. "
        f"Registro: {history_id}. Preço: BRL {price:.2f}."
    )


if __name__ == "__main__":
    main()