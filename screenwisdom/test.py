import uiautomation as uia
from time import sleep
print(uia.GetRootControl())
sleep(2)
while True:
    print(uia.ControlFromCursor())
    print(uia.ControlFromCursor().GetParentControl())
    print(uia.ControlFromCursor().GetParentControl().GetParentControl())
    sleep(2)
