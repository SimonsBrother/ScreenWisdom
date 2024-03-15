from enum import Enum


class InteractionType(Enum):
    """
    Represents the significant ways the user can interact with the computer at a high level.
    """
    # Mouse interactions
    MOUSE_PRESSED = "mouse pressed"
    MOUSE_SCROLLED = "mouse scrolled"
    # todo: drag

    # Keyboard interactions
    ENTER_PRESSED = "enter key pressed"
    KEYBOARD_TYPING = "typing"
