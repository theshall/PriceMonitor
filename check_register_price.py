
"""
Verifica o cadastro e a consulta do histórico de preços.

Este script utiliza exclusivamente o banco price_monitor_test.
"""

from decimal import Decimal

import src.price_history as history
from src.database import test_engine


# Redireciona as funções de histórico para o banco de testes.
history.engine = test_engine

# Substitua pelo ID real de uma oferta do banco de testes.
offer_id = 1

# Define um preço usando Decimal para preservar a precisão.
price = Decimal("119.90")

# Registra o preço e recupera o identificador gerado.
history_id = history.register_price(offer_id, price)

print(f"Registro de histórico criado: {history_id}")

# Verifica se o MySQL retornou um ID válido.
assert history_id is not None

# Consulta os preços registrados para a oferta.
records = history.list_price_history(offer_id)

print("Histórico encontrado:")

for record in records:
    print(record)

# Verifica se o registro recém-criado está presente.
assert any(
    record["id"] == history_id
    and record["price"] == price
    for record in records
)

print("Cadastro e consulta do histórico validados!")
