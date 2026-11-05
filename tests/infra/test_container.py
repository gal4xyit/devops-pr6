import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/app/app.py",
        "/app/gunicorn.conf.py",
        "/app/requirements.lock",
    ],
)
def test_required_files_exist(host, path):
    file = host.file(path)

    assert file.exists
    assert file.is_file


def test_gunicorn_is_running(host):
    master = host.process.get(pid=1)

    assert "gunicorn" in master.args

    workers = host.process.filter(ppid=master.pid)

    assert workers, "Gunicorn has no worker processes"
    assert all("gunicorn" in worker.args for worker in workers)


def test_application_port_is_listening(host):
    port = int(host.check_output("printenv APP_PORT"))

    assert host.socket(f"tcp://0.0.0.0:{port}").is_listening


def test_application_runs_as_non_root(host):
    assert host.check_output("id -u") == "10001"

    master = host.process.get(pid=1)
    workers = host.process.filter(ppid=master.pid)

    for process in [master, *workers]:
        assert process.user == "appuser", (
            f"Process {process.pid} runs as {process.user}"
        )