"""Testa o fluxo permanente com banco e Telegram simulados."""

from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import record_bright_data_price as recorder


@pytest.mark.parametrize(
    "current_price, expected_alert",
    [
        (Decimal("2700.00"), True),
        (Decimal("3000.00"), False),
    ],
)
def test_record_before_alert(monkeypatch, current_price, expected_alert):
    # Substitui a configuração e a coleta por valores controlados.
    monkeypatch.setattr(
        recorder,
        "dotenv_values",
        lambda _: {"BRIGHT_DATA_API_KEY": "chave-ficticia"},
    )
    monkeypatch.setattr(
        recorder,
        "collect_pilot_price",
        Mock(return_value=current_price),
    )

    # Simula os quatro resultados SQL usados pelo script.
    database_result = Mock()
    database_result.scalar_one.return_value = "price_monitor"

    offer_result = Mock()
    offer_result.mappings.return_value.one_or_none.return_value = {
        "store_name": "Mega Byte",
        "product_url": recorder.PILOT_URL,
    }

    previous_result = Mock()
    previous_result.scalar_one_or_none.return_value = Decimal("3000.00")

    insert_result = Mock()
    insert_result.lastrowid = 100

    connection = Mock()
    connection.execute.side_effect = [
        database_result,
        offer_result,
        previous_result,
        insert_result,
        Mock(),  # Para o UPDATE do preço.
    ]

    events = []

    @contextmanager
    def begin():
        # Marca a confirmação somente após sair do bloco de gravação.
        yield connection
        events.append("commit")

    fake_engine = SimpleNamespace(
        url=SimpleNamespace(database="price_monitor"),
        begin=begin,
    )
    monkeypatch.setattr(recorder, "engine", fake_engine)

    def enqueue_alert(received_connection, history_id, message):
        # A mensagem deve entrar na fila antes da confirmação do preço.
        assert events == []
        assert received_connection is connection
        assert history_id == 100
        assert "Preço anterior: R$ 3000,00" in message
        assert "Preço atual: R$ 2700,00" in message
        events.append("queue")
        return 200

    enqueue = Mock(side_effect=enqueue_alert)
    monkeypatch.setattr(recorder, "enqueue_telegram_alert", enqueue)

    recorder.main()

    assert connection.execute.call_count == 5

    # Confere se o cadastro recebe o mesmo preço usado no histórico.
    update_call = connection.execute.call_args_list[4]
    assert "UPDATE offers" in str(update_call.args[0])
    assert update_call.args[1] == {
        "price": current_price,
        "offer_id": recorder.OFFER_ID,
    }