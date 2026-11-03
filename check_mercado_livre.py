"""Verifica o acesso à página do produto pelo Python."""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

# Página do produto que queremos monitorar.
PRODUCT_URL = (
    "https://www.mercadolivre.com.br/"
    "ar-condicionado-split-lg-dual-inverter-ai-voice-9000-btu-frio/"
    "p/MLB66277100"
)

# Solicita uma página HTML.
request = Request(
    PRODUCT_URL,
    headers={
        "User-Agent": "PriceMonitor/0.1",
        "Accept": "text/html",
    },
)

try:
    # Limita o tempo de espera pela resposta.
    with urlopen(request, timeout=20) as response:
        final_url = response.url
        final_path = urlparse(final_url).path

        print("Código HTTP:", response.status)

        # Identifica o redirecionamento para verificação de conta.
        if final_path.startswith("/gz/account-verification"):
            print("Resultado: verificação de conta exigida.")
            print("A coleta foi interrompida sem obter um preço.")
        else:
            # Lê o conteúdo para uma análise posterior.
            encoding = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(encoding, errors="replace")

            print("Endereço final:", final_url)
            print("Tamanho da página:", len(html), "caracteres")
            print(
                "Contém JSON-LD:",
                "application/ld+json" in html.lower(),
            )

except HTTPError as error:
    # Trata respostas HTTP de erro.
    print("Acesso recusado ou erro HTTP:", error.code)

except URLError as error:
    # Trata falhas de conexão.
    print("Falha de conexão:", error.reason)

except TimeoutError:
    print("O servidor não respondeu dentro de 20 segundos.")