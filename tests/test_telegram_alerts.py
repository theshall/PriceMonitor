"""Testa o envio de alertas sem chamar a API do Telegram."""

from unittest.mock import Mock

import httpx
import pytest

import src.telegram_alerts as telegram


@pytest.fixture
def telegram_config(monkeypatch):
    # Substitui a leitura do .env por credenciais fictícias.
    monkeypatch.setattr(
        telegram,
        "dotenv_values",
        lambda _: {
            "TELEGRAM_BOT_TOKEN": "123:token-ficticio",
            "TELEGRAM_CHAT_ID": "456",
        },
    )


def test_send_telegram_alert(monkeypatch, telegram_config):
    # Simula a confirmação de envio pela API.
    response = httpx.Response(200, json={"ok": True})
    post = Mock(return_value=response)
    monkeypatch.setattr(telegram.httpx, "post", post)

    telegram.send_telegram_alert("Queda simulada.")

    # Confere o destino e o texto da mensagem.
    post.assert_called_once_with(
        "https://api.telegram.org/bot123:token-ficticio/sendMessage",
        json={"chat_id": "456", "text": "Queda simulada."},
        timeout=15,
    )


def test_connection_error_hides_token(monkeypatch, telegram_config):
    # Simula uma falha cujo erro original contém uma credencial.
    post = Mock(side_effect=httpx.ConnectError("Falha com 123:token-ficticio"))
    monkeypatch.setattr(telegram.httpx, "post", post)

    with pytest.raises(RuntimeError) as error:
        telegram.send_telegram_alert("Queda simulada.")

    # Confere a mensagem que o monitor exibirá no terminal.
    assert str(error.value) == "Falha de conexão com o Telegram."