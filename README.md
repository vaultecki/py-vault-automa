# VaultState - Finite State Machine

Eine robuste, JSON-basierte Finite State Machine (FSM) Implementierung in Python mit Signal-Support und umfangreicher Validierung.

## Features

- 📄 **JSON-basierte Konfiguration** - Einfache Definition von States und Transitionen
- 🔔 **Signal-System** - Event-basierte Kommunikation via PySignal
- ✅ **Umfangreiche Validierung** - Prüfung der FSM-Struktur beim Laden
- 📊 **State History** - Tracking aller Zustandsübergänge
- 🎨 **Graph Export** - Export für Visualisierung
- 🔍 **Type Hints** - Vollständige Typ-Annotationen
- ⚡ **Strict/Non-Strict Mode** - Flexible Fehlerbehandlung

## Installation

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
PySignal>=1.1.1
```

## Schnellstart

### 1. FSM-Konfiguration erstellen

Erstellen Sie eine JSON-Datei (z.B. `example_fsm.json`):

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
        "event": "target",
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

### 2. FSM verwenden

```python
from vault_state import VaultState

# FSM initialisieren
fsm = VaultState("example_fsm.json")

# Aktuellen State abfragen
print(fsm.get_current_state())  # "Superstate"

# Daten des aktuellen States
print(fsm.get_data())

# Mögliche Transitionen
print(fsm.get_possible_transitions())  # ["init_ok"]

# Event auslösen
fsm.event("init_ok")
print(fsm.get_current_state())  # "mp_init_01"
```

## API-Referenz

### Konstruktor

```python
VaultState(filename: str, strict_mode: bool = True)
```

- `filename`: Pfad zur JSON-Konfigurationsdatei
- `strict_mode`: Wenn `True`, wirft Exceptions bei Validierungsfehlern

**Raises:**
- `FSMValidationError`: Bei ungültiger FSM-Konfiguration
- `FileNotFoundError`: Wenn die Datei nicht existiert

### Methoden

#### State-Abfrage

```python
get_current_state() -> str
```
Gibt den Namen des aktuellen States zurück.

```python
get_all_states() -> List[str]
```
Gibt eine Liste aller definierten States zurück.

```python
get_state_history() -> List[str]
```
Gibt die Historie aller durchlaufenen States zurück.

#### Daten-Zugriff

```python
get_data() -> Dict[str, Any]
```
Gibt die Daten des aktuellen States zurück (merged mit globalen Daten).

```python
get_data_state(state: Optional[str] = None) -> Dict[str, Any]
```
Gibt Daten für einen spezifischen State zurück. Bei `state=None` werden globale Daten zurückgegeben.

#### Transitionen

```python
event(event: Optional[str] = None) -> bool
```
Verarbeitet ein Event und führt ggf. eine Transition durch.

**Returns:** `True` wenn State gewechselt wurde, `False` sonst.

```python
get_possible_transitions() -> List[str]
```
Gibt eine Liste aller gültigen Events für den aktuellen State zurück.

```python
is_valid_transition(event: str) -> bool
```
Prüft, ob ein Event im aktuellen State gültig ist.

#### Utility

```python
reset() -> None
```
Setzt die FSM zum initialen State zurück und löscht die History.

```python
export_graph() -> Dict[str, Any]
```
Exportiert die FSM-Struktur für Visualisierung.

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

VaultState bietet zwei Class-Signals:

```python
VaultState.automa_event
```
Signal zum Auslösen von Events. Verbinden Sie Ihre Event-Quelle:

```python
fsm.automa_event.connect(lambda event: fsm.event(event))
# Oder nutzen Sie die automatische Verbindung im Constructor
```

```python
VaultState.automa_state_changed
```
Signal das bei State-Wechseln gefeuert wird:

```python
def on_state_changed(new_state: str):
    print(f"Neuer State: {new_state}")

fsm.automa_state_changed.connect(on_state_changed)
```

## Erweiterte Beispiele

### Mit Signal-Callbacks

```python
def on_state_change(new_state: str):
    print(f"✓ State gewechselt zu: {new_state}")
    
    # Automatische Aktionen basierend auf State
    if new_state == "mp_end_03":
        print("Mission beendet!")

fsm = VaultState("example_fsm.json")
fsm.automa_state_changed.connect(on_state_change)

# Events auslösen
fsm.automa_event.emit("init_ok")
fsm.automa_event.emit("start")
```

### Non-Strict Mode

```python
# Warnungen statt Exceptions bei Validierungsfehlern
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

### Validierung vor Event-Ausführung

```python
event = "start"

if fsm.is_valid_transition(event):
    fsm.event(event)
else:
    print(f"Event '{event}' ist im aktuellen State nicht gültig")
    print(f"Gültige Events: {fsm.get_possible_transitions()}")
```

### Graph-Visualisierung vorbereiten

```python
import json

graph_data = fsm.export_graph()
print(json.dumps(graph_data, indent=2))

# Kann z.B. mit Graphviz, D3.js oder Cytoscape.js visualisiert werden
```

## JSON-Schema

Die FSM-Konfiguration muss folgende Struktur haben:

```json
{
  "version": <float>,           // Optional: Versionsnummer
  "initial": <string>,          // Pflicht: Name des initialen States
  "data": {                     // Optional: Globale Daten
    "<key>": <value>
  },
  "state": {                    // Pflicht: State-Definitionen
    "<state_name>": {
      "data": {                 // Optional: State-spezifische Daten
        "<key>": <value>
      },
      "transition": {           // Optional: Transitionen
        "<event_name>": "<target_state>"
      }
    }
  }
}
```

### Validierungsregeln

- ✅ Feld `state` ist erforderlich
- ✅ Feld `initial` ist erforderlich
- ✅ Der initiale State muss in `state` definiert sein
- ✅ Alle Ziel-States in Transitionen müssen existieren
- ✅ States und Transitionen müssen Dictionaries sein

## Error Handling

```python
from vault_state import VaultState, FSMValidationError

try:
    fsm = VaultState("my_fsm.json")
except FileNotFoundError as e:
    print(f"Datei nicht gefunden: {e}")
except FSMValidationError as e:
    print(f"Ungültige FSM-Konfiguration: {e}")
```

## Best Practices

1. **Naming Convention**: Verwenden Sie aussagekräftige State- und Event-Namen
2. **End States**: Definieren Sie explizite End-States mit leeren Transitionen
3. **Global Data**: Nutzen Sie globale Daten für konstante Werte
4. **State Data**: Nutzen Sie state-spezifische Daten für variable Werte
5. **Validation**: Verwenden Sie `is_valid_transition()` vor kritischen Events
6. **History**: Nutzen Sie `get_state_history()` für Debugging und Logging

## Testing

Das Modul enthält einen eingebauten Test:

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

## Lizenz

```
Copyright [2025] [ecki]
SPDX-License-Identifier: Apache-2.0
```

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im Repository.

## Changelog

### Version 1.0 (2025)
- ✨ Initiales Release mit vollständiger Validierung
- ✨ Type Hints und umfangreiche Dokumentation
- ✨ State History Tracking
- ✨ Graph Export Funktionalität
- ✨ Strict/Non-Strict Mode
- 🐛 Bug-Fix: String-Vergleich statt Identitäts-Vergleich
- 🐛 Bug-Fix: Verbessertes Exception Handling
