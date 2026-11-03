"""Registra alertas de queda de preço em um arquivo local."""

from datetime import datetime


def write_price_drop_alert(comparison, minimum_percent, alert_path):
    # Só grava quando existe uma queda que alcança o limite.
    if not comparison["has_drop"] or comparison["percentage"] < minimum_percent:
        return None

    difference = format(comparison["difference"], ".2f").replace(".", ",")
    percentage = format(comparison["percentage"], ".2f").replace(".", ",")
    message = f"QUEDA SIMULADA: economia de R$ {difference} ({percentage}%)."

    # Acrescenta o alerta preservando as linhas anteriores.
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with alert_path.open("a", encoding="utf-8") as alert_file:
        alert_file.write(f"{timestamp} | {message}\n")

    return message