import src.price_history as history
from src.database import test_engine

# Utiliza exclusivamente o banco de testes.
history.engine = test_engine

# Consulta um identificador inexistente.
result = history.list_price_history(999999999)

print("Histórico encontrado:", result)

assert result == []

print("Consulta de histórico validada!")
