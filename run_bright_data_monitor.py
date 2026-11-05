"""Coleta preços a cada dez minutos e processa alertas a cada minuto."""

import subprocess
import sys
import ctypes
from ctypes import wintypes
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler


@contextmanager
def single_monitor_instance():
    # O Windows compartilha esta reserva entre os processos da sessão.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateMutexW(None, False, "Local\\PriceMonitor.SingleInstance")
    error = ctypes.get_last_error()
    if not handle:
        raise ctypes.WinError(error)
    try:
        # ERROR_ALREADY_EXISTS indica outra cópia ainda ativa.
        yield error != 183
    finally:
        kernel.CloseHandle(handle)


def run_monitor():
    project_dir = Path(__file__).resolve().parent
    recorder = project_dir / "record_bright_data_price.py"
    if not recorder.is_file():
        raise SystemExit("Não encontrei record_bright_data_price.py.")
    sender = project_dir / "send_pending_alert.py"
    if not sender.is_file():
        raise SystemExit("Não encontrei send_pending_alert.py.")

    def collect_and_record():
        # Executa a coleta e a gravação do preço.
        started_at = datetime.now().astimezone().isoformat(timespec="seconds")
        print(f"{started_at} | Coleta iniciada.", flush=True)
        result = subprocess.run(
            [sys.executable, str(recorder)],
            cwd=project_dir,
            check=False,
        )
        finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
        print(
            f"{finished_at} | Coleta encerrada. Código: {result.returncode}.",
            flush=True,
        )
        if result.returncode != 0:
            print(
                "A coleta terminou com erro. O próximo horário segue agendado.",
                flush=True,
            )

    def send_pending():
        # Processa a fila independentemente do resultado da coleta.
        delivery = subprocess.run(
            [sys.executable, str(sender), "--quiet"],
            cwd=project_dir,
            check=False,
        )
        if delivery.returncode != 0:
            print(
                "O envio terminou com erro. O alerta permanece pendente.",
                flush=True,
            )

    # Agenda a primeira execução para daqui a 10 minutos.
    now = datetime.now().astimezone()
    first_run = now + timedelta(minutes=10)
    first_delivery = now + timedelta(minutes=1)
    scheduler = BlockingScheduler()
    scheduler.add_job(
        collect_and_record,
        id="collect_prices",
        trigger="interval",
        minutes=10,
        next_run_time=first_run,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        send_pending,
        id="deliver_alert",
        trigger="interval",
        minutes=1,
        next_run_time=first_delivery,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    print(
        f"Monitor ativo. Próxima coleta: {first_run:%d/%m/%Y às %H:%M:%S %z}.",
        flush=True,
    )
    print(
        f"Fila do Telegram a cada minuto. Próxima tentativa: "
        f"{first_delivery:%d/%m/%Y às %H:%M:%S %z}.",
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


def main():
    # Protege tanto o início pelo terminal quanto o início pelo Windows.
    with single_monitor_instance() as acquired:
        if not acquired:
            print("O monitor já está em execução nesta sessão do Windows.", flush=True)
            return
        run_monitor()


if __name__ == "__main__":
    main()
