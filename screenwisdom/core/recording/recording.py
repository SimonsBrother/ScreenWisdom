"""
Defines classes involved in recording input.
"""
from time import time
from dataclasses import dataclass, field

import psutil
import uiautomation as uia
import win32process
from pynput import mouse, keyboard


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
        self.window_title = None
        self.process_name = None

        # It is possible that extracting so much data will result in performance issues. Something to be aware of.
        try:
            # Control analysis
            self.closest_ctrl_name = self.get_relevant_control_attribute(self.control, "Name")
            self.closest_ctrl_class_name = self.get_relevant_control_attribute(self.control, "ClassName")

            # Window title
            window_handle = uia.WindowFromPoint(*uia.GetCursorPos())
            self.window_title = uia.GetWindowText(window_handle)

            # Get current process name. Start by getting PID from window handle, which is the last element.
            pid = win32process.GetWindowThreadProcessId(window_handle)[-1]
            self.process_name = psutil.Process(pid).name()
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
        return (f"Context(control={self.control}, "
                f"closest_ctrl_name={self.closest_ctrl_name}, "
                f"closest_ctrl_class_name={self.closest_ctrl_class_name}, "
                f"window_title='{self.window_title}', "
                f"process_name='{self.process_name}')")


@dataclass
class InputEvent:
    """ Defines required information about all input events, such as a mouse click or a key press.
        :var timestamp: seconds since epoch the event occurred. IMPORTANT: not assigned automatically, this is too slow.
        :var context: a Context object - not set by this class, must be set by something extending this class.
    """
    timestamp: float
    context: Context = field(init=False)


@dataclass
class MouseClick(InputEvent, MouseCoordinates):
    """Class for storing details about a mouse click event. Requires a timestamp and mouse coordinates.
        :var button: the button pressed on the mouse, either Button.left, Button.right, or Button.middle
        :var pressed: True if pressed, False if released
        :var context: a Context object storing data about the context.
    """
    button: mouse.Button
    pressed: bool

    def __post_init__(self):
        super().__post_init__()
        with uia.UIAutomationInitializerInThread():
            # Get control from where the mouse was clicked.
            self.context = Context(uia.ControlFromPoint(self.x, self.y))


@dataclass
class MouseScroll(InputEvent, MouseCoordinates):
    """ Class for storing details about a mouse scroll event.
        :var dx: Horizontal scroll
        :var dy: Vertical scroll
        :var context: a Context object storing data about the context.
    """
    dx: int  # Horizontal scroll
    dy: int  # Vertical scroll

    def __post_init__(self):
        super().__post_init__()
        with uia.UIAutomationInitializerInThread():
            # Get control from where the mouse was clicked.
            self.context = Context(uia.ControlFromPoint(self.x, self.y))

    def vertical_direction(self):
        return "down" if self.dy < 0 else "up"

    def horizontal_direction(self):
        return "left" if self.dx < 0 else "right"


@dataclass
class KeyRelease(InputEvent):
    """ Records a single key being released.
        :var key: the key pressed """
    key: keyboard.KeyCode

    def __post_init__(self):
        with uia.UIAutomationInitializerInThread():
            # Get control from the focused control
            self.context = Context(uia.GetFocusedControl())


@dataclass
class KeyPress(InputEvent):
    """ Records a single key being pressed or held.
        :var key: the key pressed """
    key: keyboard.KeyCode

    def __post_init__(self):
        with uia.UIAutomationInitializerInThread():
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
         Credit: Hugh Bothwell's answer
         from https://stackoverflow.com/questions/21608681/popping-all-items-from-python-list
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

        def record_key_press(key: keyboard.KeyCode):
            self.recording.append(KeyPress(time(), key))

        def record_key_release(key: keyboard.KeyCode):
            self.recording.append(KeyRelease(time(), key))

        listener = keyboard.Listener(on_press=record_key_press, on_release=record_key_release)

        return listener


if __name__ == "__main__":
    recorder = MouseRecorder()
    from time import sleep

    while True:
        sleep(1)
        try:
            print(recorder.recording)
            # TODO: an error may occur if you left click the pycharm editor and then right click quickly
            # Error: (-2147220991, 'An event was unable to invoke any of the subscribers', (None, None, None, 0, None))
        except Exception as e:
            print(f"Error: {e}")
