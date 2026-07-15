import json
from pathlib import Path

import pytest

from vault_state import FSMValidationError, VaultState

EXAMPLE_FSM_PATH = Path(__file__).parent.parent / "example_fsm.json"

VALID_FSM = {
    "version": 0.1,
    "initial": "idle",
    "data": {
        "origin": "0,0",
        "shared": "global",
    },
    "state": {
        "idle": {
            "transition": {"start": "running"},
        },
        "running": {
            "data": {"shared": "override", "speed": 5},
            "transition": {"stop": "idle", "finish": "done"},
        },
        "done": {
            "data": {},
            "transition": {},
        },
    },
}


def write_fsm(tmp_path, data):
    path = tmp_path / "fsm.json"
    path.write_text(json.dumps(data))
    return str(path)


@pytest.fixture
def fsm_path(tmp_path):
    return write_fsm(tmp_path, VALID_FSM)


@pytest.fixture
def fsm(fsm_path):
    return VaultState(fsm_path)


class TestValidation:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VaultState(str(tmp_path / "does_not_exist.json"))

    def test_invalid_json_raises_fsm_validation_error(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{not valid json")
        with pytest.raises(FSMValidationError):
            VaultState(str(path))

    def test_missing_state_field_raises(self, tmp_path):
        path = write_fsm(tmp_path, {"initial": "idle"})
        with pytest.raises(FSMValidationError, match="state"):
            VaultState(path)

    def test_missing_initial_field_raises(self, tmp_path):
        path = write_fsm(tmp_path, {"state": {"idle": {}}})
        with pytest.raises(FSMValidationError, match="initial"):
            VaultState(path)

    def test_unknown_initial_state_raises(self, tmp_path):
        path = write_fsm(tmp_path, {"initial": "missing", "state": {"idle": {}}})
        with pytest.raises(FSMValidationError, match="Initial state"):
            VaultState(path)

    def test_state_not_a_dict_raises(self, tmp_path):
        path = write_fsm(tmp_path, {"initial": "idle", "state": {"idle": "not-a-dict"}})
        with pytest.raises(FSMValidationError, match="dictionary"):
            VaultState(path)

    def test_transitions_not_a_dict_raises(self, tmp_path):
        path = write_fsm(
            tmp_path,
            {"initial": "idle", "state": {"idle": {"transition": "not-a-dict"}}},
        )
        with pytest.raises(FSMValidationError, match="dictionary"):
            VaultState(path)

    def test_unknown_target_state_raises_in_strict_mode(self, tmp_path):
        path = write_fsm(
            tmp_path,
            {
                "initial": "idle",
                "state": {"idle": {"transition": {"go": "nowhere"}}},
            },
        )
        with pytest.raises(FSMValidationError, match="nowhere"):
            VaultState(path, strict_mode=True)

    def test_unknown_target_state_only_warns_in_non_strict_mode(self, tmp_path, caplog):
        path = write_fsm(
            tmp_path,
            {
                "initial": "idle",
                "state": {"idle": {"transition": {"go": "nowhere"}}},
            },
        )
        fsm = VaultState(path, strict_mode=False)
        assert fsm.get_current_state() == "idle"


class TestStateAndTransitions:
    def test_initial_state(self, fsm):
        assert fsm.get_current_state() == "idle"
        assert fsm.get_state_history() == ["idle"]

    def test_valid_transition_changes_state_and_history(self, fsm):
        changed = fsm.event("start")
        assert changed is True
        assert fsm.get_current_state() == "running"
        assert fsm.get_state_history() == ["idle", "running"]

    def test_invalid_event_is_a_no_op(self, fsm):
        changed = fsm.event("nope")
        assert changed is False
        assert fsm.get_current_state() == "idle"
        assert fsm.get_state_history() == ["idle"]

    def test_event_none_is_a_no_op(self, fsm):
        assert fsm.event(None) is False
        assert fsm.get_current_state() == "idle"

    def test_get_possible_transitions(self, fsm):
        assert sorted(fsm.get_possible_transitions()) == ["start"]
        fsm.event("start")
        assert sorted(fsm.get_possible_transitions()) == ["finish", "stop"]

    def test_is_valid_transition(self, fsm):
        assert fsm.is_valid_transition("start") is True
        assert fsm.is_valid_transition("finish") is False

    def test_get_all_states(self, fsm):
        assert sorted(fsm.get_all_states()) == ["done", "idle", "running"]

    def test_reset_restores_initial_state_and_clears_history(self, fsm):
        fsm.event("start")
        fsm.event("finish")
        fsm.reset()
        assert fsm.get_current_state() == "idle"
        assert fsm.get_state_history() == ["idle"]


class TestData:
    def test_global_data_at_initial_state(self, fsm):
        assert fsm.get_data() == {"origin": "0,0", "shared": "global"}

    def test_state_data_overrides_global_data(self, fsm):
        fsm.event("start")
        assert fsm.get_data() == {"origin": "0,0", "shared": "override", "speed": 5}

    def test_get_data_state_global(self, fsm):
        assert fsm.get_data_state(None) == {"origin": "0,0", "shared": "global"}

    def test_get_data_state_specific(self, fsm):
        assert fsm.get_data_state("running") == {"shared": "override", "speed": 5}

    def test_get_data_state_unknown_state_returns_empty(self, fsm):
        assert fsm.get_data_state("nope") == {}


class TestGraphExport:
    def test_export_graph_structure(self, fsm):
        graph = fsm.export_graph()
        assert graph["initial"] == "idle"
        assert sorted(graph["nodes"]) == ["done", "idle", "running"]
        assert {"from": "idle", "to": "running", "label": "start"} in graph["edges"]
        assert {"from": "running", "to": "idle", "label": "stop"} in graph["edges"]
        assert {"from": "running", "to": "done", "label": "finish"} in graph["edges"]


class TestSignals:
    def test_automa_event_emit_triggers_transition(self, fsm):
        fsm.automa_event.emit("start")
        assert fsm.get_current_state() == "running"

    def test_automa_state_changed_emits_on_transition(self, fsm):
        # PySignal keeps only a weakref to connected slots, so a bare bound
        # method like `seen.append` is garbage-collected immediately; a
        # lambda is kept alive strongly by the signal's internal slot list.
        seen = []
        fsm.automa_state_changed.connect(lambda state: seen.append(state))
        fsm.event("start")
        assert seen == ["running"]

    def test_automa_state_changed_not_emitted_on_no_op(self, fsm):
        seen = []
        fsm.automa_state_changed.connect(lambda state: seen.append(state))
        fsm.event("nope")
        assert seen == []

    def test_automa_state_changed_emitted_on_reset(self, fsm):
        fsm.event("start")
        seen = []
        fsm.automa_state_changed.connect(lambda state: seen.append(state))
        fsm.reset()
        assert seen == ["idle"]

    def test_signals_are_independent_per_instance(self, fsm_path):
        fsm_a = VaultState(fsm_path)
        fsm_b = VaultState(fsm_path)
        seen_a = []
        fsm_a.automa_state_changed.connect(lambda state: seen_a.append(state))
        fsm_b.event("start")
        assert seen_a == []


class TestExampleFsm:
    def test_shipped_example_fsm_loads_and_runs(self):
        fsm = VaultState(str(EXAMPLE_FSM_PATH))
        assert fsm.get_current_state() == "Superstate"
        fsm.event("init_ok")
        assert fsm.get_current_state() == "mp_init_01"
