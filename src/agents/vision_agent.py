from ultralytics import YOLO
import os

class VisionAgent:
    def __init__(self):
        """
        Initializes the YOLO model. 
        For the demo, we use yolov8n.pt, but a buyer expects 
        a path to a custom 'best.pt' trained on pill datasets.
        """
        # Load the model (ensure the .pt file is in your root or models folder)
        self.model = YOLO('yolov8n.pt') 

    def analyze_pill(self, image_path):
        """
        Performs inference on the scanned image and extracts the 
        most likely medication ID.
        """
        try:
            # 1. Run Inference
            results = self.model(image_path, conf=0.5) # Set confidence threshold to 50%
            
            # 2. Parse Results
            for result in results:
                if len(result.boxes) > 0:
                    # In a real setup, you'd map result.boxes.cls to your inventory IDs
                    # For now, we simulate detecting a valid pill from your data/inventory.json
                    detected_class_index = int(result.boxes.cls[0])
                    
                    # Log for debugging (visible in Streamlit Cloud logs)
                    print(f"AI Detected Class Index: {detected_class_index}")
                    
                    return {
                        "status": "SUCCESS",
                        "detected_pill_id": "pill_001", # Mapping logic goes here
                        "confidence": float(result.boxes.conf[0])
                    }
            
            # 3. Fallback for no detection
            return {
                "status": "UNKNOWN",
                "detected_pill_id": "unknown",
                "confidence": 0.0
            }
            
        except Exception as e:
            # Defensive handling to prevent Orchestrator crashes
            return {
                "status": "ERROR",
                "msg": f"Vision Engine Failure: {str(e)}"
            }