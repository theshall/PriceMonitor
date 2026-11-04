"""Consulta uma oferta piloto na Bright Data e valida o preço retornado."""

import json
from decimal import Decimal
from pathlib import Path

import httpx
from dotenv import dotenv_values

from check_bright_data_result import validate_pilot_price


DATASET_ID = "gd_m7re62tb1w88ymy86r"
PILOT_URL = (
    "https://www.mercadolivre.com.br/"
    "ar-condicionado-split-lg-dual-inverter-ai-voice-9000-btu-frio/"
    "p/MLB66277100?pdp_filters=item_id:MLB7756640194"
)


def collect_pilot_price(api_key):
    # Solicita uma única coleta para a URL já conferida no painel.
    response = httpx.post(
        "https://api.brightdata.com/datasets/v3/scrape",
        params={"dataset_id": DATASET_ID, "format": "json"},
        headers={"Authorization": f"Bearer {api_key}"},
        json={"input": [{"url": PILOT_URL}]},
        timeout=75,
    )

    if response.status_code == 202:
        # A execução continua na Bright Data e pode ser aberta no painel.
        snapshot_id = response.json().get("snapshot_id")
        raise RuntimeError(f"Coleta ainda em processamento. ID: {snapshot_id}")

    if response.status_code != 200:
        raise RuntimeError(f"Consulta recusada. HTTP {response.status_code}.")

    # Aplica a mesma validação usada para o JSON baixado.
    records = json.loads(response.text, parse_float=Decimal)
    return validate_pilot_price(records)


def main():
    # Lê a chave do arquivo local sem exibir seu valor.
    settings = dotenv_values(Path(__file__).with_name(".env"))
    api_key = settings.get("BRIGHT_DATA_API_KEY")

    if not api_key or api_key == "COLE_A_CHAVE_AQUI":
        raise SystemExit("Preencha BRIGHT_DATA_API_KEY no .env.")

    try:
        price = collect_pilot_price(api_key)
    except httpx.RequestError:
        raise SystemExit(
            "Falha de comunicação. Confira Instantâneos antes de repetir a consulta."
        ) from None
    except (RuntimeError, ValueError) as error:
        raise SystemExit(f"Preço não validado. {error}") from None

    print(f"Oferta validada pela API. Preço: BRL {price:.2f}")


if __name__ == "__main__":
    main()