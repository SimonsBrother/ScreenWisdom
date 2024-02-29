import uiautomation as uia
from pynput import mouse, keyboard

import screenwisdom.core.constants as constants


class Interaction:
    """
    Records some interaction by the user with the computer.
    """
    def __init__(self, interaction_type: constants.InteractionType, interaction_value: str, control: uia.Control):
        """

        :param interaction_type: the type of the interaction, e.g., if the interaction is a left click if it involes
        the keyboard.
        :param interaction_value: further information about the interaction (e.g., text that was typed)
        :param control: the control directly involved with the interaction.
        """
        self.interaction_type = interaction_type
        self.interaction_value = interaction_value
        self.control = control

        self.closest_ctrl_name = self.get_relevant_control_attribute(self.control, "Name")
        self.closest_ctrl_class_name = self.get_relevant_control_attribute(self.control, "ClassName")

    @staticmethod
    def get_relevant_control_attribute(control: uia.Control, attribute_name: str,
                                       max_parent_control_checks: int = 5) -> str | None:
        """
        Tries to get the attribute of a control from the control passed to the function, or from some parent.
        :param control: some Control object related to what the user is doing.
        :param attribute_name: the name of the attribute to retrieve.
        :param max_parent_control_checks: the maximum number of parents to check for the attribute if the original
        control does not have it.
        :return: the value of the attribute from the control provided or one of its parents; None if no attribute was
        found or the max number of parents was reached.
        """
        # getattr is used often in this function, but the second parameter is the same each time; the get_attribute
        # function removes the need to supply this argument each time.
        def get_attribute(obj):
            return getattr(obj, attribute_name)

        # If the required attribute is assigned to the control, return it
        if get_attribute(control) != "":
            return get_attribute(control)

        # Otherwise, there is no attribute assigned, so get the parent
        parent = control.GetParentControl()
        name_search_attempts = 1
        # Stop and return None if parent is None or if it has checked the maximum number of parents allowed
        while (parent is not None
               and name_search_attempts <= max_parent_control_checks):

            # If the parent name isn't blank, return it
            if get_attribute(parent) != "":
                return get_attribute(parent)

            # Otherwise, find the next parent control
            parent = parent.GetParentControl()
            name_search_attempts += 1

        return None

    def __repr__(self):
        return (f"Interaction(type={self.interaction_type}, "
                f"name='{self.closest_ctrl_name}', "
                f"classname='{self.closest_ctrl_class_name}')")


class MouseRecorder:
    """
    Records when the mouse scrolls up or down by some unit, or if the mouse button is pressed or released,
    and provides some useful functions for working with the recording.
    """
    def __init__(self):
        """ Starts the recording. """
        self.buffer = []
        self.listener = self._build_mouse_listener()
        self.listener.start()

    def _build_mouse_listener(self) -> mouse.Listener:
        """
        Creates a mouse Listener object that has callbacks assigned.
        :return: the mouse Listener.
        """

        def on_click(x, y, button, pressed):
            action = "pressed" if pressed else "released"
            self.buffer.append(f"mouse {action} at ({x}, {y})")

        def on_scroll(x, y, dx, dy):
            direction = "down" if dy < 0 else "up"
            self.buffer.append(f"mouse scrolled {direction} at ({x}, {y})")

        listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)

        return listener


class KeyboardRecorder:
    """
    Records key presses, and provides some useful functions for working with the recording.
    """
    def __init__(self):
        """ Starts the recording. """
        self.buffer = []
        self.listener = self._build_keyboard_listener()
        self.listener.start()

    def _build_keyboard_listener(self) -> keyboard.Listener:
        """
        Creates a keyboard Listener object that has callbacks assigned.
        :return: the keyboard Listener.
        """
        def on_press(key: keyboard.KeyCode):
            self.buffer.append(key)

        listener = keyboard.Listener(on_press=on_press)

        return listener


if __name__ == "__main__":
    kb_recorder = MouseRecorder()
    from time import sleep

    while True:
        sleep(1)
        print(kb_recorder.buffer)
