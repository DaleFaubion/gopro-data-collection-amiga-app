"""
    Script to rename GoPro image files that have been processed with their EXIF data
    while the GoPro had a bad datetime (usually due to dying or reseting).
    
    NOTE: When I used it, it was for a few days of collection that Cam 2 had died, so
    you'll have to change the code to reflect which camera had bad datetime.
"""

import os
from datetime import datetime

# Example to start with, since (in theory) the images were captured 
# at the same time, so just change the wrong date by the offset.
cam1_first = "2026-07-15_12-03-39_1.JPEG" # Good
cam2_first = "2016-07-15_11-59-31_2.JPEG" # Bad

# Bad camera directory to change all files in by offset
cam2_dir = "C:\\Users\\daleb\\OneDrive\\Desktop\\GoProData\\2026-07-15\\2"

fmt = "%Y-%m-%d_%H-%M-%S"

# Compute offset to add to the bad images
t1 = datetime.strptime(cam1_first.replace("_1.JPEG", ""), fmt)
t2 = datetime.strptime(cam2_first.replace("_2.JPEG", ""), fmt)

offset = t1 - t2
print("Offset:", offset)

# Rename files with offset
for filename in sorted(os.listdir(cam2_dir)):
    if not filename.endswith(".JPEG"):
        continue

    try:
        # Take off the end, leaving just datetime
        base = filename.replace("_2.JPEG", "")
        old_time = datetime.strptime(base, fmt)

        # Modify old time by offset, correcting it, making new name
        new_time = old_time + offset
        new_name = new_time.strftime("%Y-%m-%d_%H-%M-%S") + "_2.JPEG"

        src = os.path.join(cam2_dir, filename)
        dst = os.path.join(cam2_dir, new_name)

        print(f"{filename} -> {new_name}")
        os.rename(src, dst)

    except Exception as e:
        print("Skipping:", filename, e)