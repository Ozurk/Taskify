"""PO Item Selector: a tkinter GUI for capturing reference images from the
clipboard and building/running a click-and-type macro against them with
pyautogui. The macro ("script") is a list of steps built entirely from the
UI -- no code changes are needed to reprogram what execute() does."""

import json
import os
import threading
import time

import pyautogui
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageGrab, ImageTk

WINDOW_SIZE = "980x640"
THUMBNAIL_SIZE = (70, 70)
MAX_BUTTON_COUNT = 10

DEFAULT_BUTTON_COUNT = 5
DEFAULT_CONFIDENCE = 0.75
DEFAULT_ITERATIONS = 3000

SCRIPT_FILE = "script.json"

# Seed script matching the tool's original hard-coded click sequence. Once
# loaded, this is fully editable (and persisted) from the Script tab.
DEFAULT_STEPS = [
    {"type": "image", "image": "Image1.png", "action": "click", "dx": 0, "dy": 45, "pre_sleep": 3, "post_sleep": 3},
    {"type": "image", "image": "Image2.png", "action": "click", "dx": 0, "dy": 0, "pre_sleep": 0, "post_sleep": 3},
    {"type": "scroll", "amount": -1000, "pre_sleep": 0, "post_sleep": 0},
    {"type": "image", "image": "Image3.png", "action": "click", "dx": 0, "dy": 28, "pre_sleep": 0, "post_sleep": 0},
    {"type": "image", "image": "Image4.png", "action": "click", "dx": 0, "dy": 0, "pre_sleep": 0, "post_sleep": 2},
    {"type": "image", "image": "Image5.png", "action": "click", "dx": 0, "dy": 0, "pre_sleep": 0, "post_sleep": 3},
    {"type": "image", "image": "Image6.png", "action": "click", "dx": 0, "dy": 0, "pre_sleep": 0, "post_sleep": 3},
]


def load_initial_steps():
    if os.path.exists(SCRIPT_FILE):
        try:
            with open(SCRIPT_FILE) as f:
                steps = json.load(f)
            if isinstance(steps, list):
                return steps
        except (OSError, json.JSONDecodeError):
            pass
    return [dict(step) for step in DEFAULT_STEPS]


def list_available_images():
    if not os.path.isdir("pics"):
        return []
    return sorted(f for f in os.listdir("pics") if f.lower().endswith(".png"))


def step_summary(step):
    pre, post = step.get("pre_sleep") or 0, step.get("post_sleep") or 0
    delay_bits = [f"pre {pre}s"] if pre else []
    delay_bits += [f"post {post}s"] if post else []
    delay = f"  [{', '.join(delay_bits)}]" if delay_bits else ""

    step_type = step.get("type")
    if step_type == "image":
        action = "Click" if step.get("action") == "click" else "Move to"
        dx, dy = step.get("dx", 0), step.get("dy", 0)
        offset = f" (+{dx}, +{dy})" if dx or dy else ""
        return f"{action} {step.get('image')}{offset}{delay}"
    if step_type == "move":
        return f"Move mouse ({step.get('dx', 0)}, {step.get('dy', 0)}){delay}"
    if step_type == "scroll":
        return f"Scroll {step.get('amount', 0)}{delay}"
    if step_type == "type":
        text = step.get("text", "")
        text = text if len(text) <= 30 else text[:27] + "..."
        return f'Type "{text}"{delay}'
    return "Unknown step"


class POItemSelectorApp:

    def __init__(self):
        self.confidence = DEFAULT_CONFIDENCE
        self.save_buttons = []
        self.script_steps = load_initial_steps()
        self.stop_event = threading.Event()
        self.execution_thread = None

        self.root = tk.Tk()
        self.root.title("PO Item Selector")
        self.root.geometry(WINDOW_SIZE)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.button_count_var = tk.IntVar(value=DEFAULT_BUTTON_COUNT)
        self.confidence_var = tk.DoubleVar(value=self.confidence)

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        images_tab = tk.Frame(notebook)
        script_tab = tk.Frame(notebook)
        notebook.add(images_tab, text="Capture Images")
        notebook.add(script_tab, text="Script")

        self._build_images_tab(images_tab)
        self._build_script_tab(script_tab)
        self._build_settings_panel()

        self.root.mainloop()

    # -- Capture Images tab --------------------------------------------------

    def _build_images_tab(self, tab):
        self.images_frame = tab
        self.update_buttons(self.button_count_var.get())
        for r in range(MAX_BUTTON_COUNT):
            tab.rowconfigure(r, weight=1)
        for c in range(2):
            tab.columnconfigure(c, weight=1)

    def on_button_count_change(self, event=None):
        self.update_buttons(self.button_count_var.get())

    def update_buttons(self, count):
        for button in self.save_buttons:
            button.button.destroy()
            button.thumbnail_label.destroy()

        self.save_buttons = [
            ImageSavingButton(f"Save Image{i + 1}", self.images_frame, f"Image{i + 1}.png", row=i)
            for i in range(count)
        ]

    # -- Settings panel --------------------------------------------------------

    def _build_settings_panel(self):
        settings_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        settings_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self._add_slider(
            settings_frame, "Number of Save Image Buttons", self.button_count_var,
            from_=1, to=MAX_BUTTON_COUNT, command=self.on_button_count_change,
        )
        self._add_slider(
            settings_frame, "Confidence", self.confidence_var,
            from_=0.5, to=1.0, resolution=0.01,
        )

        tk.Button(settings_frame, text="Apply Settings", command=self.apply_settings).pack(pady=20)

    @staticmethod
    def _add_slider(parent, label, variable, **scale_kwargs):
        tk.Label(parent, text=label).pack(pady=(10, 0))
        tk.Scale(parent, orient=tk.HORIZONTAL, variable=variable, **scale_kwargs).pack(pady=5, fill="x")

    def apply_settings(self):
        self.confidence = self.confidence_var.get()
        print(f"Settings applied: confidence={self.confidence}")

    # -- Script tab: build the step list ---------------------------------------

    def _build_script_tab(self, tab):
        list_frame = tk.Frame(tab)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.steps_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=14)
        self.steps_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.steps_listbox.yview)
        self.steps_listbox.bind("<Double-Button-1>", lambda e: self.edit_step())

        edit_toolbar = tk.Frame(tab)
        edit_toolbar.pack(fill="x", padx=10)
        tk.Button(edit_toolbar, text="Add Step", command=self.add_step).pack(side="left", padx=2)
        tk.Button(edit_toolbar, text="Edit Step", command=self.edit_step).pack(side="left", padx=2)
        tk.Button(edit_toolbar, text="Delete Step", command=self.delete_step).pack(side="left", padx=2)
        tk.Button(edit_toolbar, text="Move Up", command=lambda: self.move_step(-1)).pack(side="left", padx=2)
        tk.Button(edit_toolbar, text="Move Down", command=lambda: self.move_step(1)).pack(side="left", padx=2)
        tk.Button(edit_toolbar, text="Run Selected", command=self.run_selected_step).pack(side="left", padx=2)

        file_toolbar = tk.Frame(tab)
        file_toolbar.pack(fill="x", padx=10, pady=(5, 0))
        tk.Button(file_toolbar, text="Save Script...", command=self.save_script).pack(side="left", padx=2)
        tk.Button(file_toolbar, text="Load Script...", command=self.load_script).pack(side="left", padx=2)

        run_bar = tk.Frame(tab, relief=tk.RIDGE, borderwidth=1)
        run_bar.pack(fill="x", padx=10, pady=10)
        tk.Label(run_bar, text="Repeat Count:").pack(side="left", padx=(10, 5), pady=10)
        self.repeat_count_var = tk.StringVar(value=str(DEFAULT_ITERATIONS))
        tk.Entry(run_bar, textvariable=self.repeat_count_var, width=8).pack(side="left", pady=10)
        self.execute_button = tk.Button(run_bar, text="Execute", command=self.start_execution)
        self.execute_button.pack(side="left", padx=10, pady=10)
        self.stop_button = tk.Button(run_bar, text="Stop", command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.pack(side="left", pady=10)

        self.refresh_steps_listbox()

    def refresh_steps_listbox(self):
        self.steps_listbox.delete(0, tk.END)
        for i, step in enumerate(self.script_steps, start=1):
            self.steps_listbox.insert(tk.END, f"{i}. {step_summary(step)}")

    def add_step(self):
        StepEditorDialog(self.root, list_available_images(), on_save=self._append_step)

    def _append_step(self, step):
        self.script_steps.append(step)
        self.refresh_steps_listbox()

    def edit_step(self):
        selection = self.steps_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        StepEditorDialog(
            self.root, list_available_images(), step=self.script_steps[index],
            on_save=lambda step: self._replace_step(index, step),
        )

    def _replace_step(self, index, step):
        self.script_steps[index] = step
        self.refresh_steps_listbox()
        self.steps_listbox.selection_set(index)

    def delete_step(self):
        selection = self.steps_listbox.curselection()
        if not selection:
            return
        del self.script_steps[selection[0]]
        self.refresh_steps_listbox()

    def move_step(self, offset):
        selection = self.steps_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        new_index = index + offset
        if 0 <= new_index < len(self.script_steps):
            steps = self.script_steps
            steps[index], steps[new_index] = steps[new_index], steps[index]
            self.refresh_steps_listbox()
            self.steps_listbox.selection_set(new_index)

    def save_script(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", initialfile=SCRIPT_FILE, filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self.script_steps, f, indent=2)
        print(f"Script saved to {path}")

    def load_script(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path) as f:
            self.script_steps = json.load(f)
        self.refresh_steps_listbox()
        print(f"Script loaded from {path}")

    # -- Script execution --------------------------------------------------------

    def run_selected_step(self):
        if self.execution_thread and self.execution_thread.is_alive():
            return
        selection = self.steps_listbox.curselection()
        if not selection:
            return
        step = self.script_steps[selection[0]]
        threading.Thread(target=self.run_step, args=(step,), daemon=True).start()

    def start_execution(self):
        if self.execution_thread and self.execution_thread.is_alive():
            return
        if not self.script_steps:
            messagebox.showinfo("Empty script", "Add at least one step before executing.")
            return
        try:
            repeat_count = int(self.repeat_count_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Repeat count must be a whole number.")
            return

        self.stop_event.clear()
        self.execute_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.execution_thread = threading.Thread(target=self._run_script, args=(repeat_count,), daemon=True)
        self.execution_thread.start()

    def stop_execution(self):
        self.stop_event.set()

    def _run_script(self, repeat_count):
        for _ in range(repeat_count):
            if self.stop_event.is_set():
                break
            for step in self.script_steps:
                if self.stop_event.is_set():
                    break
                self.run_step(step)
        self.root.after(0, self._on_execution_finished)

    def _on_execution_finished(self):
        self.execute_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run_step(self, step):
        """Run a single step. Safe to call from the execution thread or directly."""
        pre_sleep = step.get("pre_sleep") or 0
        if pre_sleep:
            time.sleep(pre_sleep)

        step_type = step.get("type")
        if step_type == "image":
            self.click_image(
                step["image"], dx=step.get("dx", 0), dy=step.get("dy", 0),
                click=step.get("action", "click") == "click",
            )
        elif step_type == "move":
            pyautogui.moveRel(step.get("dx", 0), step.get("dy", 0), duration=0.5)
        elif step_type == "scroll":
            pyautogui.scroll(step.get("amount", 0))
        elif step_type == "type":
            pyautogui.write(step.get("text", ""))

        post_sleep = step.get("post_sleep") or 0
        if post_sleep:
            time.sleep(post_sleep)

    def click_image(self, image_name, dx=0, dy=0, click=True):
        """Locate `image_name` on screen and move (optionally clicking) `dx`, `dy` from its center."""
        image_path = f"pics/{image_name}"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if not location:
                print(f"{image_path} not found on screen.")
                return False

            x, y = pyautogui.center(location)
            print(f"Found {image_path} at ({x}, {y}). {'Clicking' if click else 'Moving'}.")
            pyautogui.moveTo(x + dx, y + dy, duration=0.5)
            if click:
                pyautogui.click()
            return True
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Stopping script.")
            self.stop_event.set()
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False


class StepEditorDialog(tk.Toplevel):
    """Modal dialog for adding or editing a single script step."""

    TYPE_LABELS = {"image": "Image", "move": "Move Mouse", "scroll": "Scroll", "type": "Type Text"}
    LABEL_TYPES = {label: key for key, label in TYPE_LABELS.items()}

    def __init__(self, parent, available_images, step=None, on_save=None):
        super().__init__(parent)
        self.title("Edit Step" if step else "Add Step")
        self.transient(parent)
        self.resizable(False, False)

        self.available_images = available_images or ["(no images captured yet)"]
        self.on_save = on_save
        self._existing = step or {}

        type_row = tk.Frame(self)
        type_row.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(type_row, text="Step Type:").pack(side="left")
        self.type_var = tk.StringVar(value=self.TYPE_LABELS.get(self._existing.get("type"), "Image"))
        type_combo = ttk.Combobox(
            type_row, textvariable=self.type_var, state="readonly", values=list(self.TYPE_LABELS.values()),
        )
        type_combo.pack(side="left", padx=5)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._render_fields())

        self.dynamic_frame = tk.Frame(self)
        self.dynamic_frame.pack(fill="x", padx=10, pady=5)

        delay_row = tk.Frame(self)
        delay_row.pack(fill="x", padx=10, pady=5)
        tk.Label(delay_row, text="Delay before (s):").grid(row=0, column=0, sticky="w")
        self.pre_sleep_var = tk.StringVar(value=str(self._existing.get("pre_sleep", 0)))
        tk.Entry(delay_row, textvariable=self.pre_sleep_var, width=6).grid(row=0, column=1, padx=5)
        tk.Label(delay_row, text="Delay after (s):").grid(row=0, column=2, sticky="w", padx=(15, 0))
        self.post_sleep_var = tk.StringVar(value=str(self._existing.get("post_sleep", 0)))
        tk.Entry(delay_row, textvariable=self.post_sleep_var, width=6).grid(row=0, column=3, padx=5)

        button_row = tk.Frame(self)
        button_row.pack(fill="x", padx=10, pady=(5, 10))
        tk.Button(button_row, text="Save", command=self._on_save).pack(side="right", padx=5)
        tk.Button(button_row, text="Cancel", command=self.destroy).pack(side="right")

        self._render_fields(initial=self._existing)
        self.grab_set()

    def _render_fields(self, initial=None):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        step_type = self.LABEL_TYPES[self.type_var.get()]
        initial = initial if initial and initial.get("type") == step_type else {}

        if step_type == "image":
            tk.Label(self.dynamic_frame, text="Image:").grid(row=0, column=0, sticky="w")
            self.image_var = tk.StringVar(value=initial.get("image", self.available_images[0]))
            ttk.Combobox(
                self.dynamic_frame, textvariable=self.image_var, state="readonly",
                values=self.available_images, width=20,
            ).grid(row=0, column=1, columnspan=3, sticky="w", padx=5)

            self.action_var = tk.StringVar(value="Move To" if initial.get("action") == "move" else "Click")
            tk.Radiobutton(self.dynamic_frame, text="Move To", variable=self.action_var, value="Move To").grid(row=1, column=0, sticky="w")
            tk.Radiobutton(self.dynamic_frame, text="Click", variable=self.action_var, value="Click").grid(row=1, column=1, sticky="w")

            tk.Label(self.dynamic_frame, text="X Offset:").grid(row=2, column=0, sticky="w")
            self.dx_var = tk.StringVar(value=str(initial.get("dx", 0)))
            tk.Entry(self.dynamic_frame, textvariable=self.dx_var, width=6).grid(row=2, column=1, sticky="w")
            tk.Label(self.dynamic_frame, text="Y Offset:").grid(row=2, column=2, sticky="w", padx=(15, 0))
            self.dy_var = tk.StringVar(value=str(initial.get("dy", 0)))
            tk.Entry(self.dynamic_frame, textvariable=self.dy_var, width=6).grid(row=2, column=3, sticky="w")

        elif step_type == "move":
            tk.Label(self.dynamic_frame, text="X Offset:").grid(row=0, column=0, sticky="w")
            self.dx_var = tk.StringVar(value=str(initial.get("dx", 0)))
            tk.Entry(self.dynamic_frame, textvariable=self.dx_var, width=6).grid(row=0, column=1, sticky="w")
            tk.Label(self.dynamic_frame, text="Y Offset:").grid(row=0, column=2, sticky="w", padx=(15, 0))
            self.dy_var = tk.StringVar(value=str(initial.get("dy", 0)))
            tk.Entry(self.dynamic_frame, textvariable=self.dy_var, width=6).grid(row=0, column=3, sticky="w")

        elif step_type == "scroll":
            tk.Label(self.dynamic_frame, text="Amount (+ up / - down):").grid(row=0, column=0, sticky="w")
            self.amount_var = tk.StringVar(value=str(initial.get("amount", -500)))
            tk.Entry(self.dynamic_frame, textvariable=self.amount_var, width=8).grid(row=0, column=1, sticky="w", padx=5)

        elif step_type == "type":
            tk.Label(self.dynamic_frame, text="Text to type:").grid(row=0, column=0, sticky="w")
            self.text_var = tk.StringVar(value=initial.get("text", ""))
            tk.Entry(self.dynamic_frame, textvariable=self.text_var, width=30).grid(row=0, column=1, columnspan=3, sticky="w", padx=5)

    def _on_save(self):
        step_type = self.LABEL_TYPES[self.type_var.get()]

        if step_type == "image" and self.image_var.get() == "(no images captured yet)":
            messagebox.showerror(
                "No image selected", "Capture at least one image in the Capture Images tab first.", parent=self,
            )
            return

        try:
            step = {
                "type": step_type,
                "pre_sleep": float(self.pre_sleep_var.get() or 0),
                "post_sleep": float(self.post_sleep_var.get() or 0),
            }
            if step_type == "image":
                step["image"] = self.image_var.get()
                step["action"] = "click" if self.action_var.get() == "Click" else "move"
                step["dx"] = int(self.dx_var.get() or 0)
                step["dy"] = int(self.dy_var.get() or 0)
            elif step_type == "move":
                step["dx"] = int(self.dx_var.get() or 0)
                step["dy"] = int(self.dy_var.get() or 0)
            elif step_type == "scroll":
                step["amount"] = int(self.amount_var.get() or 0)
            elif step_type == "type":
                step["text"] = self.text_var.get()
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Numeric fields must contain whole or decimal numbers.", parent=self,
            )
            return

        if self.on_save:
            self.on_save(step)
        self.destroy()


class ImageSavingButton:
    """A button that saves the current clipboard image to pics/ and shows a thumbnail preview."""

    def __init__(self, button_label, master, image_name, row=0, column=0):
        self.image_name = image_name
        self.master = master

        self.button = tk.Button(master, text=button_label, command=self.grab_image)
        self.button.grid(row=row, column=column, padx=5, pady=5, sticky="ew")

        self.thumbnail_label = tk.Label(master)
        self.thumbnail_label.grid(row=row, column=column + 1, padx=5, pady=5)

        self.update_thumbnail()

    def grab_image(self):
        try:
            image = ImageGrab.grabclipboard()
            if image is None:
                print("No image found in clipboard. Please copy an image first.")
                return

            os.makedirs("pics", exist_ok=True)
            image.save(f"pics/{self.image_name}", "PNG")
            print("Image saved successfully.")
            self.update_thumbnail()
        except Exception as e:
            print(f"Error: {e}. Please ensure the path exists and is accessible.")

    def update_thumbnail(self):
        image_path = f"pics/{self.image_name}"
        if not os.path.exists(image_path):
            self.thumbnail_label.config(image='', text="")
            return

        try:
            img = Image.open(image_path)
            img.thumbnail(THUMBNAIL_SIZE)
            self.tk_img = ImageTk.PhotoImage(img)
            self.thumbnail_label.config(image=self.tk_img)
            self.thumbnail_label.image = self.tk_img  # Prevent garbage collection
        except Exception:
            self.thumbnail_label.config(image='', text="Err")


if __name__ == "__main__":
    POItemSelectorApp()
