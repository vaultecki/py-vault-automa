import json
import PySignal


class VaultState:
    automa_event = PySignal.ClassSignal()
    automa_state_changed = PySignal.ClassSignal()

    def __init__(self, filename):
        self.__filename = filename
        self.__transition_dict = {}
        self.__current_state = None
        self.__data = {}
        if not self.__read_fsm_file():
            raise ValueError("no file or broken json inside")
        # print(self.data)
        self.__analyse_data()
        # print(self.transition_dict)
        self.automa_event.connect(self.event)

    def __read_fsm_file(self):
        """reads json from self filename and saves data as dict

            return: if error occurred
            rtype: bool
        """
        try:
            with open(file=self.__filename, mode='r') as file:
                self.__data = json.load(file)
        except Exception as e:
            print("Oops Error: {}".format(e))
            self.__data = {}
            return False
        return True

    def __analyse_data(self):
        for state, value in self.__data.get("state", {}).items():
            # print("State: {} -- Value: {}".format(state, value))
            for transition, new_state in value.get("transition", {}).items():
                self.__transition_dict.update({(state, transition): new_state})
        if self.__data.get("initial", ""):
            self.__current_state = self.__data.get("initial", "")
        # TODO add checks

    def get_current_state(self):
        return self.__current_state

    def get_data(self):
        return self.get_data_state(self.__current_state)
        
    def get_data_state(self, state=None):
        if not state:
            return self.__data.get("data", {})
        else:
            return self.__data.get("state", {}).get(state, {}).get("data", {})

    def event(self, event=None):
        old_state = self.__current_state
        self.__current_state = self.__transition_dict.get((self.__current_state, event), self.__current_state)
        if old_state is not self.__current_state:
            self.automa_state_changed.emit(self.__current_state)

    def get_possible_transitions(self):
        return_transition_list = []
        for transition in self.__transition_dict.keys():
            # print("cs: {} -- transition: {}".format(self.current_state, transition))
            if self.__current_state == transition[0]:
                return_transition_list.append(transition[1])
        return return_transition_list


def test_state_changed_signal(new_state):
    print("state changed to: {}".format(new_state))


if __name__ == '__main__':
    json_file = "example_fsm.json"
    fsm = VaultState(json_file)
    fsm.automa_state_changed.connect(test_state_changed_signal)
    print(fsm.get_data_state())
    print(fsm.get_current_state())
    print(fsm.get_data())
    print(fsm.get_possible_transitions())
    fsm.automa_event.emit("init_ok")
    print(fsm.get_current_state())
    print(fsm.get_data())
    print(fsm.get_possible_transitions())
    fsm.event("start")
    print(fsm.get_current_state())
    print(fsm.get_data())
    print(fsm.get_possible_transitions())
