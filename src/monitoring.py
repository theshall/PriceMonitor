"""Coordena a coleta e o registro de preços."""

from src.schemas import PriceHistoryCreate


def monitor_offer(offer_id, collector, register_price):
    # Obtém os dados usando o coletor recebido.
    # Falhas de coleta são propagadas, impedindo a gravação.
    result = collector()

    # Uma oferta indisponível não gera registro de preço.
    if not result["available"]:
        return None

    # O monitor trabalha atualmente com preços em reais.
    if result["currency"] != "BRL":
        raise ValueError("O monitor aceita somente preços em BRL.")

    # Reutiliza a validação de preços já utilizada pela API.
    entry = PriceHistoryCreate(price=result["price"])

    # Registra o preço usando a função fornecida pelo chamador.
    return register_price(offer_id, entry.price)