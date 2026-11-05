"""Testa a fila exclusivamente no banco de testes."""

from sqlalchemy import text

from src.alert_queue import enqueue_telegram_alert
from src.database import test_engine
from unittest.mock import Mock
import pytest
from src.alert_queue import dispatch_next_telegram_alert

def test_history_and_alert_rollback_together():
    # Confirma o banco configurado antes de iniciar o teste.
    assert test_engine.url.database == "price_monitor_test"

    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            # Confirma também o banco selecionado pelo MySQL.
            assert connection.execute(
                text("SELECT DATABASE()")
            ).scalar_one() == "price_monitor_test"

            # Cria os registros necessários para as chaves estrangeiras.
            product_id = connection.execute(
                text("INSERT INTO products (name) VALUES (:name)"),
                {"name": "TESTE - Fila de alertas"},
            ).lastrowid

            offer_id = connection.execute(
                text("""
                    INSERT INTO offers (product_id, store_name, price)
                    VALUES (:product_id, :store_name, :price)
                """),
                {
                    "product_id": product_id,
                    "store_name": "TESTE - Loja da fila",
                    "price": "100.00",
                },
            ).lastrowid

            # Simula a transação que gravará preço e alerta juntos.
            savepoint = connection.begin_nested()

            history_id = connection.execute(
                text("""
                    INSERT INTO price_history (offer_id, price)
                    VALUES (:offer_id, :price)
                """),
                {"offer_id": offer_id, "price": "90.00"},
            ).lastrowid

            alert_id = enqueue_telegram_alert(
                connection,
                history_id,
                "TESTE - Queda de preço para R$ 90,00.",
            )

            # O alerta recém-criado deve estar pendente.
            pending = connection.execute(
                text("""
                    SELECT history_id, message, sent_at
                    FROM telegram_alerts
                    WHERE id = :id
                """),
                {"id": alert_id},
            ).mappings().one()

            assert pending["history_id"] == history_id
            assert pending["message"] == "TESTE - Queda de preço para R$ 90,00."
            assert pending["sent_at"] is None
            # A primeira tentativa simula uma falha de conexão.
            failed_sender = Mock(side_effect=RuntimeError("Falha simulada."))

            with pytest.raises(RuntimeError, match="Falha simulada"):
                dispatch_next_telegram_alert(connection, failed_sender)

            # O alerta deve continuar pendente para uma nova tentativa.
            assert connection.execute(
                text("SELECT sent_at FROM telegram_alerts WHERE id = :id"),
                {"id": alert_id},
            ).scalar_one() is None

            # A segunda tentativa simula uma confirmação do Telegram.
            successful_sender = Mock()
            sent_id = dispatch_next_telegram_alert(
                connection,
                successful_sender,
            )

            assert sent_id == alert_id
            successful_sender.assert_called_once_with(
                "TESTE - Queda de preço para R$ 90,00."
            )
            assert connection.execute(
                text("SELECT sent_at FROM telegram_alerts WHERE id = :id"),
                {"id": alert_id},
            ).scalar_one() is not None

            # Um alerta confirmado deve sair da seleção de pendentes.
            unused_sender = Mock()
            assert dispatch_next_telegram_alert(connection, unused_sender) is None
            unused_sender.assert_not_called()
            
            # Desfaz o trecho que criou o preço e o alerta.
            savepoint.rollback()

            assert connection.execute(
                text("SELECT COUNT(*) FROM price_history WHERE id = :id"),
                {"id": history_id},
            ).scalar_one() == 0

            assert connection.execute(
                text("SELECT COUNT(*) FROM telegram_alerts WHERE id = :id"),
                {"id": alert_id},
            ).scalar_one() == 0

        finally:
            # Desfaz também o produto e a oferta temporários.
            transaction.rollback()
