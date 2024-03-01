try:
    import uiautomation
    import pynput
    import psutil
    import win32
    print("Successfully accessed needed libraries.")
except Exception as e:
    print(f"Failed to access needed libraries. The virtual environment is not set up correctly.\n"
          f"More details: {e}")
