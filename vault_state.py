# Copyright [2025] [ecki]
# SPDX-License-Identifier: Apache-2.0

"""
Improved Finite State Machine implementation with enhanced validation and error handling.
"""
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import PySignal


class FSMValidationError(Exception):
    """Custom exception for FSM validation errors."""
    pass


class VaultState:
    """
    Finite State Machine implementation based on JSON configuration.

    Supports state transitions via events and provides signals for state changes.
    """

    automa_event = PySignal.ClassSignal()
    automa_state_changed = PySignal.ClassSignal()

    def __init__(self, filename: str, strict_mode: bool = True):
        """
        Initialize the FSM from a JSON file.

        Args:
            filename: Path to the FSM JSON configuration file
            strict_mode: If True, raises exceptions on validation errors

        Raises:
            FSMValidationError: If the FSM configuration is invalid
            FileNotFoundError: If the configuration file doesn't exist
        """
        self.__filename = Path(filename)
        self.__strict_mode = strict_mode
        self.__transition_dict: Dict[Tuple[str, str], str] = {}
        self.__current_state: Optional[str] = None
        self.__data: Dict[str, Any] = {}
        self.__state_history: List[str] = []

        self.__read_fsm_file()
        self.__validate_and_analyse_data()
        self.automa_event.connect(self.event)

    def __read_fsm_file(self) -> None:
        """
        Reads JSON from file and saves data as dict.

        Raises:
            FileNotFoundError: If file doesn't exist
            FSMValidationError: If JSON is invalid
        """
        if not self.__filename.exists():
            raise FileNotFoundError(f"FSM file not found: {self.__filename}")

        try:
            with open(self.__filename, 'r', encoding='utf-8') as file:
                self.__data = json.load(file)
        except json.JSONDecodeError as e:
            raise FSMValidationError(f"Invalid JSON in {self.__filename}: {e}")
        except IOError as e:
            raise FSMValidationError(f"Error reading file {self.__filename}: {e}")

    def __validate_and_analyse_data(self) -> None:
        """
        Validates FSM structure and builds transition dictionary.

        Raises:
            FSMValidationError: If FSM structure is invalid
        """
        # Check required fields
        if "state" not in self.__data:
            raise FSMValidationError("Missing 'state' field in FSM configuration")

        if "initial" not in self.__data:
            raise FSMValidationError("Missing 'initial' field in FSM configuration")

        initial_state = self.__data.get("initial", "")
        states = self.__data.get("state", {})

        # Validate initial state exists
        if initial_state not in states:
            raise FSMValidationError(
                f"Initial state '{initial_state}' not found in state definitions"
            )

        # Build transition dictionary
        for state, value in states.items():
            if not isinstance(value, dict):
                raise FSMValidationError(f"State '{state}' must be a dictionary")

            transitions = value.get("transition", {})
            if not isinstance(transitions, dict):
                raise FSMValidationError(
                    f"Transitions for state '{state}' must be a dictionary"
                )

            for event, target_state in transitions.items():
                # Validate target state exists
                if target_state not in states:
                    msg = f"Target state '{target_state}' for event '{event}' in state '{state}' doesn't exist"
                    if self.__strict_mode:
                        raise FSMValidationError(msg)
                    else:
                        print(f"Warning: {msg}")

                self.__transition_dict[(state, event)] = target_state

        self.__current_state = initial_state
        self.__state_history.append(initial_state)

    def get_current_state(self) -> str:
        """Returns the current state name."""
        return self.__current_state

    def get_state_history(self) -> List[str]:
        """Returns the history of state transitions."""
        return self.__state_history.copy()

    def get_data(self) -> Dict[str, Any]:
        """Returns data for the current state merged with global data."""
        global_data = self.__data.get("data", {})
        state_data = self.get_data_state(self.__current_state)

        # Merge global and state-specific data (state data takes precedence)
        return {**global_data, **state_data}

    def get_data_state(self, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns data for a specific state or global data.

        Args:
            state: State name, or None for global data

        Returns:
            Dictionary with state-specific or global data
        """
        if state is None:
            return self.__data.get("data", {})

        return self.__data.get("state", {}).get(state, {}).get("data", {})

    def event(self, event: Optional[str] = None) -> bool:
        """
        Process an event and transition to new state if possible.

        Args:
            event: Event name to process

        Returns:
            True if state changed, False otherwise
        """
        if event is None:
            print("Warning: event() called with None")
            return False

        old_state = self.__current_state
        new_state = self.__transition_dict.get(
            (self.__current_state, event),
            self.__current_state
        )

        # Use equality comparison, not identity
        if old_state != new_state:
            self.__current_state = new_state
            self.__state_history.append(new_state)
            self.automa_state_changed.emit(self.__current_state)
            return True
        else:
            # Log invalid transition attempt
            if (old_state, event) not in self.__transition_dict:
                print(f"Warning: No transition for event '{event}' in state '{old_state}'")
            return False

    def get_possible_transitions(self) -> List[str]:
        """
        Returns list of valid events for the current state.

        Returns:
            List of event names that can be triggered from current state
        """
        return [
            event for state, event in self.__transition_dict.keys()
            if state == self.__current_state
        ]

    def is_valid_transition(self, event: str) -> bool:
        """
        Check if an event is valid for the current state.

        Args:
            event: Event name to check

        Returns:
            True if transition exists, False otherwise
        """
        return (self.__current_state, event) in self.__transition_dict

    def reset(self) -> None:
        """Reset FSM to initial state and clear history."""
        self.__current_state = self.__data.get("initial", "")
        self.__state_history = [self.__current_state]
        self.automa_state_changed.emit(self.__current_state)

    def get_all_states(self) -> List[str]:
        """Returns list of all defined states."""
        return list(self.__data.get("state", {}).keys())

    def export_graph(self) -> Dict[str, Any]:
        """
        Export FSM structure for visualization.

        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        nodes = self.get_all_states()
        edges = [
            {"from": state, "to": target, "label": event}
            for (state, event), target in self.__transition_dict.items()
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "initial": self.__data.get("initial", "")
        }


def test_state_changed_signal(new_state: str) -> None:
    """Callback for state change signal."""
    print(f"✓ State changed to: {new_state}")


if __name__ == '__main__':
    # Test the improved FSM
    print("=== Testing Improved VaultState FSM ===\n")

    json_file = "example_fsm.json"

    try:
        fsm = VaultState(json_file)
        fsm.automa_state_changed.connect(test_state_changed_signal)

        print(f"Initial state: {fsm.get_current_state()}")
        print(f"Global + state data: {fsm.get_data()}")
        print(f"Possible transitions: {fsm.get_possible_transitions()}\n")

        # Test valid transition
        print("→ Emitting 'init_ok' event:")
        success = fsm.automa_event.emit("init_ok")
        print(f"Current state: {fsm.get_current_state()}")
        print(f"State data: {fsm.get_data()}")
        print(f"Possible transitions: {fsm.get_possible_transitions()}\n")

        # Test another transition
        print("→ Emitting 'start' event:")
        fsm.event("start")
        print(f"Current state: {fsm.get_current_state()}")
        print(f"State data: {fsm.get_data()}")
        print(f"Possible transitions: {fsm.get_possible_transitions()}\n")

        # Test invalid transition
        print("→ Attempting invalid 'invalid_event':")
        fsm.event("invalid_event")
        print()

        # Show history
        print(f"State history: {' → '.join(fsm.get_state_history())}")

        # Export graph
        print(f"\nGraph structure: {json.dumps(fsm.export_graph(), indent=2)}")

    except (FSMValidationError, FileNotFoundError) as e:
        print(f"Error: {e}")
