"""
    Script to extract EXIF data from GoPro images and move/rename the files
    based on the creation timestamp.

    To use, point the input_root and ouput_root at where you want it to pull 
    from and move to.
    
    NOTE: Change Constants below for input/output folders, cam_num, date images
    were recorded.
    You'll have to delete the 100GOPRO folders from the DCIM folder of each SD card
    at the moment, that would be easy to fix though. It doesn't break anything that
    I could find, but it keeps it cleaner.
"""

import os
import shutil
import time
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

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
    """
    #print(f"Processing: {image_path}")

    # Extract datetime from EXIF data
    dt = get_exif_datetime(image_path)

    if dt is None:
        print(f"No EXIF date for {image_path}")
        return
    
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

#TODO: Change these to run
input_root = "D:\\DCIM"
output_root = "C:\\Users\\daleb\\OneDrive\\Desktop\\GoProData"
cam_num = "2"
date = "2026-08-26"

count = 0
chunked_progress = 0
start_time = time.time()

print(f"Starting to move from {input_root} to {output_root}")

# Walk through all subfolders
for root, dirs, files in os.walk(input_root):
    for file in files:
        if file.lower().endswith((".jpg", ".jpeg")):
            count = count + 1
            full_path = os.path.join(root, file)
            process_image(full_path, output_root, cam_num, date)

            ## Every 10%, update user with how much time is left
            elapsed_time = time.time() - start_time
            #TODO: Could change to actually check how many there are, but usually around 3100 - 3200
            percent_done = (count / 3200) * 100
            speed = 0
            if (elapsed_time > 0):
                speed = elapsed_time / count

            #TODO: change 321 to the actual number, but its close enough for now.
            progress = int(count / 321) * 10
            if (progress > chunked_progress):
                seconds = ((3200 - count) * speed)
                minutes = int(seconds / 60)
                seconds_left = seconds - (minutes * 60)
                print(f"{(progress):.0f}% Complete Estimated time left: {minutes}:{seconds_left:.0f} minutes ({speed:.2f} per file)")
                chunked_progress = progress


time_passed = time.time() - start_time
print(f"Time passed: {time_passed}, images moved: {count}")
if count > 0:
    time_per_image = time_passed / count
    print(f"Time per image: {time_per_image}")
