"""Autoriza a integração e salva os tokens localmente no .env."""

import json
import secrets
import time
from getpass import getpass
from urllib.parse import parse_qs, urlparse

import httpx
from dotenv import set_key

from src.mercado_livre_auth import create_authorization_request
from src.mercado_livre_config import (
    PROJECT_ROOT,
    load_mercado_livre_config,
)


def main():
    config = load_mercado_livre_config()
    authorization = create_authorization_request()
    started_at = time.monotonic()

    # Mantém o state e o segredo PKCE na memória deste programa.
    print("Abra este link no navegador e autorize sua aplicação:")
    print(authorization["authorization_url"])

    # Oculta a URL digitada porque ela contém um código temporário.
    returned_url = getpass(
        "\nApós autorizar, cole a URL completa de retorno e pressione Enter: "
    ).strip()

    # Limita a duração desta tentativa de autorização.
    if time.monotonic() - started_at > 600:
        raise ValueError("Tentativa expirada. Execute o programa novamente.")

    returned = urlparse(returned_url)
    expected = urlparse(config["redirect_uri"])

    # Confere se o retorno usa o endereço cadastrado.
    if (
        returned.scheme,
        returned.netloc,
        returned.path,
    ) != (
        expected.scheme,
        expected.netloc,
        expected.path,
    ):
        raise ValueError("O endereço de retorno difere do configurado.")

    parameters = parse_qs(returned.query)
    states = parameters.get("state", [])

    # Confere se o retorno pertence à solicitação iniciada aqui.
    if len(states) != 1 or not secrets.compare_digest(
        states[0], authorization["state"]
    ):
        raise ValueError("O state recebido é inválido.")

    if "error" in parameters:
        raise ValueError("A autorização foi recusada pelo Mercado Livre.")

    codes = parameters.get("code", [])
    if len(codes) != 1:
        raise ValueError("O retorno não contém um código de autorização válido.")

    # Troca o código pelo token enviando os segredos no corpo da requisição.
    response = httpx.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": codes[0],
            "redirect_uri": config["redirect_uri"],
            "code_verifier": authorization["code_verifier"],
        },
        timeout=20,
    )

    # Evita imprimir a resposta completa, que pode conter credenciais.
    if response.status_code != 200:
        raise ValueError(
            f"Falha ao obter o token. HTTP {response.status_code}. "
            "Execute novamente para iniciar uma nova autorização."
        )

    tokens = response.json()

    if not tokens.get("access_token") or not tokens.get("refresh_token"):
        raise ValueError("A resposta não contém os dois tokens esperados.")

    expires_in = int(tokens["expires_in"])
    if expires_in <= 0:
        raise ValueError("O token recebido tem validade inválida.")

    # Guarda os tokens e a expiração em uma única configuração.
    saved_tokens = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_at": int(time.time()) + expires_in,
    }

    set_key(
        str(PROJECT_ROOT / ".env"),
        "ML_TOKEN_JSON",
        json.dumps(saved_tokens),
    )

    print("Autorização concluída. Tokens salvos no .env.")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(f"Autorização interrompida: {error}")
    except httpx.RequestError:
        print("Falha de conexão com o Mercado Livre. Inicie uma nova tentativa.")
    except OSError:
        print("Falha ao acessar os arquivos locais de configuração.")