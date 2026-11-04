"""Valida o preço coletado pela Bright Data para a oferta piloto."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from src.schemas import PriceHistoryCreate


def read_pilot_price(json_path):
    # Lê o preço como Decimal para preservar a precisão monetária.
    records = json.loads(
        json_path.read_text(encoding="utf-8-sig"),
        parse_float=Decimal,
    )
    return validate_pilot_price(records)

def validate_pilot_price(records):
    # A consulta piloto deve retornar exatamente um registro.
    if not isinstance(records, list) or len(records) != 1:
        raise ValueError("O JSON deve conter exatamente um registro.")

    record = records[0]
    if not isinstance(record, dict) or record.get("error"):
        raise ValueError("A coleta não retornou um registro válido.")

    # Confere a identidade antes de aceitar qualquer preço.
    if record.get("catalog_product_id") != "MLB66277100":
        raise ValueError("O catálogo retornado difere do esperado.")

    if str(record.get("seller_id")) != "167787623":
        raise ValueError("O vendedor retornado difere da Mega Byte.")

    voltages = {
        str(feature.get("value", "")).replace(" ", "").upper()
        for feature in record.get("product_features") or []
        if feature.get("type") == "Voltagem da unidade externa"
    }
    if voltages != {"220V"}:
        raise ValueError("A voltagem da unidade externa não pôde ser confirmada.")

    if record.get("in_stock") is not True:
        raise ValueError("A coleta não confirmou estoque.")

    if record.get("currency") != "BRL":
        raise ValueError("A coleta não retornou um preço em reais.")

    # Aplica a mesma validação monetária usada no histórico.
    return PriceHistoryCreate(price=record.get("final_price")).price


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="JSON baixado da Bright Data.")
    args = parser.parse_args()

    try:
        price = read_pilot_price(args.json_path)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Coleta rejeitada: {error}\n")

    display_price = format(price, ",.2f").replace(",", "_")
    display_price = display_price.replace(".", ",").replace("_", ".")
    print(f"Oferta validada. Preço: R$ {display_price}")


if __name__ == "__main__":
    main()