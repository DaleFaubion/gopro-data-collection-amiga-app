import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
import time
import threading

from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

# ========================================
# Image moving methods
# ========================================
def get_exif_datetime(image_path):
    """
        Extracts the EXIF metadata from the image, returning
        datetime in YYY:MM:DD HH:MM:SS format
        @Return: DateTime if found, None if not found
    """
    try:
        img = Image.open(image_path)
        exif_data = img.getexif()

        if not exif_data:
            return None
        
        dt_value = None

        # Iterate through all tags, looking for DateTime
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)

            # Depending on if the image has been edited, this field can be
            # named differently, or on other cameras perhaps.
            if tag_name == "DateTimeOriginal":
                dt_value = value
                break
            elif tag_name == "DateTime" and dt_value is None:
                dt_value = value

        if dt_value:
            return datetime.strptime(dt_value, "%Y:%m:%d %H:%M:%S")
            
    except Exception as e:
        print(f"EXIF error on {image_path}: {e}")
    
    return None

def process_image(image_path, base_output_dir, cam_num, date):
    """
        Processes an image's EXIF data, renaming the file to reflect
        the date and camera on which it was captured, putting it in
        the correct Date/CamNum/img.JPEG structure for VineTech.
        Returns 0 if no EXIF data, 1 if there is and it was processed
    """
    #print(f"Processing: {image_path}")

    # Extract datetime from EXIF data
    dt = get_exif_datetime(image_path)

    if dt is None:
        print(f"No EXIF date for {image_path}")
        return 0
    
    # Build new output folder: Date/CamNum
    output_dir = os.path.join(base_output_dir, date, cam_num)
    os.makedirs(output_dir, exist_ok=True)

    # Filename format: YYYY-MM-DD_HH:MM:SS_CamNum.JPEG
    base_name = f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}_{cam_num}"
    ext = ".JPEG"

    new_path = os.path.join(output_dir, base_name + ext)

    # Avoid overwritting just in case
    counter = 1
    while os.path.exists(new_path):
        new_path = os.path.join(output_dir, f"{base_name}_{counter}{ext}")
        counter += 1
    # Move and rename the file
    shutil.move(image_path, new_path)
    #print(f"Moved -> {new_path}")
    return 1

class App:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.root.title("GoPro Image Mover")
        self.root.geometry("800x600")
        self.root.config(bg="lightgrey")

        # ==========================================
        # Instructions
        # ==========================================
        self.instr_frame = tk.Frame(root)
        self.instr_frame.pack(
            padx=20, 
            pady=20, 
            fill=tk.X
        )
        # Instructions label
        self.instructions = tk.Label(
            self.instr_frame,
            text=(
                "GoPro Image Mover\n\n"
                "Insert the SD card in to the dongle.\n"
                "Select the input directory containing the GoPro images.\n"
                "Select the output directory where the organized images "
                "should be placed.\n"
                "Enter the date and select the camera number.\n\n"
                "Click Submit to start moving images."
            ),
            justify=tk.LEFT
        )
        self.instructions.pack(anchor="w")

        # ==========================================
        # Input
        # ==========================================
        self.inputs_frame = tk.Frame(root)
        self.inputs_frame.pack(
            padx=20, 
            pady=10,
            fill=tk.X
        )

        # Input Dir Entry
        self.input_dir_label = tk.Label(self.inputs_frame, text="Input Root Directory:")
        self.input_dir_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        self.input_dir_entry = tk.Entry(self.inputs_frame, width=60)
        self.input_dir_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=8,
            sticky="ew"
        )

        # ------------------------------------------
        # Output directory
        # ------------------------------------------

        self.output_dir_label = tk.Label(
            self.inputs_frame,
            text="Output Root Directory:"
        )
        self.output_dir_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        self.output_dir_entry = tk.Entry(
            self.inputs_frame,
            width=60
        )
        self.output_dir_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=8,
            sticky="ew"
        )


        # ------------------------------------------
        # Date
        # ------------------------------------------

        self.date_label = tk.Label(
            self.inputs_frame,
            text="Date (YYYY-MM-DD):"
        )
        self.date_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        self.date_entry = tk.Entry(
            self.inputs_frame,
            width=20
        )
        self.date_entry.grid(
            row=2,
            column=1,
            sticky="w",
            padx=5,
            pady=8
        )


        # ------------------------------------------
        # Camera selection
        # ------------------------------------------

        self.cam_label = tk.Label(
            self.inputs_frame,
            text="Camera:"
        )
        self.cam_label.grid(
            row=3,
            column=0,
            sticky="w",
            padx=5,
            pady=8
        )

        self.var = tk.IntVar(
            value=1
        )

        self.camera_frame = tk.Frame(
            self.inputs_frame
        )
        self.camera_frame.grid(
            row=3,
            column=1,
            sticky="w",
            padx=5,
            pady=8
        )

        cam_values = {
            "Cam 1": 1,
            "Cam 2": 2,
            "Cam 3": 3,
            "Cam 4": 4,
        }

        for text, value in cam_values.items():

            tk.Radiobutton(
                self.camera_frame,
                text=text,
                variable=self.var,
                value=value,
            ).pack(
                side=tk.LEFT,
                padx=10
            )


        # Make column 1 expand when the window grows
        self.inputs_frame.columnconfigure(
            1,
            weight=1
        )


        # ==========================================
        # Submit
        # ==========================================

        self.submit_button = tk.Button(
            root,
            text="Submit",
            command=self.submit,
            width=15
        )
        self.submit_button.pack(
            pady=20
        )

        # ==========================================
        # Progress
        # ==========================================

        self.progress = ttk.Progressbar(
            root,
            orient="horizontal",
            length=600,
            mode="determinate"
        )
        self.progress.pack(
            padx=20,
            pady=10
        )

        self.progress_label = tk.Label(
            root,
            text="Ready"
        )
        self.progress_label.pack(
            pady=5
        )


        # ==========================================
        # Status
        # ==========================================

        self.status_label = tk.Label(
            root,
            text="Ready"
        )
        self.status_label.pack(
            pady=10
        )

    # =============================================
    # Submit
    # =============================================
    def submit(self):

        if self.running:
            return

        input_dir = self.input_dir_entry.get()
        output_dir = self.output_dir_entry.get()
        date = self.date_entry.get()
        camera = self.var.get()

        print(f"Input Dir:  {input_dir}")
        print(f"Output Dir: {output_dir}")
        print(f"Date:       {date}")
        print(f"Camera:     {camera}")

        self.status_label.config(
            text=f"Camera {camera} selected"
        )

        # ------------------------------------------
        # Validate input
        # ------------------------------------------
        #TODO: more validation probably
        if not os.path.isdir(input_dir):
            messagebox.showerror(
                "Invalid Input",
                "The input directory does not exist."
            )
            return

        if not output_dir:
            messagebox.showerror(
                "Invalid Input",
                "Please enter an output directory."
            )
            return

        if not date:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a date."
            )
            return

        # -------------------------------
        # Start processing images
        # -------------------------------

        self.running = True
        self.submit_button.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress_label.config(text="Finding images...")
        self.status_label.config(text="Starting...")

        # Run processing in the background so the GUI doesn't freeze
        thread = threading.Thread(
            target=self.move_images,
            args=(
                input_dir,
                output_dir,
                str(camera),
                date
            ),
            daemon=True
        )
        thread.start()


    # ================================
    # Get EXIF date
    # ================================
    def get_exif_datetime(image_path):
        """
            Extracts the EXIF metadata from the image, returning
            datetime in YYY:MM:DD HH:MM:SS format
            @Return: DateTime if found, None if not found
        """
        try:
            with Image.open(image_path) as img:
                exif_data = img.getexif()

                if not exif_data:
                    return None
                
                dt_value = None

                # Iterate through all tags, looking for DateTime
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)

                    # Depending on if the image has been edited, this field can be
                    # named differently, or on other cameras perhaps.
                    if tag_name == "DateTimeOriginal":
                        dt_value = value
                        break
                    elif tag_name == "DateTime" and dt_value is None:
                        dt_value = value

                if dt_value:
                    return datetime.strptime(dt_value, "%Y:%m:%d %H:%M:%S")
                
        except Exception as e:
            print(f"EXIF error on {image_path}: {e}")
        
        return None


    # ===========================================================
    # Process Images, Rename, Move
    # ===========================================================
    def process_image(image_path, base_output_dir, cam_num, date):
        """
            Processes an image's EXIF data, renaming the file to reflect
            the date and camera on which it was captured, putting it in
            the correct Date/CamNum/img.JPEG structure for VineTech.
            @Return: 0 if no EXIF data, 1 if successful processing of image
        """
        #print(f"Processing: {image_path}")

        # Extract datetime from EXIF data
        dt = get_exif_datetime(image_path)

        if dt is None:
            print(f"No EXIF date for {image_path}")
            return 0
        
        # Build new output folder: Date/CamNum
        output_dir = os.path.join(base_output_dir, date, cam_num)
        os.makedirs(output_dir, exist_ok=True)

        # Filename format: YYYY-MM-DD_HH:MM:SS_CamNum.JPEG
        base_name = f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}_{cam_num}"
        ext = ".JPEG"

        new_path = os.path.join(output_dir, base_name + ext)

        # Avoid overwritting just in case
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(output_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        # Move and rename the file
        shutil.move(image_path, new_path)
        #print(f"Moved -> {new_path}")
        return 1


    # ===================================
    # Move Images
    # ===================================
    def move_images(
        self,
        input_dir,
        output_dir,
        cam_num,
        date
    ):
        count = 0
        no_exif = 0
        #TODO: Could change this to actual number, but it took too long to count so I just used an average
        total = 3200
        chunked_progress = 0
        start_time = time.time()

        print(f"Starting to move from {input_dir} to {output_dir}")

        # Walk through all subfolders
        for dir_root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg")):
                    full_path = os.path.join(dir_root, file)
                    was_moved = process_image(full_path, output_dir, cam_num, date)
                    
                    if was_moved == 1:
                        count = count + 1
                    else:
                        no_exif = no_exif + 1
                    

                    ## Every 10%, update user with how much time is left
                    elapsed_time = time.time() - start_time
                    #TODO: Could change to actually check how many there are, but usually around 3100 - 3200
                    percent_done = (count / total) * 100
                    speed = 0
                    if (elapsed_time > 0):
                        speed = elapsed_time / count

                    #TODO: change 321 to the actual number, but its close enough for now.
                    progress = int(count / 321) * 10


                    # --------------------------------
                    # Update GUI
                    # --------------------------------
                    seconds = ((total - count) * speed)
                    minutes = int(seconds / 60)
                    seconds_left = seconds - (minutes * 60)
                    print(f"{(progress):.0f}% Complete Estimated time left: {minutes}:{seconds_left:.0f} minutes ({speed:.2f} per file)")
                    
                    self.root.after(
                        0,
                        self.update_progress,
                        percent_done,
                        count,
                        total,
                        minutes,
                        seconds_left
                    )

        # --------------------------------
        # Finished
        # --------------------------------
        time_passed = time.time() - start_time
        print(f"Time passed: {time_passed}, images moved: {count}")
        if count > 0:
            time_per_image = time_passed / count
            print(f"Time per image: {time_per_image}")

        self.root.after(
            0,
            self.finished,
            count,
            no_exif,
            time_passed
        )

    # =====================================
    # Update Progress
    # =====================================
    def update_progress(
        self,
        percent,
        count,
        total,
        minutes,
        seconds
    ):
        self.progress["value"] = percent
        self.progress_label.config(
            text=(
                f"{count}/{total} ({percent:.1f}%)  "
                f"Estimated time remaining: {minutes}:{seconds:02f}"
            )
        )
        self.status_label.config(text="Moving images...")


    # =====================================
    # Finished
    # =====================================
    def finished(
        self,
        moved,
        no_exif,
        elapsed
    ):
        self.running = False
        self.submit_button.config(state=tk.NORMAL)
        self.progress["value"] = 100

        minutes = int(elapsed / 60)
        seconds = int(elapsed % 60)
        self.progress_label.config(text="Finished!")

        self.status_label.config(
            text=(
                f"Moved: {moved} | "
                f"No EXIF: {no_exif} | "
                f"Time: {minutes}:{seconds:02d}"
            )
        )

        messagebox.showinfo(
            "Complete",
            (
                f"Finished moving images.\n\n"
                f"Images moved: {moved}\n"
                f"Images without EXIF: {no_exif}\n"
                f"Time: {minutes}:{seconds:02d}"
            )
        )



    # ==================================
    # No Images
    # ==================================
    def no_images(self):
        self.running = False
        self.submit_button.config(
            state=tk.NORMAL
        )
        self.progress["value"] = 0
        self.progress_label.config(text="No images found.")
        self.status_label.config(text="Ready")


        messagebox.showwarning("No images, no JPG or JPEG files found")





if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()