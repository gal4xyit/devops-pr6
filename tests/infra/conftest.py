import subprocess
from pathlib import Path

import pytest
import testinfra


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def host():
    result = subprocess.run(
        [
            "docker", "compose", "ps",
            "--status", "running", "-q", "web",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )

    container_ids = result.stdout.split()

    if len(container_ids) != 1:
        pytest.fail(
            "Expected exactly one running container for service 'web'. "
            "Run docker compose up first.",
            pytrace=False,
        )

    return testinfra.get_host(f"docker://{container_ids[0]}")