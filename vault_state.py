# Copyright [2025] [ecki]
# SPDX-License-Identifier: Apache-2.0

"""
Improved Finite State Machine implementation with enhanced validation and error handling.
"""
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import PySignal

# Configure module logger
logger = logging.getLogger('VaultState')


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

        logger.info(f"Initializing FSM from {self.__filename}")

        self.__read_fsm_file()
        self.__validate_and_analyse_data()
        self.automa_event.connect(self.event)

        logger.info(f"FSM initialized successfully with initial state: {self.__current_state}")

    def __read_fsm_file(self) -> None:
        """
        Reads JSON from file and saves data as dict.

        Raises:
            FileNotFoundError: If file doesn't exist
            FSMValidationError: If JSON is invalid
        """
        if not self.__filename.exists():
            error_msg = f"FSM file not found: {self.__filename}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(self.__filename, 'r', encoding='utf-8') as file:
                self.__data = json.load(file)
            logger.debug(f"Successfully loaded JSON from {self.__filename}")
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {self.__filename}: {e}"
            logger.error(error_msg)
            raise FSMValidationError(error_msg)
        except IOError as e:
            error_msg = f"Error reading file {self.__filename}: {e}"
            logger.error(error_msg)
            raise FSMValidationError(error_msg)

    def __validate_and_analyse_data(self) -> None:
        """
        Validates FSM structure and builds transition dictionary.

        Raises:
            FSMValidationError: If FSM structure is invalid
        """
        logger.debug("Starting FSM validation")

        # Check required fields
        if "state" not in self.__data:
            error_msg = "Missing 'state' field in FSM configuration"
            logger.error(error_msg)
            raise FSMValidationError(error_msg)

        if "initial" not in self.__data:
            error_msg = "Missing 'initial' field in FSM configuration"
            logger.error(error_msg)
            raise FSMValidationError(error_msg)

        initial_state = self.__data.get("initial", "")
        states = self.__data.get("state", {})

        # Validate initial state exists
        if initial_state not in states:
            error_msg = f"Initial state '{initial_state}' not found in state definitions"
            logger.error(error_msg)
            raise FSMValidationError(error_msg)

        # Build transition dictionary
        transition_count = 0
        for state, value in states.items():
            if not isinstance(value, dict):
                error_msg = f"State '{state}' must be a dictionary"
                logger.error(error_msg)
                raise FSMValidationError(error_msg)

            transitions = value.get("transition", {})
            if not isinstance(transitions, dict):
                error_msg = f"Transitions for state '{state}' must be a dictionary"
                logger.error(error_msg)
                raise FSMValidationError(error_msg)

            for event, target_state in transitions.items():
                # Validate target state exists
                if target_state not in states:
                    msg = f"Target state '{target_state}' for event '{event}' in state '{state}' doesn't exist"
                    if self.__strict_mode:
                        logger.error(msg)
                        raise FSMValidationError(msg)
                    else:
                        logger.warning(msg)

                self.__transition_dict[(state, event)] = target_state
                transition_count += 1
                logger.debug(f"Added transition: {state} --[{event}]--> {target_state}")

        self.__current_state = initial_state
        self.__state_history.append(initial_state)

        logger.info(f"Validation complete: {len(states)} states, {transition_count} transitions")

    def get_current_state(self) -> str:
        """Returns the current state name."""
        logger.debug(f"Current state queried: {self.__current_state}")
        return self.__current_state

    def get_state_history(self) -> List[str]:
        """Returns the history of state transitions."""
        logger.debug(f"State history queried: {len(self.__state_history)} states")
        return self.__state_history.copy()

    def get_data(self) -> Dict[str, Any]:
        """Returns data for the current state merged with global data."""
        global_data = self.__data.get("data", {})
        state_data = self.get_data_state(self.__current_state)

        # Merge global and state-specific data (state data takes precedence)
        merged_data = {**global_data, **state_data}
        logger.debug(f"Data for state '{self.__current_state}': {len(merged_data)} keys")
        return merged_data

    def get_data_state(self, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns data for a specific state or global data.

        Args:
            state: State name, or None for global data

        Returns:
            Dictionary with state-specific or global data
        """
        if state is None:
            data = self.__data.get("data", {})
            logger.debug(f"Global data queried: {len(data)} keys")
            return data

        data = self.__data.get("state", {}).get(state, {}).get("data", {})
        logger.debug(f"Data for state '{state}': {len(data)} keys")
        return data

    def event(self, event: Optional[str] = None) -> bool:
        """
        Process an event and transition to new state if possible.

        Args:
            event: Event name to process

        Returns:
            True if state changed, False otherwise
        """
        if event is None:
            logger.warning("event() called with None")
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
            logger.info(f"Event '{event}' triggered: {old_state} -> {new_state}")
            self.automa_state_changed.emit(self.__current_state)
            return True
        else:
            # Log invalid transition attempt
            if (old_state, event) not in self.__transition_dict:
                logger.warning(f"No transition for event '{event}' in state '{old_state}'")
            else:
                logger.debug(f"Event '{event}' triggered but state unchanged: {old_state}")
            return False

    def get_possible_transitions(self) -> List[str]:
        """
        Returns list of valid events for the current state.

        Returns:
            List of event names that can be triggered from current state
        """
        transitions = [
            event for state, event in self.__transition_dict.keys()
            if state == self.__current_state
        ]
        logger.debug(f"Possible transitions from '{self.__current_state}': {transitions}")
        return transitions

    def is_valid_transition(self, event: str) -> bool:
        """
        Check if an event is valid for the current state.

        Args:
            event: Event name to check

        Returns:
            True if transition exists, False otherwise
        """
        is_valid = (self.__current_state, event) in self.__transition_dict
        logger.debug(f"Transition validation for '{event}' in '{self.__current_state}': {is_valid}")
        return is_valid

    def reset(self) -> None:
        """Reset FSM to initial state and clear history."""
        initial_state = self.__data.get("initial", "")
        logger.info(f"Resetting FSM to initial state: {initial_state}")
        self.__current_state = initial_state
        self.__state_history = [self.__current_state]
        self.automa_state_changed.emit(self.__current_state)

    def get_all_states(self) -> List[str]:
        """Returns list of all defined states."""
        states = list(self.__data.get("state", {}).keys())
        logger.debug(f"All states queried: {len(states)} states")
        return states

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

        graph = {
            "nodes": nodes,
            "edges": edges,
            "initial": self.__data.get("initial", "")
        }

        logger.debug(f"Graph exported: {len(nodes)} nodes, {len(edges)} edges")
        return graph


def test_state_changed_signal(new_state: str) -> None:
    """Callback for state change signal."""
    print(f"✓ State changed to: {new_state}")


if __name__ == '__main__':
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test the improved FSM
    print("=== Testing Improved VaultState FSM ===\n")

    json_file = "example_fsm.json"

    try:
        fsm = VaultState(json_file)
        fsm.automa_state_changed.connect(test_state_changed_signal)

        print(f"\nInitial state: {fsm.get_current_state()}")
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
        logger.error(f"Failed to initialize FSM: {e}")
        print(f"Error: {e}")
