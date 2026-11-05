"""Registra o preço e enfileira alertas da oferta permanente."""

from decimal import Decimal, InvalidOperation
from pathlib import Path
import httpx
from dotenv import dotenv_values
from sqlalchemy import text
from check_bright_data_api import PILOT_URL, collect_pilot_price
from src.alert_queue import enqueue_telegram_alert
from src.database import engine
from src.price_comparison import calculate_price_drop


OFFER_ID = 1


def main():
    # Confere a configuração antes de fazer a coleta.
    if engine.url.database != "price_monitor":
        raise SystemExit("A configuração deve apontar para price_monitor.")

    settings = dotenv_values(Path(__file__).with_name(".env"))
    # Valida o limite antes de iniciar uma consulta à Bright Data.
    try:
        minimum_percent = Decimal(
            settings.get("PRICE_ALERT_MIN_PERCENT") or "5.00"
        )
    except InvalidOperation:
        raise SystemExit(
            "PRICE_ALERT_MIN_PERCENT deve ser um número, como 5.00."
        ) from None

    if not minimum_percent.is_finite() or not (
        Decimal("0") <= minimum_percent <= Decimal("100")
    ):
        raise SystemExit("PRICE_ALERT_MIN_PERCENT deve estar entre 0 e 100.")

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

    alert_id = None

    # Preço e mensagem são confirmados ou desfeitos juntos.
    with engine.begin() as connection:
        database_name = connection.execute(
            text("SELECT DATABASE()")
        ).scalar_one()
        if database_name != "price_monitor":
            raise SystemExit("O MySQL selecionou um banco inesperado.")

        # Serializa as gravações desta oferta.
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

        history_id = connection.execute(
            text("""
                INSERT INTO price_history (offer_id, price)
                VALUES (:offer_id, :price)
            """),
            {"offer_id": OFFER_ID, "price": price},
        ).lastrowid

        # Atualiza o preço exibido no cadastro da oferta.
        # A alteração é confirmada junto com o histórico e o eventual alerta.
        connection.execute(
            text("""
                UPDATE offers
                SET price = :price
                WHERE id = :offer_id
            """),
            {"price": price, "offer_id": OFFER_ID},
        )

        if previous_price is not None:
            comparison = calculate_price_drop(previous_price, price)

            if (
                comparison["has_drop"]
                and comparison["percentage"] >= minimum_percent
            ):
                previous_display = format(previous_price, ".2f").replace(".", ",")
                current_display = format(price, ".2f").replace(".", ",")
                percentage = format(
                    comparison["percentage"], ".2f"
                ).replace(".", ",")

                message = (
                    "Queda de preço — Mega Byte\n"
                    "LG Dual Inverter AI Voice 9000 BTUs — 220 V\n"
                    f"Preço anterior: R$ {previous_display}\n"
                    f"Preço atual: R$ {current_display}\n"
                    f"Redução: {percentage}%\n"
                    f"{PILOT_URL}"
                )

                # Participa da mesma transação do histórico.
                alert_id = enqueue_telegram_alert(
                    connection,
                    history_id,
                    message,
                )

    # Só informa sucesso após a confirmação da transação.
    print(
        f"Histórico permanente registrado. Oferta: {OFFER_ID}. "
        f"Registro: {history_id}. Preço: BRL {price:.2f}."
    )

    if alert_id is None:
        print("Nenhum novo alerta gerado nesta coleta.")
    else:
        print(f"Alerta {alert_id} salvo na fila para envio.")


if __name__ == "__main__":
    main()
