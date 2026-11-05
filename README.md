# DevOps PR6

Python-сервіс із маршрутами `/health` і `/version`. Потрібні Python, Git, curl, Docker і Docker Compose v2; стандартний порт — 8000.

## Підготовка

```bash
git clone https://github.com/gal4xyit/devops-pr6.git
cd devops-pr6

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
test -f .env || cp .env.example .env
mkdir -p reports
```

Наступні команди виконуються з кореня проєкту. Ручний запуск і відкат виконуються після завершення активного CD.

## Запуск

```bash
IMAGE_TAG=$(git rev-parse HEAD)
docker build --build-arg "APP_VERSION=$IMAGE_TAG" -t "devops-pr6:$IMAGE_TAG" .
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/deploy.sh "devops-pr6:$IMAGE_TAG"
```

Скрипт чекає готовності контейнера, перевіряє HTTP і виконує Testinfra.

## Перевірка

```bash
source .venv/bin/activate
mkdir -p reports

python -m pytest tests/unit -v --junitxml=reports/pytest.xml
python -m pytest tests/infra -v --junitxml=reports/testinfra.xml

docker compose ps
curl --fail --max-time 5 -i http://127.0.0.1:8000/health
curl --fail --max-time 5 -i http://127.0.0.1:8000/version
```

Для Testinfra контейнер має працювати. Очікуються 18 модульних і 6 інфраструктурних перевірок без помилок, стан `healthy`, HTTP 200 та SHA образу у `/version`.

## Відкат

Вкажіть повний SHA попереднього справного образу, який є локально:

```bash
docker image ls devops-pr6
OLD_SHA='REPLACE_WITH_PREVIOUS_GOOD_SHA'

docker image inspect --format '{{.Id}}' "devops-pr6:$OLD_SHA"
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/deploy.sh "devops-pr6:$OLD_SHA"

curl --fail --max-time 5 -i http://127.0.0.1:8000/health
curl --fail --max-time 5 -i http://127.0.0.1:8000/version
```

Замініть `REPLACE_WITH_PREVIOUS_GOOD_SHA` на потрібний SHA; тег `devops-pr6:rollback` зарезервований скриптом. Якщо перевірки нового розгортання не проходять і попередній образ існує, скрипт автоматично повертає його та завершується з кодом 1.

Звіти ручного запуску містяться в `reports/`, а CI/CD — в артефактах [GitHub Actions](https://github.com/gal4xyit/devops-pr6/actions).
