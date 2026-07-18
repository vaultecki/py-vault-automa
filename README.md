# VaultState

JSON-based Finite State Machine (FSM) implementation in Python, with signal
support via `psygnal`, structure validation, and logging.

## Installation

```bash
pip install .
```

For development (adds `pytest`, `ruff`, `mypy`):

```bash
pip install -e ".[dev]"
```

Dependencies are declared in `pyproject.toml` (currently just `psygnal>=0.11`).

## Quick Start

### 1. Create an FSM configuration

Example (`example_fsm.json`):

```json
{
  "version": 0.1,
  "initial": "Superstate",
  "data": {
    "origin": "38.5200248466315,-28.6320306729769",
    "number_vehicles": 2,
    "role_vehicle1": "lsv",
    "role_vehicle2": "ssv"
  },
  "state": {
    "Superstate": {
      "transition": {
        "init_ok": "mp_init_01"
      }
    },
    "mp_init_01": {
      "transition": {
        "start": "mp_change_02",
        "abort": "mp_end_03"
      },
      "data": {
        "service": "standard"
      }
    },
    "mp_change_02": {
      "data": {
        "rel_pos_vehicle_1": [0.0, 0.0, 10.0],
        "rel_pos_vehicle_2": [-7.0, -7.0, 0.0]
      },
      "transition": {
        "formation_ok": "mp_end_03",
        "abort": "mp_end_03"
      }
    },
    "mp_end_03": {
      "data": {},
      "transition": {}
    }
  }
}
```

### 2. Use the FSM

```python
from vault_state import VaultState
import logging

logging.basicConfig(level=logging.INFO)

fsm = VaultState("example_fsm.json")

print(fsm.get_current_state())        # "Superstate"
print(fsm.get_data())                 # current state data merged with global data
print(fsm.get_possible_transitions()) # ["init_ok"]

fsm.event("init_ok")
print(fsm.get_current_state())        # "mp_init_01"
```

## Logging

VaultState uses Python's standard `logging` module.

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('VaultState')
logger.setLevel(logging.INFO)
```

Levels used:

- **DEBUG**: transitions, state changes, data access
- **INFO**: successful operations and state transitions
- **WARNING**: invalid transitions, missing data, validation warnings (non-strict mode)
- **ERROR**: validation errors, file errors

## API Reference

### Constructor

```python
VaultState(filename: str, strict_mode: bool = True)
```

- `filename`: path to the JSON configuration file
- `strict_mode`: if `True`, raises exceptions on validation errors; if `False`, logs warnings instead

Raises `FSMValidationError` on invalid configuration, `FileNotFoundError` if the file doesn't exist.

### State queries

```python
get_current_state() -> str
get_all_states() -> list[str]
get_state_history() -> list[str]
```

### Data access

```python
get_data() -> dict[str, Any]
```
Data for the current state, merged with global data.

```python
get_data_state(state: str | None = None) -> dict[str, Any]
```
Data for a specific state, or global data if `state=None`.

### Transitions

```python
event(event: str | None = None) -> bool
```
Processes an event and transitions if valid. Returns `True` if the state changed.

```python
get_possible_transitions() -> list[str]
is_valid_transition(event: str) -> bool
```

### Utility

```python
reset() -> None
```
Resets to the initial state and clears history.

```python
export_graph() -> dict[str, Any]
```
Returns:
```python
{
    "nodes": ["State1", "State2", ...],
    "edges": [{"from": "State1", "to": "State2", "label": "event1"}, ...],
    "initial": "State1"
}
```

### Signals

Two class-level signals, provided by `psygnal`:

```python
VaultState.automa_event          # trigger an event
VaultState.automa_state_changed  # fired on state change
```

```python
fsm.automa_state_changed.connect(lambda new_state: print(f"New state: {new_state}"))
fsm.automa_event.emit("init_ok")
```

> psygnal keeps only a `weakref` to connected bound methods. A bare bound
> method of a builtin type (e.g. `some_list.append`) is garbage-collected
> immediately after `connect()` returns, so the callback silently never
> fires. Connect a plain function, a lambda, or a bound method of a
> long-lived object instead (see `tests/test_vault_state.py` for examples).

## JSON Schema

```json
{
  "version": <float>,
  "initial": <string>,
  "data": {
    "<key>": <value>
  },
  "state": {
    "<state_name>": {
      "data": {
        "<key>": <value>
      },
      "transition": {
        "<event_name>": "<target_state>"
      }
    }
  }
}
```

`initial` and `state` are required; `version` and `data` are optional.

Validation rules:

- `state` must be present
- `initial` must be present and defined in `state`
- all transition targets must exist in `state`
- states and transitions must be dictionaries

## Error Handling

```python
from vault_state import VaultState, FSMValidationError

try:
    fsm = VaultState("my_fsm.json")
except FileNotFoundError as e:
    ...
except FSMValidationError as e:
    ...
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```

Tests live in `tests/test_vault_state.py` and cover validation (missing/invalid
fields, strict vs. non-strict mode), transitions, state history, data merging,
signals, and `export_graph()`.

`vault_state.py` also has a manual smoke test when run directly:

```bash
python vault_state.py
```

## Linting and Type Checking

```bash
ruff check .
mypy
```

Both are configured in `pyproject.toml` and run in CI (`.github/workflows/ci.yml`)
across Python 3.9–3.13, along with `pytest`.

## License

```
Copyright [2025] [ecki]
SPDX-License-Identifier: Apache-2.0
```
