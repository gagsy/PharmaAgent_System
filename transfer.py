import os
import shutil

# Paths to your current folders
base_path = r"C:\xampp\htdocs\PharmaAgent_System\dataset"
types = ['images', 'labels']

for t in types:
    target_dir = os.path.join(base_path, t, 'train')
    # Walk through every subfolder
    for root, dirs, files in os.walk(target_dir):
        if root == target_dir:
            continue
        for file in files:
            # Move file to the main 'train' folder
            old_path = os.path.join(root, file)
            new_path = os.path.join(target_dir, file)
            shutil.move(old_path, new_path)
    print(f"✅ Finished flattening {t}")