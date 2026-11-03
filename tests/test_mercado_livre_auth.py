"""Testa a preparação da autorização sem acessar serviços externos."""

import base64
import hashlib
from urllib.parse import parse_qs, urlparse

import src.mercado_livre_auth as auth


def test_create_authorization_request(monkeypatch):
    # Usa configurações fictícias durante o teste.
    monkeypatch.setattr(
        auth,
        "load_mercado_livre_config",
        lambda: {
            "client_id": "123456",
            "client_secret": "segredo-ficticio",
            "redirect_uri": "https://example.com/oauth/mercadolivre/callback",
        },
    )

    request = auth.create_authorization_request()
    parsed_url = urlparse(request["authorization_url"])
    parameters = parse_qs(parsed_url.query)

    # Confere o destino e os parâmetros da autorização.
    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "auth.mercadolivre.com.br"
    assert parameters["client_id"] == ["123456"]
    assert parameters["state"] == [request["state"]]
    assert parameters["code_challenge_method"] == ["S256"]

    # Confere se o desafio corresponde ao segredo temporário.
    verifier = request["code_verifier"]
    assert 43 <= len(verifier) <= 128

    expected_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    assert parameters["code_challenge"] == [expected_challenge]

    # Confere que os segredos não foram incluídos no link.
    assert "client_secret" not in parameters
    assert "code_verifier" not in parameters

    # Cada tentativa deve gerar novos valores.
    another_request = auth.create_authorization_request()
    assert another_request["state"] != request["state"]
    assert another_request["code_verifier"] != verifier