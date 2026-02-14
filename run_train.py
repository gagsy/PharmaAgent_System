from ultralytics import YOLO
import torch

def train_pharma_brain():
    # 1. Clear memory before starting
    torch.cuda.empty_cache()
    
    model = YOLO('yolov8n.pt') 

    # 2. STRATEGIC REDUCTIONS
    model.train(
        data='dataset/data.yaml', 
        epochs=100,               
        imgsz=416,                # REDUCE from 640 to 416 (Massive VRAM savings)
        batch=4,                  # REDUCE from 8 to 4
        device=0,       
        workers=0,                # REDUCE to 0 to save system RAM/VRAM overhead
        amp=False,                # DISABLE AMP as suggested by your WARNING log
        project='runs/pharma',    
        name='exp_final_attempt',
        close_mosaic=0            # Disable heavy augmentation to save memory
    )

if __name__ == '__main__':
    train_pharma_brain()