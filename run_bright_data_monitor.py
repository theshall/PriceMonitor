"""Agenda a coleta de preços da oferta permanente a cada seis horas."""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler


def main():
    project_dir = Path(__file__).resolve().parent
    recorder = project_dir / "record_bright_data_price.py"
    if not recorder.is_file():
        raise SystemExit("Não encontrei record_bright_data_price.py.")

    def collect_and_record():
        # Usa o mesmo Python e ambiente virtual que iniciaram o monitor.
        result = subprocess.run(
            [sys.executable, str(recorder)],
            cwd=project_dir,
            check=False,
        )
        if result.returncode != 0:
            print(
                "A coleta terminou com erro. O próximo horário segue agendado.",
                flush=True,
            )

    first_run = datetime.now().astimezone() + timedelta(hours=6)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        collect_and_record,
        trigger="interval",
        hours=6,
        next_run_time=first_run,
        max_instances=1,
        coalesce=True,
    )

    print(
        f"Monitor ativo. Próxima coleta: {first_run:%d/%m/%Y às %H:%M:%S %z}.",
        flush=True,
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nEncerrando o monitor...")
    finally:
        # Aguarda uma coleta em andamento antes de encerrar.
        if scheduler.running:
            scheduler.shutdown(wait=True)


if __name__ == "__main__":
    main()