"""Testa a gravação de alertas em um arquivo temporário."""

from decimal import Decimal

from src.price_alerts import write_price_drop_alert
from src.price_comparison import calculate_price_drop


def test_only_qualifying_drops_are_written(tmp_path):
    # Usa um arquivo isolado, criado pelo pytest para este teste.
    alert_path = tmp_path / "simulated_alerts.log"
    comparison = calculate_price_drop("2599.90", "2399.90")

    # O valor de 7,69% alcança o limite de 5%.
    message = write_price_drop_alert(comparison, Decimal("5"), alert_path)
    assert message == "QUEDA SIMULADA: economia de R$ 200,00 (7,69%)."

    original = alert_path.read_text(encoding="utf-8")
    assert original.splitlines()[0].endswith(f" | {message}")

    # Com limite de 10%, a mesma queda preserva o conteúdo do arquivo.
    assert write_price_drop_alert(comparison, Decimal("10"), alert_path) is None
    assert alert_path.read_text(encoding="utf-8") == original