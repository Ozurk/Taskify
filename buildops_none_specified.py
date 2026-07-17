"""
BuildOps bulk "Project Type -> None Specified" clicker.
Adapted from Taskify main.py. Uses the same pics/ reference images:

  Image1.png = "Number" column header  (list page)   -> click 40px below = first row
  Image2.png = "EDIT PROJECT" button   (project page)
  Image3.png = "PROJECT TYPE" label    (edit dialog)  -> click 28px below = dropdown
  Image4.png = "None Specified" option (open dropdown)
  Image5.png = "SAVE" button           (edit dialog)
  Image6.png = "Project Management" breadcrumb (project page) -> back to list

HOW TO RUN
  1. Open Chrome to the Project Management page with the "Unspecified Type"
     view + its 5 filters ACTIVE. (Critical: if the filters are off, this
     script will overwrite types on EVERY project.)
  2. Browser window maximized, same zoom level as when images were snipped.
  3. Run this script, click Execute, then keep hands off mouse/keyboard.
  4. ABORT any time by slamming the mouse into the top-left screen corner
     (pyautogui failsafe).

The script stops itself after 3 failed projects in a row (usually means the
list is empty and the job is done, or the page changed).
"""

import tkinter as tk
import pyautogui
import time

pyautogui.FAILSAFE = True

CONFIDENCE = 0.75
MAX_PROJECTS = 3000          # loop ceiling; stops early on repeated failure
ROW_OFFSET_Y = 40            # px below "Number" header = first data row
DROPDOWN_OFFSET_Y = 28       # px below "PROJECT TYPE" label = the dropdown
SCROLL_STEP = -300           # per attempt while hunting for PROJECT TYPE
SCROLL_ATTEMPTS = 6

PAGE_LOAD_WAIT = 3           # after opening a project
DIALOG_WAIT = 2              # after clicking EDIT PROJECT
SAVE_WAIT = 4                # after clicking SAVE
LIST_RELOAD_WAIT = 5         # after returning to the list


def find(image_name, retries=3, wait=1.0):
    """Locate an image on screen. Returns center point or None."""
    path = "pics/" + image_name
    for _ in range(retries):
        try:
            loc = pyautogui.locateOnScreen(path, confidence=CONFIDENCE)
            if loc:
                return pyautogui.center(loc)
        except Exception:
            pass
        time.sleep(wait)
    print(f"  !! {path} not found")
    return None


def click_at(point, dy=0):
    pyautogui.moveTo(point.x, point.y + dy, duration=0.3)
    pyautogui.click()


def find_type_field_with_scroll():
    """The edit dialog opens at unpredictable scroll positions.
    Hunt for the PROJECT TYPE label: try as-is, scroll down in steps,
    then scroll back up in steps."""
    pt = find("Image3.png", retries=1)
    if pt:
        return pt
    for direction in (SCROLL_STEP, -SCROLL_STEP):
        for _ in range(SCROLL_ATTEMPTS):
            pyautogui.scroll(direction)
            time.sleep(0.4)
            pt = find("Image3.png", retries=1)
            if pt:
                return pt
    return None


def recover_to_list():
    """Get back to the project list no matter where we are."""
    pyautogui.press("esc")   # close dropdown if open
    time.sleep(0.5)
    pyautogui.press("esc")   # close edit dialog if open
    time.sleep(1)
    crumb = find("Image6.png", retries=1)
    if crumb:
        click_at(crumb)
    else:
        pyautogui.hotkey("alt", "left")  # browser back
    time.sleep(LIST_RELOAD_WAIT)


def process_one_project():
    """Returns True on success, False on any miss (then caller recovers)."""
    # 1. open first project in the filtered list
    header = find("Image1.png")
    if not header:
        return False
    click_at(header, dy=ROW_OFFSET_Y)
    time.sleep(PAGE_LOAD_WAIT)

    # 2. open the edit dialog
    edit = find("Image2.png")
    if not edit:
        return False
    click_at(edit)
    time.sleep(DIALOG_WAIT)

    # 3. find PROJECT TYPE (scroll-hunt) and open the dropdown
    label = find_type_field_with_scroll()
    if not label:
        return False
    click_at(label, dy=DROPDOWN_OFFSET_Y)
    time.sleep(1)

    # 4. pick "None Specified"
    option = find("Image4.png")
    if not option:
        return False
    click_at(option)
    time.sleep(0.5)

    # 5. save
    save = find("Image5.png")
    if not save:
        return False
    click_at(save)
    time.sleep(SAVE_WAIT)

    # 6. breadcrumb back to the list
    crumb = find("Image6.png")
    if not crumb:
        return False
    click_at(crumb)
    time.sleep(LIST_RELOAD_WAIT)
    return True


def run():
    done, fails = 0, 0
    for i in range(MAX_PROJECTS):
        print(f"--- project {i + 1} (done so far: {done}) ---")
        if process_one_project():
            done += 1
            fails = 0
        else:
            fails += 1
            print(f"  miss #{fails} — recovering to list")
            recover_to_list()
            if fails >= 3:
                print("3 misses in a row — stopping. "
                      "Either the list is empty (job done!) or the page changed.")
                break
    print(f"Finished. Projects updated this run: {done}")


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BuildOps: Type -> None Specified")
        self.root.geometry("420x160")
        tk.Label(self.root, text=(
            "1) Chrome open on the FILTERED project list\n"
            "2) Same window size/zoom as when images were snipped\n"
            "3) Click Execute, then hands off\n"
            "ABORT: slam mouse to top-left corner"), justify="left").pack(pady=10)
        tk.Button(self.root, text="Execute (starts in 5 s)",
                  command=self.execute, height=2).pack(fill="x", padx=20)
        self.root.mainloop()

    def execute(self):
        self.root.iconify()   # get the window out of the way
        time.sleep(5)         # time to focus Chrome
        run()


if __name__ == "__main__":
    App()
