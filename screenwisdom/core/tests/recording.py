from time import sleep

from pynput import keyboard, mouse
import uiautomation as uia

import screenwisdom.core.recording as rec


# Tests everything to do with the MouseRecorder. By proxy tests construction of MouseClick, MouseScroll, Context,
# MouseCoordinates, and InputEvent.
def test_mouse_recorder():
    # NOTE: Calculator must be open and focussed.
    # Get details of calculator window and it's location
    sleep(2)
    calc_win = uia.WindowControl(searchDepth=4, Name="Calculator", ClassName="ApplicationFrameTitleBarWindow")
    calc_x = calc_win.BoundingRectangle.xcenter()
    calc_y = calc_win.BoundingRectangle.ycenter()

    # Start mouse recorder and create mouse controller
    mouse_rec = rec.MouseRecorder()
    mouse_controller = mouse.Controller()

    # Move mouse to just beside the minimise button
    mouse_controller.position = (calc_x - 90, calc_y)
    # Test all clicks
    mouse_controller.click(mouse.Button.left)
    mouse_controller.click(mouse.Button.middle)
    mouse_controller.click(mouse.Button.right)
    assert len(mouse_rec.recording) == 6  # Should be 3 clicks, 3 releases

    # Test scrolling
    mouse_controller.scroll(2, -3)
    scroll_event = mouse_rec.recording[-1]
    assert isinstance(scroll_event, rec.MouseScroll)
    assert scroll_event.dx == 2 and scroll_event.dy == -3

    # Test recording is cleared when popped
    recording = mouse_rec.pop_recording()
    assert len(mouse_rec.recording) == 0

    # Test Context data is correct
    first_event = recording[0]
    assert first_event.context.closest_ctrl_name == "Calculator"
    assert first_event.context.closest_ctrl_class_name == "ApplicationFrameTitleBarWindow"
    assert first_event.context.window_title == "Calculator"
    assert first_event.context.process_name == "ApplicationFrameHost.exe"


# Tests everything to do with the KeyboardRecorder. By proxy tests construction of KeyPress, KeyRelease, and InputEvent.
def test_keyboard_recorder():
    sleep(2)
    # Start keyboard recorder and create keyboard controller
    keyboard_rec = rec.KeyboardRecorder()
    keyboard_controller = keyboard.Controller()
    sleep(1)

    # Test normal typing
    keyboard_controller.type("TEST")
    sleep(1)
    assert len(keyboard_rec.recording) == 8

    # Test a press increases by 1
    keyboard_controller.press("T")
    sleep(1)
    assert len(keyboard_rec.recording) == 9

    # Test a release increases by 1
    keyboard_controller.release("T")
    sleep(1)
    assert len(keyboard_rec.recording) == 10


# Test get_relevant_control_attribute
def test_get_relevant_control_attribute():
    # The taskbar has no name, and its parent doesn't either, but the parent's parent is called DesktopWindowXamlSource.
    taskbar = uia.PaneControl(ClassName="Taskbar.TaskbarFrameAutomationPeer", AutomationId="TaskbarFrame")
    assert rec.Context.get_relevant_control_attribute(taskbar, "Name") == "DesktopWindowXamlSource"

    # Test if max_parent_control_checks works by limiting it to 1
    assert rec.Context.get_relevant_control_attribute(taskbar, "Name", 1) is None
