"""
Downloads timelapse images from a GoPro once connected to the GoPro's WiFi.

TODO:
- Fix OUTPUT_DIR to reflect where we want the images to be stored

Future Plans:
- Make it rename them like the moveImages.py script
- Check to see if any files are already downloaded and skip those, so we have a bit
    of checkpointing instead of downloading all of the same files again.
- Check if there is a more efficient way of doing this script.
"""

import json
import time
from pathlib import Path
import urllib.request

# GoPro default Wi-Fi IP and HTTP server port
GOPRO_IP = "10.5.5.9:8080"
OUTPUT_DIR = Path("./downloaded_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# 1. Fetch SD card media index
print("Fetching media list from GoPro...")
response = urllib.request.urlopen(f"http://{GOPRO_IP}/gopro/media/list")
media_data = json.loads(response.read().decode("utf-8"))

"""
GOPRO JSON codes:
"media" = all media on SD
"d" = directory
"b" = ID of first group member
"l" = ID of last group member
"m" = IDs of deleted members
Filenames for timelapse:
GXXXYYYY.JPG
"XXX" = GroupID, "YYYY" is Group member ID
thus,
100GOPRO contains
{G 002 0963 .JGP} -- {G 002 0977 .JPG} 
 G ggg bbbb .JPG  --  G ggg llll .JPG
== 14 images (since "m" is empty, continuous from "b" to "l")
ex.

{
  "id": "168178003346863224",
  "media": 
  [
    {
      "d": "100GOPRO",
      "fs": [
        {
          "n": "G0020963.JPG",
          "g": "2",
          "b": "963",
          "l": "977",
          "cre": "1786614137",
          "mod": "1786614137",
          "s": "87088964",
          "t": "b",
          "m": []
        }
      ]
    },
    {
      "d": 101GOPRO",
      "fs": [
        {
          "n": ""
          ...
        }
      ]
    }
  ]
}
"""
total_size_mb = 0
filepaths = set()
num_files = 0
file_size_mb = 0
# 2. Get the file list from the latest directory
dirs_JSON = media_data["media"]
print("Found media. Fetching names...")
## For each directory in the JSON, parse the filenames from their groups to get a list 
##    of names
for dir in dirs_JSON:
    folder_name = dir["d"]
    groups = dir["fs"]
    #print(folder_name)
    for group in groups:
        ## If it's not grouped, it won't break.
        ## Timelapse photos are grouped, so we skip pictures/videos
        try:
            group_num = group["g"].zfill(3)
            first_file_num = int(group["b"])
            last_file_num = int(group["l"])

            for file_num in range(first_file_num, last_file_num + 1):
                file_num_pad = str(file_num).zfill(4)

                filename = f"G{group_num}{file_num_pad}.JPG"
                filepath = f"{folder_name}/{filename}"
                #print(filepath)
                filepaths.add(filepath)
                num_files += 1

                ## NOTE: This makes it much slower, but gives you an estimate of size
                ##          if needed
                if (1 == 0):
                    response = urllib.request.urlopen(f"http://10.5.5.9:8080/gopro/media/info?path={filepath}")
                    media_data = json.loads(response.read().decode("utf-8"))
                    file_size_bytes = int(media_data["s"], 0)
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    total_size_mb += file_size_mb
                    print(f"Latest media found: {filename} ({file_size_mb:.2f} MB)")

        except KeyError:
            print(f"No Group ID, skipped picture or video: {folder_name}/{group["n"]}")
        
# Print a rough estimation (On my laptop, average is .5 sec per file)
#TODO: update for the Amiga's time
print(f"Total files to download: {num_files}")
print(f"Estimated Time: {(num_files * .5):.2f} seconds")

files_processed = 1
start_time = time.time()
between_download = start_time
tenth = int(0.1 * num_files) + 1
chunked_progress = 0

## Process all files
for filepath in filepaths:
    # 3. Construct download URL and local destination path
    download_url = f"http://{GOPRO_IP}/videos/DCIM/{filepath}"
    destination = OUTPUT_DIR / filepath.split("/")[0]
    destination.mkdir(exist_ok=True)
    destination = OUTPUT_DIR / filepath

    # 4. Download
    
    #print(f"Downloading: {filepath}")
    #TODO: Check this for speed
    urllib.request.urlretrieve(download_url, destination)

    ## How much time it took
    elapsed_time = time.time() - start_time
    per_file_time = time.time() - between_download
    between_download = time.time()
    percent_done = (files_processed / num_files) * 100
    speed = 0
    if (elapsed_time > 0):
        speed = files_processed / elapsed_time

    ## Every 10%, update user with how much time is left
    progress = int(files_processed / tenth) * 10
    if (progress > chunked_progress):
        print(f"{(progress):.0f}% Complete Estimated time left: {((num_files - files_processed) * speed):.2f} seconds ({speed:.2f})")
        chunked_progress = progress

    files_processed += 1

# TODO WHY IS IT SO SLOW?? - find if WiFi version can change that/how we get requests.
# TODO: make an app to copy the files off micro SD cards

print("-" * 50)
print(f"Download complete!")
print(f"Saved to: {OUTPUT_DIR}")
print(f"Time:     {elapsed_time:.2f} seconds")