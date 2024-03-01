# Simple test for checking the virtual environment is working

try:
    # Attempt to import the needed libraries.
    import uiautomation
    import pynput
    import psutil
    import win32
    print("Successfully accessed needed libraries.")

except Exception as exception:
    # Exception will be thrown if a library is not installed correctly. Print the exception for debugging.
    print(f"Failed to access needed libraries. The virtual environment is not set up correctly.\n"
          f"More details: {exception}")
