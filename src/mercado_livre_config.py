"""Carrega e valida as configurações da integração com o Mercado Livre."""

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


# Localiza o .env a partir da pasta do projeto.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def load_mercado_livre_config():
    # Lê as configurações sem exibir credenciais.
    config = {
        "client_id": os.getenv("ML_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("ML_CLIENT_SECRET", "").strip(),
        "redirect_uri": os.getenv("ML_REDIRECT_URI", "").strip(),
    }

    # Interrompe a execução caso alguma configuração esteja vazia.
    for field, value in config.items():
        if not value:
            raise ValueError(
                f"Configuração obrigatória ausente: ML_{field.upper()}"
            )

    # Confere o formato do identificador da aplicação.
    if not config["client_id"].isdigit():
        raise ValueError("ML_CLIENT_ID deve conter somente números.")

    # Confere o endereço que receberá a autorização.
    redirect = urlparse(config["redirect_uri"])

    if redirect.scheme != "https" or not redirect.hostname:
        raise ValueError("ML_REDIRECT_URI deve ser um endereço HTTPS válido.")

    if redirect.path != "/oauth/mercadolivre/callback":
        raise ValueError("ML_REDIRECT_URI deve terminar com a rota de callback.")

    if redirect.query or redirect.fragment or redirect.username:
        raise ValueError(
            "ML_REDIRECT_URI deve estar sem parâmetros, fragmentos ou usuário."
        )

    return config


if __name__ == "__main__":
    # Permite verificar a configuração sem imprimir seus valores.
    load_mercado_livre_config()
    print("Configurações do Mercado Livre carregadas e formato validado.")