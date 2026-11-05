"""Adiciona alertas à fila dentro da transação do histórico."""

from sqlalchemy import text


def enqueue_telegram_alert(connection, history_id, message):
    # Usa a conexão recebida para participar da mesma transação do preço.
    result = connection.execute(
        text("""
            INSERT INTO telegram_alerts (history_id, message)
            VALUES (:history_id, :message)
        """),
        {"history_id": history_id, "message": message},
    )

    return result.lastrowid
def dispatch_next_telegram_alert(connection, sender):
    # Reserva um alerta nesta transação para evitar envios simultâneos.
    alert = connection.execute(
        text("""
            SELECT id, message
            FROM telegram_alerts
            WHERE sent_at IS NULL
            ORDER BY id
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)
    ).mappings().one_or_none()

    if alert is None:
        return None

    # Se o envio falhar, a exceção interrompe a função antes da confirmação.
    sender(alert["message"])

    # Marca como enviado somente depois que sender retornar com sucesso.
    connection.execute(
        text("""
            UPDATE telegram_alerts
            SET sent_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {"id": alert["id"]},
    )

    return alert["id"]