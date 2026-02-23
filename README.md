# Stratego

A Python implementation of the classic two-player board game **Stratego**.

## Requirements

- Python 3.12 or later
- [pygame-ce](https://pypi.org/project/pygame-ce/) 2.4+
- [pygame-gui](https://pypi.org/project/pygame-gui/) 0.6+
- [pyyaml](https://pypi.org/project/PyYAML/) 6.0+

## Installation

Install directly from the repository:

```bash
# Standard install (game dependencies only)
pip install .

# Editable install for development (includes linting and test tools)
pip install -e ".[dev]"
```

## Running the game

After installation a `stratego` command is available:

```bash
stratego
```

Alternatively you can run the package directly without installing:

```bash
python -m src
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--config PATH` | `~/.stratego/config.yaml` | Path to a custom `config.yaml` |
| `--log-level LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

Example:

```bash
stratego --config ./my_config.yaml --log-level DEBUG
```

## Configuration

On first run the application uses built-in defaults.  To customise, create
`~/.stratego/config.yaml`:

```yaml
display:
  resolution: [1280, 720]
  fps_cap: 60
  fullscreen: false

ai:
  default_difficulty: medium   # easy | medium | hard
  time_limit_ms: 950

persistence:
  save_directory: ~/.stratego/saves
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Lint
ruff check src

# Type-check
mypy src
```

## Project structure

```
src/
  domain/          # Game rules, board, pieces, combat — no I/O
  application/     # Game loop, controller, event bus, commands
  ai/              # Minimax + alpha-beta search, evaluation, opening book
  presentation/    # pygame renderer, input handler, screens
  infrastructure/  # JSON persistence, config, logging
  Tests/           # Unit and integration tests
specifications/    # Architecture documents and game rules
planning/          # Sprint plans and product backlog
```

## Licence

See [LICENSE](LICENSE).
