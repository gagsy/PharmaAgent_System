import json      # Fixed: Added missing import 
import os
import shutil
import time
from bing_image_downloader import downloader

# --- CONFIGURATION ---
BASE_IMG_DIR = "dataset/images/train"
BASE_LBL_DIR = "dataset/labels/train"

def setup_environment():
    """Creates directory structure for images and labels[cite: 64, 109]."""
    print("Setting up folders...")
    for path in [BASE_IMG_DIR, BASE_LBL_DIR]:
        os.makedirs(path, exist_ok=True)

def create_dummy_labels(folder_path, class_index):
    """Generates placeholder labels to satisfy YOLO requirements[cite: 68, 110]."""
    if not os.path.exists(folder_path):
        return
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for img in images:
        label_name = os.path.splitext(img)[0] + ".txt"
        label_path = os.path.join(BASE_LBL_DIR, label_name)
        # YOLO format: <class_id> <x_center> <y_center> <width> <height> [cite: 110]
        with open(label_path, "w") as f:
            f.write(f"{class_index} 0.5 0.5 0.8 0.8")

def collect_images(drug_data):
    """Downloads images and renames folders for mapping[cite: 6, 9, 64]."""
    class_names = list(drug_data.keys())
    for idx, key in enumerate(class_names):
        info = drug_data[key]
        # Added 'packaging' to query for better pharmaceutical results [cite: 111]
        query = f"{info['name']} {info['dose']} medicine packaging"
        print(f"\n[{idx+1}/{len(class_names)}] Processing: {key}")
        
        try:
            downloader.download(
                query, 
                limit=15, 
                output_dir=BASE_IMG_DIR, 
                adult_filter_off=True, 
                force_replace=False, 
                timeout=5,
                verbose=False
            )
            
            # Standardize folder names to match JSON keys [cite: 8, 37, 55]
            query_folder = os.path.join(BASE_IMG_DIR, query)
            target_folder = os.path.join(BASE_IMG_DIR, key)
            
            if os.path.exists(query_folder):
                if os.path.exists(target_folder): 
                    shutil.rmtree(target_folder)
                os.rename(query_folder, target_folder)
                create_dummy_labels(target_folder, idx) # Generate labels [cite: 68, 114]
            
            time.sleep(0.5) # Prevent IP blocking [cite: 114]
        except Exception as e:
            print(f"Error downloading {key}: {e}")

def generate_yaml(class_names):
    """Generates the data.yaml file for YOLO training[cite: 115]."""
    yaml_path = "dataset/data.yaml"
    yaml_content = f"""path: /app/dataset\ntrain: images/train\nval: images/train\n\nnc: {len(class_names)}\nnames: {class_names}"""
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
    print(f"\n✅ Created: {yaml_path}")

if __name__ == "__main__":
    inventory_path = 'data/inventory.json' 
    try:
        with open(inventory_path, 'r') as f:
            data = json.load(f)
        setup_environment()
        collect_images(data)
        generate_yaml(list(data.keys()))
    except FileNotFoundError:
        print(f"Error: {inventory_path} not found!") [cite: 116, 117]