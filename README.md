# VaultState - Finite State Machine

A robust, JSON-based Finite State Machine (FSM) implementation in Python with signal support, comprehensive validation, and logging capabilities.

## Features

- 📄 **JSON-based Configuration** - Easy definition of states and transitions
- 🔔 **Signal System** - Event-based communication via PySignal
- ✅ **Comprehensive Validation** - FSM structure validation on load
- 📊 **State History** - Tracking of all state transitions
- 🎨 **Graph Export** - Export for visualization
- 🔍 **Type Hints** - Full type annotations
- ⚡ **Strict/Non-Strict Mode** - Flexible error handling
- 📝 **Logging Support** - Configurable logging with multiple levels

## Installation

```bash
pip install .
```

For development (adds `pytest` and `ruff`):

```bash
pip install -e ".[dev]"
```

Dependencies are declared in `pyproject.toml` (currently just `PySignal>=1.1.1`).

## Quick Start

### 1. Create FSM Configuration

Create a JSON file (e.g., `example_fsm.json`):

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

# Optional: Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FSM
fsm = VaultState("example_fsm.json")

# Query current state
print(fsm.get_current_state())  # "Superstate"

# Get current state data
print(fsm.get_data())

# Get possible transitions
print(fsm.get_possible_transitions())  # ["init_ok"]

# Trigger event
fsm.event("init_ok")
print(fsm.get_current_state())  # "mp_init_01"
```

## Logging Configuration

VaultState uses Python's built-in logging module. Configure logging levels to control verbosity:

```python
import logging

# Set logging level for VaultState
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or configure specific logger
logger = logging.getLogger('VaultState')
logger.setLevel(logging.INFO)
```

### Logging Levels

- **DEBUG**: Detailed information about transitions, state changes, and data access
- **INFO**: Confirmation of successful operations and state transitions
- **WARNING**: Invalid transitions, missing data, validation warnings (non-strict mode)
- **ERROR**: Validation errors, file errors
- **CRITICAL**: Not used by VaultState

### Example Log Output

```
2026-07-15 18:52:29,703 - VaultState - INFO - Initializing FSM from example_fsm.json
2026-07-15 18:52:29,703 - VaultState - INFO - Validation complete: 4 states, 5 transitions
2026-07-15 18:52:29,704 - VaultState - INFO - FSM initialized successfully with initial state: Superstate
2026-07-15 18:52:29,704 - VaultState - INFO - Event 'init_ok' triggered: Superstate -> mp_init_01
2026-07-15 18:52:29,704 - VaultState - WARNING - No transition for event 'invalid_event' in state 'mp_init_01'
```

## API Reference

### Constructor

```python
VaultState(filename: str, strict_mode: bool = True)
```

- `filename`: Path to JSON configuration file
- `strict_mode`: If `True`, raises exceptions on validation errors

**Raises:**
- `FSMValidationError`: On invalid FSM configuration
- `FileNotFoundError`: If configuration file doesn't exist

### Methods

#### State Queries

```python
get_current_state() -> str
```
Returns the name of the current state.

```python
get_all_states() -> list[str]
```
Returns a list of all defined states.

```python
get_state_history() -> list[str]
```
Returns the history of all traversed states.

#### Data Access

```python
get_data() -> dict[str, Any]
```
Returns data for the current state (merged with global data).

```python
get_data_state(state: str | None = None) -> dict[str, Any]
```
Returns data for a specific state. Returns global data if `state=None`.

#### Transitions

```python
event(event: str | None = None) -> bool
```
Processes an event and performs a transition if valid.

**Returns:** `True` if state changed, `False` otherwise.

```python
get_possible_transitions() -> list[str]
```
Returns a list of all valid events for the current state.

```python
is_valid_transition(event: str) -> bool
```
Checks if an event is valid in the current state.

#### Utility

```python
reset() -> None
```
Resets the FSM to the initial state and clears history.

```python
export_graph() -> dict[str, Any]
```
Exports the FSM structure for visualization.

**Returns:**
```python
{
    "nodes": ["State1", "State2", ...],
    "edges": [
        {"from": "State1", "to": "State2", "label": "event1"},
        ...
    ],
    "initial": "State1"
}
```

### Signals

VaultState provides two class signals:

```python
VaultState.automa_event
```
Signal for triggering events. Connect your event source:

```python
fsm.automa_event.connect(lambda event: fsm.event(event))
# Or use the automatic connection in constructor
```

```python
VaultState.automa_state_changed
```
Signal fired on state changes:

```python
def on_state_changed(new_state: str):
    print(f"New state: {new_state}")

fsm.automa_state_changed.connect(on_state_changed)
```

> **Note:** PySignal keeps only a `weakref` to connected slots. A bare bound
> method of a builtin type (e.g. `some_list.append`) is garbage-collected
> immediately after `connect()` returns, so the callback silently never
> fires. Connect a plain function, a lambda, or a bound method of a
> long-lived object instead (see the tests in `tests/test_vault_state.py`
> for examples).

## Advanced Examples

### With Signal Callbacks and Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def on_state_change(new_state: str):
    logging.info(f"✓ State changed to: {new_state}")
    
    # Automatic actions based on state
    if new_state == "mp_end_03":
        logging.info("Mission completed!")

fsm = VaultState("example_fsm.json")
fsm.automa_state_changed.connect(on_state_change)

# Trigger events
fsm.automa_event.emit("init_ok")
fsm.automa_event.emit("start")
```

### Non-Strict Mode

```python
# Warnings instead of exceptions on validation errors
fsm = VaultState("example_fsm.json", strict_mode=False)
```

### State History Tracking

```python
fsm.event("init_ok")
fsm.event("start")
fsm.event("formation_ok")

history = fsm.get_state_history()
print(" → ".join(history))
# Output: Superstate → mp_init_01 → mp_change_02 → mp_end_03
```

### Validation Before Event Execution

```python
import logging

event = "start"

if fsm.is_valid_transition(event):
    fsm.event(event)
else:
    logging.warning(f"Event '{event}' is not valid in current state")
    logging.info(f"Valid events: {fsm.get_possible_transitions()}")
```

### Graph Visualization Preparation

```python
import json

graph_data = fsm.export_graph()
print(json.dumps(graph_data, indent=2))

# Can be visualized with Graphviz, D3.js, or Cytoscape.js
```

### Custom Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Create custom logger
logger = logging.getLogger('VaultState')
logger.setLevel(logging.DEBUG)

# File handler with rotation
file_handler = RotatingFileHandler(
    'fsm.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Now initialize FSM
fsm = VaultState("example_fsm.json")
```

## JSON Schema

The FSM configuration must have the following structure:

```json
{
  "version": <float>,           // Optional: Version number
  "initial": <string>,          // Required: Name of initial state
  "data": {                     // Optional: Global data
    "<key>": <value>
  },
  "state": {                    // Required: State definitions
    "<state_name>": {
      "data": {                 // Optional: State-specific data
        "<key>": <value>
      },
      "transition": {           // Optional: Transitions
        "<event_name>": "<target_state>"
      }
    }
  }
}
```

### Validation Rules

- ✅ Field `state` is required
- ✅ Field `initial` is required
- ✅ The initial state must be defined in `state`
- ✅ All target states in transitions must exist
- ✅ States and transitions must be dictionaries

## Error Handling

```python
from vault_state import VaultState, FSMValidationError
import logging

logging.basicConfig(level=logging.INFO)

try:
    fsm = VaultState("my_fsm.json")
except FileNotFoundError as e:
    logging.error(f"File not found: {e}")
except FSMValidationError as e:
    logging.error(f"Invalid FSM configuration: {e}")
```

## Best Practices

1. **Naming Convention**: Use descriptive state and event names
2. **End States**: Define explicit end states with empty transitions
3. **Global Data**: Use global data for constant values
4. **State Data**: Use state-specific data for variable values
5. **Validation**: Use `is_valid_transition()` before critical events
6. **History**: Use `get_state_history()` for debugging and logging
7. **Logging**: Configure appropriate log levels for production vs development
8. **Error Handling**: Always catch FSMValidationError and FileNotFoundError

## Testing

The test suite uses `pytest` and lives in `tests/test_vault_state.py`:

```bash
pip install -e ".[dev]"
pytest
```

It covers validation (missing/invalid fields, strict vs. non-strict mode),
transitions, state history, data merging, signals, and `export_graph()`.

The module also contains a manual smoke test:

```bash
python vault_state.py
```

Output:
```
=== Testing Improved VaultState FSM ===

Initial state: Superstate
Global + state data: {...}
Possible transitions: ['init_ok']

→ Emitting 'init_ok' event:
✓ State changed to: mp_init_01
Current state: mp_init_01
...
```

## Linting

The project uses `ruff`, configured in `pyproject.toml`:

```bash
ruff check .
```

## License

```
Copyright [2025] [ecki]
SPDX-License-Identifier: Apache-2.0
```

## Support

For questions or issues, please create an issue in the repository.

## Changelog

### Unreleased
- 🐛 Bug fix: removed invalid `"event": "target"` transition from `example_fsm.json` that broke strict-mode validation
- ✅ Added `pytest` test suite (`tests/test_vault_state.py`)
- 📦 Added `pyproject.toml` packaging (installable via `pip install .`)
- 🧹 Linted codebase with `ruff`; modernized type hints (`dict`/`list`/`X | None`)

### Version 1.0 (2025)
- ✨ Initial release with comprehensive validation
- ✨ Type hints and extensive documentation
- ✨ State history tracking
- ✨ Graph export functionality
- ✨ Strict/Non-strict mode
- ✨ Integrated logging support
- 🐛 Bug fix: String comparison instead of identity comparison
- 🐛 Bug fix: Improved exception handling
