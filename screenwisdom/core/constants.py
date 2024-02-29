from enum import Enum


class MouseInteractionType(Enum):
    """
    Represents the ways the user can interact with the user via the mouse.
    """
    MOUSE_LEFT = "left mouse button"
    MOUSE_RIGHT = "right mouse button"
    MOUSE_MIDDLE = "middle mouse button"


class KeyboardInteractionType(Enum):
    """
    Represents the ways the user can interact with the user via the keyboard.
    """
    ENTER_PRESSED = "enter key pressed"
    TYPING = "typing"


class InteractionType(Enum):
    """
    Represents the ways the user can interact with the user.
    """
    MOUSE = MouseInteractionType
    KEYBOARD = KeyboardInteractionType
