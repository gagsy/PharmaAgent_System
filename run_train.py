from ultralytics import YOLO
import torch

def train_pharma_brain():
    # 1. Clear memory before starting
    torch.cuda.empty_cache()
    
    # Using the latest YOLOv11 nano for best performance
    model = YOLO('yolo11n.pt') 

    # 2. STRATEGIC AUGMENTATION FOR MEDICINE DETECTION
    model.train(
        data='dataset/data.yaml', 
        epochs=100,               # 100 epochs is vital for small datasets
        imgsz=640,                # INCREASED to 640 to capture tiny pill text
        batch=4,                  # Keep low for your GTX 1660 Ti VRAM
        device=0,       
        workers=0,                
        amp=False,                # Keep disabled for 1660 Ti stability
        project='runs/pharma',    
        name='exp_augmented_final',
        
        # --- THE MEDICINE-FIXER SETTINGS ---
        augment=True,             # Enable standard variations
        hsv_h=0.015,              # Shifts colors (detects Crocin even in yellow light)
        hsv_s=0.7,                # Changes saturation (detects faded strips)
        hsv_v=0.4,                # Changes brightness (detects strips in shadows)
        degrees=30.0,             # Rotates strips (detects them at any angle)
        translate=0.1,            # Moves the drug around the frame
        scale=0.5,                # Simulates the drug being far or near the camera
        fliplr=0.5,               # Horizontal flip
        mosaic=1.0,               # Mixes 4 images into 1 (Best for small pills)
        mixup=0.1,                # Blends images (prevents the model from "memorizing")
        copy_paste=0.1            # Pastes pills onto different backgrounds
    )

if __name__ == '__main__':
    train_pharma_brain()