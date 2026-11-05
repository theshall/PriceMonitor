"""Testa a sequência do agendador com processos simulados."""

from unittest.mock import Mock

import pytest

import run_bright_data_monitor as monitor


@pytest.mark.parametrize("collection_returncode", [0, 1])
@pytest.mark.parametrize("delivery_returncode", [0, 1])
def test_independent_collection_and_delivery(
    monkeypatch, collection_returncode, delivery_returncode
):
    # Simula sucessos e falhas sem consultar serviços externos.
    run = Mock(
        side_effect=[
            Mock(returncode=collection_returncode),
            Mock(returncode=delivery_returncode),
        ]
    )
    monkeypatch.setattr(monitor.subprocess, "run", run)

    # Substitui o agendador para executar a tarefa imediatamente no teste.
    scheduler = Mock()
    scheduler.running = False

    def start():
        # O agendador deve cadastrar tarefas com intervalos independentes.
        jobs = {
            call.kwargs["id"]: call
            for call in scheduler.add_job.call_args_list
        }
        assert len(jobs) == 2
        collection = jobs["collect_prices"]
        delivery = jobs["deliver_alert"]
        assert collection.kwargs["minutes"] == 10
        assert delivery.kwargs["minutes"] == 1
        for job in jobs.values():
            assert job.kwargs["max_instances"] == 1
            assert job.kwargs["coalesce"] is True

        # A coleta executa apenas seu próprio processo.
        collection.args[0]()
        assert run.call_count == 1
        # A tarefa de envio continua disponível mesmo após falha na coleta.
        delivery.args[0]()

    scheduler.start.side_effect = start
    monkeypatch.setattr(
        monitor,
        "BlockingScheduler",
        Mock(return_value=scheduler),
    )

    # Testa o agendador isolado da trava da instância real.
    monitor.run_monitor()

    # O envio deve ser tentado nos dois resultados possíveis da coleta.
    assert run.call_count == 2

    collection_command = run.call_args_list[0].args[0]
    delivery_command = run.call_args_list[1].args[0]

    assert collection_command[0] == monitor.sys.executable
    assert collection_command[1].endswith("record_bright_data_price.py")
    assert delivery_command[0] == monitor.sys.executable
    assert delivery_command[1].endswith("send_pending_alert.py")
    assert delivery_command[2:] == ["--quiet"]
