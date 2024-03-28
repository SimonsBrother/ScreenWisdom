from enum import Enum


class InteractionType(Enum):
    """
    Represents the significant ways the user can interact with the computer at a high level.
    """
    # Mouse interactions
    MOUSE_DRAGGED = "mouse dragged"
    MOUSE_CLICKED = "mouse clicked"
    MOUSE_DOUBLE_CLICKED = "mouse double clicked"
    MOUSE_SCROLLED = "mouse scrolled"

    # Keyboard interactions
    SINGLE_KEY_PRESSED = "single key pressed"
    SINGLE_KEY_HELD = "single key held"
    KEYBOARD_TYPING = "typing"


MOUSE_MAX_DOUBLE_CLICK_DELAY_SECONDS = 0.5
KEYBOARD_MAX_TYPING_DELAY_SECONDS = 1.5
