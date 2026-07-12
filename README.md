# RabbitMQ broker examples

Examples for testing RabbitMQ message broker access from Python in two modes:

- synchronous client with `pika`
- asynchronous client with `aio-pika`

The examples use a single queue named `ping_pong` by default and demonstrate
publishing, one-shot consuming, and callback-based consuming.

## Requirements

- Python 3.11 or newer (`python3` on Debian/Ubuntu based systems)
- Poetry 2.x
- RabbitMQ reachable from the machine running the examples

## Environment

The examples read RabbitMQ connection settings from environment variables.
When a variable is not set, the local development defaults are used.

| Variable | Default | Description |
| --- | --- | --- |
| `RABBITMQ_HOST` | `localhost` | RabbitMQ host name |
| `RABBITMQ_PORT` | `5672` | RabbitMQ AMQP port |
| `RABBITMQ_USERNAME` | `user` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | `passwd` | RabbitMQ password |
| `RABBITMQ_QUEUE` | `ping_pong` | Queue used by the examples |

Example:

```bash
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_USERNAME=user
export RABBITMQ_PASSWORD=passwd
export RABBITMQ_QUEUE=ping_pong
```

## Setup

Install dependencies with Poetry:

```bash
poetry install
```

If Poetry is not installed, install it outside the project environment first:

```bash
python3 -m pip install --user poetry
```

## Run

Run the synchronous example functions from a Python shell:

```bash
poetry run python -c "import sync; sync.sender(); sync.receiver_simple()"
```

Run the asynchronous example functions:

```bash
poetry run python -c "import asyncio, asyncb; asyncio.run(asyncb.sender()); asyncio.run(asyncb.receiver_simple())"
```

Both commands require RabbitMQ to be running and reachable with the configured
credentials.

## Test

Run the unit test suite:

```bash
poetry run pytest
```

Run tests with coverage:

```bash
poetry run pytest --cov=. --cov-report=term-missing
```

Run a dependency audit against the locked Poetry dependencies:

```bash
poetry export -f requirements.txt --without-hashes -o /tmp/broker-requirements.txt
poetry run pip-audit -r /tmp/broker-requirements.txt
```

## Queue flags

- `exclusive` binds a queue to one consumer. When that consumer disconnects,
  the queue and its data are removed.
- `auto_delete` keeps a queue while consumers exist. After the last consumer
  unsubscribes, the queue is removed.
