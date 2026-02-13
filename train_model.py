from ultralytics import YOLO

# 1. Load a pre-trained base model
model = YOLO('yolov8n.pt') 

# 2. Start Training on your laptop
# 'epochs' is how many times it looks at the data. Use 50 for a quick, good result.
results = model.train(
    data='dataset/data.yaml', 
    epochs=50, 
    imgsz=640, 
    device='cpu' # Use '0' if you have an NVIDIA GPU, otherwise 'cpu'
)


