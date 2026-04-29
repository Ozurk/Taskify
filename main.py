import tkinter as tk
import pyautogui
from PIL import Image, ImageTk, ImageGrab
import time
import os

class POItemSelectorApp:

    sleep_time = 0.4
    confidence = .75

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PO Item Selector")
        self.root.geometry("600x600")

        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        settings_frame = tk.Frame(self.root, relief=tk.RIDGE, borderwidth=2)
        settings_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        # Number of buttons slider
        tk.Label(settings_frame, text="Number of Save Image Buttons").pack(pady=(10, 0))
        self.button_count_var = tk.IntVar(value=6)
        button_count_slider = tk.Scale(
            settings_frame, from_=1, to=10, orient=tk.HORIZONTAL,
            variable=self.button_count_var, command=self.on_button_count_change
        )
        button_count_slider.pack(pady=5, fill="x")

        # Confidence slider
        tk.Label(settings_frame, text="Confidence").pack(pady=(10, 0))
        self.confidence_var = tk.DoubleVar(value=self.confidence)
        confidence_slider = tk.Scale(settings_frame, from_=0.5, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.confidence_var)
        confidence_slider.pack(pady=5, fill="x")

        # Speed (Sleep Time) slider
        tk.Label(settings_frame, text="Speed (Sleep Time)").pack(pady=(10, 0))
        self.sleep_time_var = tk.DoubleVar(value=self.sleep_time)
        speed_slider = tk.Scale(settings_frame, from_=0.01, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.sleep_time_var)
        speed_slider.pack(pady=5, fill="x")

        # Scroll distance slider
        tk.Label(settings_frame, text="Scroll Distance").pack(pady=(10, 0))
        self.scroll_distance_var = tk.IntVar(value=25)
        scroll_slider = tk.Scale(settings_frame, from_=1, to=200, orient=tk.HORIZONTAL, variable=self.scroll_distance_var)
        scroll_slider.pack(pady=5, fill="x")

        tk.Button(settings_frame, text="Apply Settings", command=self.apply_settings).pack(pady=20)

        # Create and place buttons in a grid
        self.save_buttons = []
        self.main_frame = main_frame
        self.update_buttons(self.button_count_var.get(), main_frame)

        execute_button = tk.Button(main_frame, text="Execute", command=self.execute_script)
        execute_button.grid(row=11, column=0, columnspan=2, pady=20, sticky="ew")

        for r in range(12):
            main_frame.rowconfigure(r, weight=1)
        for c in range(2):
            main_frame.columnconfigure(c, weight=1)

        self.root.mainloop()

    def on_button_count_change(self, event=None):
        count = self.button_count_var.get()
        self.update_buttons(count, self.main_frame)

    def update_buttons(self, count, main_frame):
        # Clear existing buttons
        for button in self.save_buttons:
            button.button.destroy()
            button.thumbnail_label.destroy()
        self.save_buttons = []
        # Create new buttons
        for i in range(count):
            row = i
            col = 0
            btn = ImageSaving_Button(f"Save Image{i+1}", main_frame, f"Image{i+1}.png", row=row, column=col)
            self.save_buttons.append(btn)

    def apply_settings(self):
        self.confidence = self.confidence_var.get()
        self.sleep_time = self.sleep_time_var.get()
        self.scroll_distance = self.scroll_distance_var.get()
        print(f"Settings applied: confidence={self.confidence}, sleep_time={self.sleep_time}, scroll_distance={self.scroll_distance}")

    def execute_script(self):
        # Click on the first 3 images in a row, with 1 second delay between each
        for x in range(3000):
            # STEP1
            self.move_to_image("Image1.png")
            pyautogui.moveRel(-18, 50, duration=0.5)
            pyautogui.click()
            time.sleep(.5)
            # STEP 2
            self.click_image2()
            time.sleep(.5)
            # Step 3
            self.move_to_image("Image3.png")
            pyautogui.moveRel(0, 50, duration=0.5)
            pyautogui.click()
            time.sleep(1)

            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'x')

            #Step 4
            pyautogui.scroll(-100)
            self.move_to_image("Image4.png")
            pyautogui.moveRel(0, 50, duration=0.5)
            pyautogui.click()
            time.sleep(.5)
            # step 5
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey("backspace")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(.5)
            pyautogui.scroll(1000)

            # Step 6
            self.click_image5()
            time.sleep(.5)

            # Step 7
            self.click_image6()
            time.sleep(6)
            
            

    def click_image1(self):
        image_path = "pics/Image1.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x , y, duration=0.5)
                pyautogui.click()
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")

    def click_image2(self):
        image_path = "pics/Image2.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")

    def click_image3(self):
        image_path = "pics/Image3.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
                time.sleep(self.sleep_time)
                
                
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")
    
    def click_image4(self):
        image_path = "pics/Image4.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")
    
    def click_image5(self):
        image_path = "pics/Image5.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")
        
    def click_image6(self):
        image_path = "pics/Image6.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")
        
    def click_image7(self):
        image_path = "pics/Image7.png"
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving and clicking.")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")
    
    def move_to_image(self, image_name):
        image_path = "pics/" + image_name
        print(f"Looking for {image_path}...")
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=self.confidence)
            if location:
                x, y = pyautogui.center(location)
                print(f"Found {image_path} at ({x}, {y}). Moving.")
                pyautogui.moveTo(x, y, duration=0.5)
            else:
                print(f"{image_path} not found on screen.")
        except pyautogui.FailSafeException:
            print("PyAutoGUI fail-safe triggered. Exiting.")
            quit()
        except Exception as e:
            print(f"Error: {e}")
    


class ImageSaving_Button():
    def __init__(self, button_label, master, image_name, row=0, column=0):
        self.image_name = image_name
        self.master = master

        # Button to save image from clipboard
        self.button = tk.Button(master, text=button_label, command=self.grab_image)
        self.button.grid(row=row, column=column, padx=5, pady=5, sticky="ew")

        # Thumbnail label (initially empty)
        self.thumbnail_label = tk.Label(master)
        self.thumbnail_label.grid(row=row, column=column+1, padx=5, pady=5)

        # Try to load and display the thumbnail if it exists
        self.update_thumbnail()

    def grab_image(self):
        try:
            image = ImageGrab.grabclipboard()
            if image is not None:
                # Ensure the pics directory exists
                os.makedirs("pics", exist_ok=True)
                image.save("pics/" + self.image_name, "PNG")
                print("Image saved successfully.")
                self.update_thumbnail()
            else:
                print("No image found in clipboard. Please copy an image first.")
        except Exception as e:
            print(f"Error: {e}. Please ensure the path exists and is accessible.")

    def update_thumbnail(self):
        image_path = "pics/" + self.image_name
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail((70, 70))
                self.tk_img = ImageTk.PhotoImage(img)
                self.thumbnail_label.config(image=self.tk_img)
                self.thumbnail_label.image = self.tk_img  # Prevent garbage collection
            except Exception as e:
                self.thumbnail_label.config(image='', text="Err")
        else:
            self.thumbnail_label.config(image='', text="")

if __name__ == "__main__":
    app = POItemSelectorApp()
