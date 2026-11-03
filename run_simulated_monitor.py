"""Executa o monitor simulado periodicamente no banco de testes."""

from functools import partial
from itertools import cycle

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import text

import src.price_history as history
from src.database import test_engine
from src.monitoring import monitor_offer
from src.simulated_collector import collect_simulated_price


def main():
    # Verifica o banco configurado antes de criar qualquer registro.
    if test_engine.url.database != "price_monitor_test":
        raise RuntimeError("A simulação exige o banco price_monitor_test.")

    # Confirma também o banco realmente selecionado pelo MySQL.
    with test_engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT DATABASE()")
        ).scalar_one()

    if database_name != "price_monitor_test":
        raise RuntimeError("A conexão está usando um banco inesperado.")

    # Direciona o histórico para o banco de testes neste processo.
    history.engine = test_engine

    product_id = None
    offer_id = None
    scheduler = BlockingScheduler()

    # Repete os cenários em uma sequência conhecida.
    scenarios = cycle([
        "normal",
        "price_drop",
        "unavailable",
        "connection_error",
    ])

    try:
        # Cria um produto e uma oferta exclusivos desta execução.
        with test_engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO products (name, brand)
                    VALUES (:name, :brand)
                """),
                {
                    "name": "SIMULADO - Monitor periódico",
                    "brand": "Marca de Teste",
                },
            )
            product_id = result.lastrowid

            result = connection.execute(
                text("""
                    INSERT INTO offers (product_id, store_name, price)
                    VALUES (:product_id, :store_name, :price)
                """),
                {
                    "product_id": product_id,
                    "store_name": "SIMULADO - Loja periódica",
                    "price": "2599.90",
                },
            )
            offer_id = result.lastrowid

        def run_collection():
            # Escolhe o próximo cenário a cada execução.
            scenario = next(scenarios)
            collector = partial(collect_simulated_price, scenario)

            try:
                history_id = monitor_offer(
                    offer_id=offer_id,
                    collector=collector,
                    register_price=history.register_price,
                )
            except TimeoutError:
                # Registra a falha no terminal e permite a próxima rodada.
                print(f"[{scenario}] Falha simulada de conexão.", flush=True)
                return

            if history_id is None:
                print(f"[{scenario}] Produto indisponível.", flush=True)
            else:
                print(
                    f"[{scenario}] Histórico registrado. ID: {history_id}",
                    flush=True,
                )

        # Impede execuções simultâneas da mesma tarefa.
        scheduler.add_job(
            run_collection,
            trigger="interval",
            seconds=5,
            max_instances=1,
            coalesce=True,
        )

        print("Banco confirmado: price_monitor_test")
        print("Monitor iniciado. Pressione Ctrl+C para encerrar.")

        scheduler.start()

    except KeyboardInterrupt:
        print("\nEncerrando o monitor...")

    finally:
        # Espera a coleta em andamento terminar antes de limpar os dados.
        if scheduler.running:
            scheduler.shutdown(wait=True)

        # Remove somente os registros criados por esta execução.
        with test_engine.begin() as connection:
            if offer_id is not None:
                connection.execute(
                    text("DELETE FROM price_history WHERE offer_id = :id"),
                    {"id": offer_id},
                )
                connection.execute(
                    text("DELETE FROM offers WHERE id = :id"),
                    {"id": offer_id},
                )

            if product_id is not None:
                connection.execute(
                    text("DELETE FROM products WHERE id = :id"),
                    {"id": product_id},
                )

        print("Dados temporários removidos do banco de testes.")


if __name__ == "__main__":
    main()