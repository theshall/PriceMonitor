"""Agenda duas consultas ao vivo para validar o coletor da Bright Data."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import dotenv_values
from contextlib import ExitStack

from sqlalchemy.exc import SQLAlchemyError

import src.price_history as history
from check_bright_data_history import temporary_pilot_offer
from check_bright_data_api import collect_pilot_price


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=21600,
        help="Intervalo entre consultas em segundos. Padrão: 6 horas.",
    )
    args = parser.parse_args()

    # A consulta HTTP pode aguardar até 75 segundos.
    if args.interval_seconds < 90:
        parser.error("--interval-seconds deve ser de pelo menos 90 segundos.")

    settings = dotenv_values(Path(__file__).with_name(".env"))
    api_key = settings.get("BRIGHT_DATA_API_KEY")
    if not api_key or api_key == "COLE_A_CHAVE_AQUI":
        parser.error("Preencha BRIGHT_DATA_API_KEY no .env.")

    finished = Event()
    attempts = 0
    failed = False
    resources = ExitStack()
    offer_id = None

    def run_collection():
        nonlocal attempts, failed, offer_id

        # Protege o limite de consultas mesmo durante o encerramento.
        if finished.is_set():
            return

        attempts += 1
        print(f"Consulta {attempts}/2 iniciada.", flush=True)

        try:
            # Reaproveita a consulta e a validação já testadas.
            price = collect_pilot_price(api_key)
                        # Abre a oferta na primeira coleta e a reutiliza na segunda.
            if offer_id is None:
                offer_id = resources.enter_context(temporary_pilot_offer(price))

            # Grava imediatamente após validar a resposta da Bright Data.
            history_id = history.register_price(offer_id, price)
        except httpx.RequestError:
            print(
                "Falha de comunicação. Confira Instantâneos na Bright Data.",
                flush=True,
            )
            failed = True
        except (RuntimeError, ValueError) as error:
            print(f"Preço não validado. {error}", flush=True)
            failed = True
        except SQLAlchemyError:
            print("Falha ao gravar no banco de testes.", flush=True)
            failed = True
        else:
           
            print(f"Oferta validada. Preço: BRL {price:.2f}", flush=True)
            print(f"Histórico registrado. ID: {history_id}", flush=True)
        finally:
            # Encerra após a segunda tentativa ou após uma falha tratada.
            if attempts >= 2 or failed:
                finished.set()

    scheduler = BackgroundScheduler(timezone=timezone.utc)
    scheduler.add_job(
        run_collection,
        trigger="interval",
        seconds=args.interval_seconds,
        next_run_time=datetime.now(timezone.utc),
        max_instances=1,
        coalesce=True,
    )

    print(f"Piloto iniciado. Intervalo: {args.interval_seconds} segundos.", flush=True)
    scheduler.start()

    try:
        finished.wait()
    except KeyboardInterrupt:
        print("\nEncerrando o piloto...")
    finally:
        # Aguarda uma consulta em andamento antes de sair.
        finished.set()
        scheduler.shutdown(wait=True)
        # Remove a oferta somente depois que a tarefa agendada terminar.
        resources.close()

    if failed:
        raise SystemExit("Piloto encerrado após falha na consulta.")
    print(f"Piloto encerrado. Consultas iniciadas: {attempts}.")


if __name__ == "__main__":
    main()