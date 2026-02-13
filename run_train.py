from ultralytics import YOLO
import torch

def train_pharma_brain():
    # 1. Clear GPU cache before starting
    torch.cuda.empty_cache()
    
    # 2. Load the model
    model = YOLO('yolov8n.pt') 

    # 3. Start GPU Training with safe memory limits
    model.train(
        data='dataset/data.yaml', 
        epochs=100,               
        imgsz=640,                
        device=0,       
        # Change batch from -1 to 8 or 4 to stay within 6GB VRAM
        batch=8,                  
        workers=2,                # Lower workers reduces CPU/RAM strain
        project='runs/pharma',    
        name='exp_gpu_fixed',
        amp=True,                 # Automatic Mixed Precision (saves VRAM)
        cache=False               # Set to False if you still get OOM
    )

if __name__ == '__main__':
    train_pharma_brain()