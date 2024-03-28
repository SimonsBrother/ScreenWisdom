""" Expected output
Left click
Middle click
Right click

Double-left-click
Double-middle-click
Double-right-click

Drag left button
Drag middle button
Drag right button

Scroll horizontally by 1
Scroll vertically by 1
Scroll horizontally by 5 and vertically by 5
Scroll horizontally by -5 and vertically by 5

Type "Test"

"t" held for 2 seconds

"t" tapped
"""

from time import sleep
from pynput import keyboard, mouse

from screenwisdom.core.recording import *
from screenwisdom.core.interpreting import *

sleep(2)
# Simulates all the possible Interaction types
# Start recording and controllers
mouse_rec = MouseRecorder()
keyboard_rec = KeyboardRecorder()

mouse_con = mouse.Controller()
keyboard_con = keyboard.Controller()


# Helper functions
def double_click(button: mouse.Button):
    mouse_con.click(button)
    sleep(0.3)
    mouse_con.click(button)


def drag(button: mouse.Button):
    mouse_con.press(button)
    mouse_con.move(30, 30)
    mouse_con.release(button)


# Clicking
mouse_con.click(mouse.Button.left)
mouse_con.click(mouse.Button.middle)
mouse_con.click(mouse.Button.right)
sleep(1)

# Double-clicking
double_click(mouse.Button.left)
double_click(mouse.Button.middle)
double_click(mouse.Button.right)
sleep(1)

# Dragging
drag(mouse.Button.left)
drag(mouse.Button.middle)
drag(mouse.Button.right)
sleep(1)

# Mouse scrolled
mouse_con.scroll(1, 0)
mouse_con.scroll(0, 1)
mouse_con.scroll(5, 5)
mouse_con.scroll(-5, 5)

# Keyboard
keyboard_con.type("Test")
sleep(3)

# Press and hold key
keyboard_con.press("t")
sleep(2)
keyboard_con.release("t")
sleep(2)

# Press
keyboard_con.tap("t")
sleep(2)

# Interpret
mouse_interactions = interactions_from_mouse_recording(mouse_rec.pop_recording())
keyboard_interactions = interactions_from_keyboard_recording(keyboard_rec.pop_recording())

combined = mouse_interactions + keyboard_interactions
combined.sort(key=lambda e: e.interaction_start_timestamp)
for interaction in combined:
    print(translate_interaction(interaction))
