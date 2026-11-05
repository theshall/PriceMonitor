"""Registra uma coleta validada no histórico da oferta permanente."""

from pathlib import Path

import httpx
from dotenv import dotenv_values
from sqlalchemy import text
from decimal import Decimal

from src.price_comparison import calculate_price_drop
from src.telegram_alerts import send_telegram_alert
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
        
        # Consulta a última observação antes de gravar a nova.
        previous_price = connection.execute(
            text("""
                SELECT price
                FROM price_history
                WHERE offer_id = :offer_id
                ORDER BY checked_at DESC, id DESC
                LIMIT 1
            """),
            {"offer_id": OFFER_ID},
        ).scalar_one_or_none()

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
    # A primeira observação estabelece a referência de comparação.
    if previous_price is None:
        print("Primeiro preço registrado para comparação.")
        return

    comparison = calculate_price_drop(previous_price, price)

    if not comparison["has_drop"]:
        print("Sem queda em relação à observação anterior.")
        return

    if comparison["percentage"] < Decimal("5.00"):
        print("Queda abaixo do limite de alerta de 5%.")
        return

    # Envia o alerta depois que a transação do histórico foi confirmada.
    previous_display = format(previous_price, ".2f").replace(".", ",")
    current_display = format(price, ".2f").replace(".", ",")
    percentage = format(comparison["percentage"], ".2f").replace(".", ",")

    message = (
        f"Queda de preço — Mega Byte\n"
        f"LG Dual Inverter AI Voice 9000 BTUs — 220 V\n"
        f"Preço anterior: R$ {previous_display}\n"
        f"Preço atual: R$ {current_display}\n"
        f"Redução: {percentage}%\n"
        f"{PILOT_URL}"
    )

    try:
        send_telegram_alert(message)
    except RuntimeError as error:
        print(f"Histórico salvo, mas o alerta falhou: {error}")
    else:
        print("Alerta de queda enviado ao Telegram.")

if __name__ == "__main__":
    main()