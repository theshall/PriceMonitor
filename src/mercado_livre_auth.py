"""Prepara a autorização do Mercado Livre com PKCE e state."""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

from src.mercado_livre_config import load_mercado_livre_config


def create_authorization_request():
    # Carrega as configurações já validadas.
    config = load_mercado_livre_config()

    # Gera um segredo temporário usado na troca do código pelo token.
    code_verifier = secrets.token_urlsafe(64)

    # Calcula o desafio PKCE usando SHA-256 e Base64 URL-safe.
    verifier_hash = hashlib.sha256(
        code_verifier.encode("ascii")
    ).digest()

    code_challenge = (
        base64.urlsafe_b64encode(verifier_hash)
        .rstrip(b"=")
        .decode("ascii")
    )

    # Identifica esta tentativa de autorização.
    state = secrets.token_urlsafe(32)

    # Monta os parâmetros enviados à página de autorização.
    parameters = {
        "response_type": "code",
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = (
        "https://auth.mercadolivre.com.br/authorization?"
        + urlencode(parameters)
    )

    # O programa que iniciar a autorização deverá guardar estes dados
    # até receber e validar o retorno do Mercado Livre.
    return {
        "authorization_url": authorization_url,
        "state": state,
        "code_verifier": code_verifier,
    }