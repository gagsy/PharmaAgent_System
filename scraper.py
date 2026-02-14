import json
import os
import shutil
import time
import re
from pathlib import Path
from bing_image_downloader import downloader

# --- CRITICAL FIX FOR WINDOWS ---
Path.isdir = lambda self: os.path.isdir(self) # Fixes Path object bug

# --- CONFIGURATION ---
BASE_IMG_DIR = "dataset/images/train"
BASE_LBL_DIR = "dataset/labels/train"
TEMP_DIR = "dataset/temp_download"

def sanitize_folder_name(name):
    """Removes all Windows illegal characters: < > : " / \ | ? *"""
    return re.sub(r'[<>:"/\\|?*]', ' ', name).strip()

def setup_environment():
    """Safely cleans directories."""
    print("Setting up folders...")
    for p in [BASE_IMG_DIR, BASE_LBL_DIR, TEMP_DIR]:
        if os.path.exists(p):
            try: shutil.rmtree(p)
            except: pass
        os.makedirs(p, exist_ok=True)

def move_and_label(query_folder, drug_key, class_index):
    """Unique rename and YOLO label generation."""
    if not os.path.exists(query_folder): return
    files = [f for f in os.listdir(query_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for i, filename in enumerate(files):
        unique_name = f"{drug_key}_{i+1}{os.path.splitext(filename)[1]}"
        try:
            shutil.move(os.path.join(query_folder, filename), os.path.join(BASE_IMG_DIR, unique_name))
            with open(os.path.join(BASE_LBL_DIR, f"{drug_key}_{i+1}.txt"), "w") as f:
                f.write(f"{class_index} 0.5 0.5 0.8 0.8")
        except: continue

def collect_images(drug_data):
    class_names = list(drug_data.keys())
    for idx, key in enumerate(class_names):
        info = drug_data[key]
        # Sanitize for folder creation safety
        query = sanitize_folder_name(f"{info['name']} {info['dose']} medicine packaging")
        print(f"[{idx+1}/{len(class_names)}] Downloading: {key}")
        try:
            downloader.download(query, limit=15, output_dir=TEMP_DIR, adult_filter_off=True, force_replace=True, verbose=False)
            move_and_label(os.path.join(TEMP_DIR, query), key, idx)
        except Exception as e: print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    with open('data/inventory.json', 'r') as f: data = json.load(f)
    setup_environment()
    collect_images(data)
    print("\n✅ DATA COLLECTION DONE. RUN 'py run_train.py' NOW!")