"""Tenta enviar um alerta pendente da fila do banco principal."""

import argparse
from datetime import datetime

from sqlalchemy import text

from src.alert_queue import dispatch_next_telegram_alert
from src.database import engine
from src.telegram_alerts import send_telegram_alert


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet", action="store_true",
        help="Omite a mensagem quando a fila estiver vazia.",
    )
    args = parser.parse_args()

    # Confere a configuração antes de acessar a fila.
    if engine.url.database != "price_monitor":
        raise SystemExit("A configuração deve apontar para price_monitor.")

    try:
        # A confirmação do envio participa desta transação.
        with engine.begin() as connection:
            database_name = connection.execute(
                text("SELECT DATABASE()")
            ).scalar_one()

            if database_name != "price_monitor":
                raise SystemExit("O MySQL selecionou um banco inesperado.")

            alert_id = dispatch_next_telegram_alert(
                connection,
                send_telegram_alert,
            )

    except RuntimeError as error:
        # A transação é desfeita e o alerta permanece pendente.
        raise SystemExit(f"Alerta mantido na fila. {error}") from None

    if alert_id is None:
        if not args.quiet:
            print("Nenhum alerta pendente disponível.")
    else:
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        print(f"{timestamp} | Alerta {alert_id} enviado e confirmado no banco.")


if __name__ == "__main__":
    main()
