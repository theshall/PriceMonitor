"""Diagnostica o acesso à conta e ao anúncio sem exibir credenciais."""

import json
import time

import httpx
from dotenv import dotenv_values

from src.mercado_livre_config import PROJECT_ROOT


ITEM_ID = "MLB7756640194"


def show_result(label, response, access_token):
    # Mostra somente o resultado HTTP das consultas bem-sucedidas.
    print(f"{label} — HTTP: {response.status_code}")

    if response.status_code == 200:
        return

    # Alguns bloqueios retornam HTML em vez de JSON.
    try:
        error_data = response.json()
    except ValueError:
        print("O servidor retornou uma resposta fora do formato JSON.")
        return

    if not isinstance(error_data, dict):
        print("A resposta de erro tem formato inesperado.")
        return

    # Exibe apenas campos úteis para diagnosticar a recusa.
    for field in ("error", "code", "message", "blocked_by"):
        value = error_data.get(field)
        if value is not None:
            safe_value = str(value).replace(access_token, "[OCULTO]")
            print(f"{field}: {safe_value}")


def main():
    # Lê os tokens salvos pelo programa de autorização.
    settings = dotenv_values(PROJECT_ROOT / ".env")
    saved_tokens = settings.get("ML_TOKEN_JSON")

    if not saved_tokens:
        print("Tokens ausentes no .env.")
        return

    tokens = json.loads(saved_tokens)

    if time.time() >= tokens["expires_at"]:
        print("Token expirado. Precisamos renová-lo antes do diagnóstico.")
        return

    access_token = tokens["access_token"]

    with httpx.Client(
        base_url="https://api.mercadolibre.com",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    ) as client:
        # Verifica o acesso à conta que autorizou a aplicação.
        account_response = client.get("/users/me")
        show_result("Minha conta", account_response, access_token)

        # Verifica o acesso ao anúncio escolhido.
        item_response = client.get(f"/items/{ITEM_ID}")
        show_result("Anúncio", item_response, access_token)


if __name__ == "__main__":
    try:
        main()
    except httpx.RequestError:
        print("Falha de conexão com a API.")
    except (ValueError, KeyError, TypeError):
        print("Configuração de tokens inválida ou incompleta.")