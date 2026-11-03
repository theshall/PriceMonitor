"""Serviço inicial para testar o endereço de retorno da autorização."""

from fastapi import FastAPI

# Desativa as páginas de documentação neste serviço dedicado.
app = FastAPI(
    title="Price Monitor - Autorização",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/oauth/mercadolivre/callback")
def mercado_livre_callback():
    # Confirma que o endereço está acessível.
    # A validação da autorização será implementada na próxima etapa.
    return {
        "status": "ok",
        "message": "Endereço de retorno do Price Monitor disponível.",
    }