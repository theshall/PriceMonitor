"""Localiza a conversa privada que receberá os alertas."""

from pathlib import Path

import httpx
from dotenv import dotenv_values


def main():
    # Lê o token do .env sem exibi-lo no terminal.
    settings = dotenv_values(Path(__file__).with_name(".env"))
    token = settings.get("TELEGRAM_BOT_TOKEN")

    if not token or token == "COLE_O_TOKEN_AQUI":
        print("Preencha TELEGRAM_BOT_TOKEN no .env.")
        return

    try:
        # Confere qual bot corresponde ao token do .env.
        bot_response = httpx.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=15,
        )
        if bot_response.status_code != 200:
            print(f"Falha ao identificar o bot. HTTP {bot_response.status_code}.")
            return

        print("Bot configurado: @" + bot_response.json()["result"]["username"])
        response = httpx.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"allowed_updates": '["message"]'},timeout=15,
        )
    except httpx.RequestError:
        print("Falha de conexão com o Telegram.")
        return

    # Exibe apenas o status em caso de erro, pois a URL contém o token.
    if response.status_code != 200:
        print(f"Consulta ao Telegram recusada. HTTP {response.status_code}.")
        return

    # Seleciona somente conversas privadas com a mensagem de teste.
    print("Atualizações recebidas:", len(response.json()["result"]))
    chat_ids = set()
    for update in response.json()["result"]:
        message = update.get("message", {})
        chat = message.get("chat", {})
        if chat.get("type") == "private" and chat.get("id") is not None:
            chat_ids.add(chat["id"])

    if len(chat_ids) != 1:
        print("Não foi possível identificar uma única conversa de teste.")
        return

    print(f"TELEGRAM_CHAT_ID={chat_ids.pop()}")


if __name__ == "__main__":
    main()