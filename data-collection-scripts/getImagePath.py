"""
    Produces a CSV file containing all the names of the image files for a day
    to feed into the tagrows.py file to label row ends.

    NOTE: this is setup for windows, with the \\ folder denoter, but still works
    fine with Linux filesystems.
"""
import os

root = r"c:\\Users\\daleb\\OneDrive\\Desktop\\GoProData\\2026-07-30"
#root = r"/home/dalebyte/remote/2025-07-30"

with open("2026-07-30-ends.csv", "w") as f:
    for dirpath, _, filenames in os.walk(root):
        for file in filenames:
            if file.lower().endswith(".jpeg"):
                full_path = os.path.join(dirpath, file)
                f.write(full_path.replace("\\", "/") + "\n")