"""
Defines classes involved in recording input.
"""
from time import time
from dataclasses import dataclass, field

import uiautomation as uia
from pynput import mouse, keyboard

import screenwisdom.core.constants as constants


@dataclass
class Timestamp:
    """ Dataclass for storing a timestamp to be used by other classes. Currently, timestamp is just seconds since epoch.
    Made separate in case format of timestamp is changed. Knowing precisely when an event occurred may be useful. """
    timestamp: float


@dataclass
class MouseCoordinates:
    """ Dataclass for storing mouse coordinates to be used by other classes.
        :var x: the x coordinate, an integer.
        :var y: the y coordinate, also an integer.
        :var coords: not an argument, so you don't need to provide this - a tuple generated from the previous two
         attributes in the form (x, y).
    """
    x: int
    y: int
    coords: tuple = field(init=False)  # Make an attribute of type tuple that doesn't require an arg for instantiation

    def __post_init__(self):
        """ Initialise the coords attribute, based on the x and y attribute. """
        self.coords = (self.x, self.y)


class Context:
    """ Class that stores a details surrounding an interaction, such as a related uiautomation Control or the current
        application. The relevant information is retrieved immediately, should any be unavailable in the future. """

    def __init__(self, control):
        self.control = control

        # Extractable data
        self.closest_ctrl_name = None
        self.closest_ctrl_class_name = None

        # TODO: determine the current application

        # It is possible that extracting so much data will result in performance issues. Something to be aware of.
        try:
            self.closest_ctrl_name = self.get_relevant_control_attribute(self.control, "Name")
            self.closest_ctrl_class_name = self.get_relevant_control_attribute(self.control, "ClassName")
        except:
            pass  # It is possible that the control was deleted, or the application is closed, as data is extracted,
            # which may cause an exception.

    @staticmethod
    def get_relevant_control_attribute(control: uia.Control, attribute_name: str,
                                       max_parent_control_checks: int = 5) -> str | None:
        """
        Tries to get the attribute of a control from the control passed to the function, or from some nearby parent.

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
        ...  # TODO: make repr, after getting all the required data for context like application


@dataclass
class MouseClick(Timestamp, MouseCoordinates):
    """Class for storing details about a mouse click event. Requires a timestamp and mouse coordinates.
        :var button: the button pressed on the mouse, either Button.left, Button.right, or Button.middle
        :var pressed: True if pressed, False if released
        :var context: a Context object storing data about the context.
    """
    button: mouse.Button
    pressed: bool
    context: Context = field(init=False)

    def __post_init__(self):
        # Get control from where the mouse was clicked.
        self.context = Context(uia.ControlFromPoint(self.x, self.y))

    def __repr__(self):
        action = "pressed" if self.pressed else "released"
        return f"{self.button} button on mouse {action} at {self.coords}"


@dataclass
class MouseScroll(Timestamp, MouseCoordinates):
    """ Class for storing details about a mouse scroll event.
        :var dx: Horizontal scroll
        :var dy: Vertical scroll
        :var context: a Context object storing data about the context.
    """
    dx: int  # Horizontal scroll
    dy: int  # Vertical scroll
    context: Context = field(init=False)

    def __post_init__(self):
        # Get control from where the mouse was clicked.
        self.context = Context(uia.ControlFromPoint(self.x, self.y))

    def vertical_direction(self):
        return "down" if self.dy < 0 else "up"

    def horizontal_direction(self):
        return "left" if self.dx < 0 else "right"

    def __repr__(self):
        return f"mouse scrolled ({self.dx}, {self.dy}) at {self.coords}"


@dataclass
class KeyRelease(Timestamp):
    """ Records a single key being released.
        :var key: the key pressed """
    key: keyboard.KeyCode
    context: Context = field(init=False)

    def __post_init__(self):
        # Get control from the focused control
        self.context = Context(uia.GetFocusedControl())


class InputRecorder:
    """ A base class for recording a series of input events from some source. Offers a system for starting recordings
    automatically, provided the _build_listener method is overridden.
        :var recording: the recording of events. The format will depend on the extended classes of InputRecorder.
    """

    def __init__(self):
        """ Starts the recording. """
        self.recording = []  # Note, I didn't bother making this a property; a property would return a reference to
        # the original list anyway. I don't want to duplicate the list each time either, as that is large overhead for
        # something that may be done often.

        self._listener = self._build_listener()
        self._listener.start()

    def _build_listener(self):
        """
        Builds a listener of some sort, with callbacks assigned.
        Created with pynput mouse and keyboard listeners in mind.
        This one shouldn't be called.
        """
        raise Exception("This method should be overridden. Use a class inheriting this class instead.")

    def pop_recording(self):
        """
        Clears the recording and returns its contents. May be useful when repeatedly getting input from recorder, and
         you want to ignore previous events.
        Credit: Hugh Bothwell's answer from https://stackoverflow.com/questions/21608681/popping-all-items-from-python-list
        :return: the contents of recording, since the last pop.
        """
        # Assign result to the recording list, and the recording list attribute to a new blank list. Return result.
        # This gives the illusion of popping the entire list. Thanks, Hugh.
        result, self.recording = self.recording, []
        return result


class MouseRecorder(InputRecorder):
    """
    Records when the mouse scrolls up or down, or left or right, or if the mouse button is pressed or released,
    and provides some useful functions for working with the recording.
        :var recording: a list of MouseClick and MouseScroll objects, recorded over time.
    """

    def __init__(self):
        super().__init__()

    def _build_listener(self) -> mouse.Listener:
        """
        Creates a mouse Listener object that has callbacks assigned.
        :return: the mouse Listener.
        """

        def on_click(x, y, button, pressed):
            # Add a MouseClick object to the recording to indicate the event.
            self.recording.append(MouseClick(x, y, time(), button, pressed))

        def on_scroll(x, y, dx, dy):
            self.recording.append(MouseScroll(x, y, time(), dx, dy))

        listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)

        return listener


class KeyboardRecorder(InputRecorder):
    """
    Records key presses, and provides some useful functions for working with the recording.
        :var recording: a list of KeyPress objects, recorded over time.
    """

    def __init__(self):
        super().__init__()

    def _build_listener(self) -> keyboard.Listener:
        """
        Creates a keyboard Listener object that has callbacks assigned to on_release.
        The reason only on_release has a callback is that holding a key for a while floods on_press with data. I'll
        change the system to include this if needs be, key releases should be sufficient.
        :return: the keyboard Listener.
        """

        def record_key(key: keyboard.KeyCode):
            self.recording.append(KeyRelease(time(), key))

        listener = keyboard.Listener(on_release=record_key)

        return listener


class Interaction:
    """
    Represents part of a recording, so it can be turned into coherent english.
    """

    def __init__(self, interaction_type: constants.InteractionType, interaction_value: str):
        """
        Creates the interaction, and gets further information regarding the context of the interaction.

        :param interaction_type: the type of the interaction, e.g., if the interaction is a left click if it involves
         the keyboard.
        :param interaction_value: further information about the interaction (e.g., text that was typed, or the mouse
         button that was pressed)
        """
        self.interaction_type = interaction_type
        self.interaction_value = interaction_value
        # TODO: add other significant data about interaction, such as the application being used

    def __repr__(self):
        ...  # TODO: rewrite repr


def interactions_from_recording(rec: InputRecorder) -> [Interaction]:
    """
    Pops all events in the recording of an InputRecorder, and analyses it to create meaningful Interaction objects.
    :param rec: an InputRecorder to analyse the recording of.
    :return: a list of interactions representing the recording.
    """
    ...


if __name__ == "__main__":
    recorder = KeyboardRecorder()
    from time import sleep

    while True:
        sleep(1)
        print(recorder.recording)
