from time import sleep

import psutil
import win32gui
import win32process

sleep(2)
current_window = win32gui.GetForegroundWindow()
pid = win32process.GetWindowThreadProcessId(current_window)[-1]

process = psutil.Process(pid)

print(process.name())
