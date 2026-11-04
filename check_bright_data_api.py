"""Consulta uma oferta piloto na Bright Data e valida o preço retornado."""

import json
from decimal import Decimal
from pathlib import Path
import argparse
import re
from time import sleep
import httpx
from dotenv import dotenv_values

from check_bright_data_result import validate_pilot_price


DATASET_ID = "gd_m7re62tb1w88ymy86r"
PILOT_URL = (
    "https://www.mercadolivre.com.br/"
    "ar-condicionado-split-lg-dual-inverter-ai-voice-9000-btu-frio/"
    "p/MLB66277100?pdp_filters=item_id:MLB7756640194"
)

def read_snapshot_price(api_key, snapshot_id):
    # Confere o identificador antes de incluí-lo no endereço da consulta.
    if not isinstance(snapshot_id, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]+", snapshot_id
    ):
        raise ValueError("A Bright Data não retornou um ID de coleta válido.")

    with httpx.Client(
        base_url="https://api.brightdata.com/datasets/v3/",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    ) as client:
        # Consulta o estado da mesma coleta até 12 vezes.
        for attempt in range(12):
            progress = client.get(f"progress/{snapshot_id}")
            if progress.status_code != 200:
                raise RuntimeError(
                    f"Falha ao consultar a coleta {snapshot_id}. "
                    f"HTTP {progress.status_code}."
                )

            status = progress.json().get("status")

            if status == "ready":
                # Baixa o resultado da coleta original e valida a oferta.
                result = client.get(
                    f"snapshot/{snapshot_id}",
                    params={"format": "json"},
                )
                if result.status_code == 200:
                    records = json.loads(result.text, parse_float=Decimal)
                    return validate_pilot_price(records)

                # O arquivo pode continuar pendente por alguns segundos.
                if result.status_code != 202:
                    raise RuntimeError(
                        f"Falha ao baixar a coleta {snapshot_id}. "
                        f"HTTP {result.status_code}."
                    )
            elif status not in {"starting", "running"}:
                raise RuntimeError(
                    f"Coleta {snapshot_id} com status inesperado: {status}."
                )

            if attempt < 11:
                sleep(5)

    raise RuntimeError(
        f"Resultado ainda pendente. Consulte o ID {snapshot_id} em Instantâneos."
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
    # Acompanha a coleta já iniciada.
        snapshot_id = response.json().get("snapshot_id")
        return read_snapshot_price(api_key, snapshot_id)

    if response.status_code != 200:
        raise RuntimeError(f"Consulta recusada. HTTP {response.status_code}.")

    # Aplica a mesma validação usada para o JSON baixado.
    records = json.loads(response.text, parse_float=Decimal)
    return validate_pilot_price(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot-id",
        help="Recupera uma coleta existente pelo ID.",
    )
    args = parser.parse_args()    
    # Lê a chave do arquivo local sem exibir seu valor.
    settings = dotenv_values(Path(__file__).with_name(".env"))
    api_key = settings.get("BRIGHT_DATA_API_KEY")

    if not api_key or api_key == "COLE_A_CHAVE_AQUI":
        raise SystemExit("Preencha BRIGHT_DATA_API_KEY no .env.")

    try:
        if args.snapshot_id:
            price = read_snapshot_price(api_key, args.snapshot_id)
        else:
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