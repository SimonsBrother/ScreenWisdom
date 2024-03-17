from enum import Enum


class InteractionType(Enum):
    """
    Represents the significant ways the user can interact with the computer at a high level.
    """
    # Mouse interactions
    MOUSE_CLICKED = "mouse clicked"
    MOUSE_DOUBLE_CLICKED = "mouse double clicked"
    MOUSE_SCROLLED = "mouse scrolled"
    MOUSE_DRAGGED = "mouse dragged"

    # Keyboard interactions
    SINGLE_KEY_PRESSED = "single key pressed"
    KEYBOARD_TYPING = "typing"
