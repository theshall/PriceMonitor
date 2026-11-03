"""Envia mensagens de alerta para a conversa configurada no Telegram."""

from pathlib import Path

import httpx
from dotenv import dotenv_values


def send_telegram_alert(message):
    # Lê a configuração da raiz do projeto.
    env_path = Path(__file__).resolve().parent.parent / ".env"
    settings = dotenv_values(env_path)

    token = settings.get("TELEGRAM_BOT_TOKEN")
    chat_id = settings.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("Preencha TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env.")

    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=15,
        )
    except httpx.RequestError:
        # Evita exibir a URL da requisição, que contém o token.
        raise RuntimeError("Falha de conexão com o Telegram.") from None

    if response.status_code != 200:
        raise RuntimeError(f"Envio recusado pelo Telegram. HTTP {response.status_code}.")

    try:
        accepted = response.json().get("ok") is True
    except (ValueError, AttributeError):
        raise RuntimeError("Resposta inesperada do Telegram.") from None

    if not accepted:
        raise RuntimeError("O Telegram não confirmou o envio.")


if __name__ == "__main__":
    # Envia uma única mensagem para validar a conversa.
    try:
        send_telegram_alert("Teste do Price Monitor: alertas do Telegram configurados. ok?")
    except RuntimeError as error:
        raise SystemExit(str(error)) from None

    print("Mensagem de teste aceita pelo Telegram.")