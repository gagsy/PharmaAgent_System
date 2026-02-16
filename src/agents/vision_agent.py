import os
import cv2
import json
from ultralytics import YOLO
from datetime import datetime

class VisionAgent:
    def __init__(self):
        # PROD MODEL RESOLUTION
        # We check the Docker internal path first for your trained weights
        self.prod_path = "/usr/src/app/runs/detect/runs/pharma/exp_augmented_final/weights/best.onnx"
        self.alt_path = "/usr/src/app/models/best.pt"
        
        if os.path.exists(self.prod_path):
            self.model = YOLO(self.prod_path)
            print(f"✅ PROD: Using optimized ONNX model.")
        elif os.path.exists(self.alt_path):
            self.model = YOLO(self.alt_path)
            print(f"✅ PROD: Using PyTorch weights.")
        else:
            print("⚠️ PROD WARNING: Custom model not found. Using base model.")
            self.model = YOLO("yolo11n.pt")
            
        self.model_names = self.model.names 
        # Persistence path synced with Docker volumes
        self.history_file = "/usr/src/app/data/logs/audit_trail.csv"

    def analyze_frame(self, frame, target_id):
        """
        CORE MEDICINE DETECTION: This function is the heartbeat of your system.
        It runs inference and then logs the result to PROD storage.
        """
        # 1. RUN DETECTION
        results = self.model(frame, conf=0.5, verbose=False, classes=[0, 1, 2, 3, 4])
        
        detected_id = "none"
        conf = 0.0
        annotated_frame = frame.copy()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for r in results:
            if len(r.boxes) > 0:
                box = r.boxes[0]
                class_id = int(box.cls[0])
                detected_id = self.model_names.get(class_id, "Unknown")
                conf = float(box.conf[0])

                # 2. MATCH LOGIC: Check if detected medicine matches the selection
                is_match = (detected_id == target_id)
                box_color = (0, 255, 0) if is_match else (0, 0, 255)
                
                # Draw high-visibility boxes for the UI
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 4)
                cv2.putText(annotated_frame, f"{detected_id} {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                
                # 3. PROD LOGGING: Write directly to the persistent CSV
                if conf > 0.70:
                    status = "SAFE" if is_match else "DANGER"
                    msg = f"Verified: {detected_id}" if is_match else f"Mismatch! Detected {detected_id}"
                    
                    try:
                        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                        with open(self.history_file, "a", encoding='utf-8') as f:
                            f.write(f"{status},{msg},{timestamp}\n")
                            f.flush()            # Force write out of buffer
                            os.fsync(f.fileno())  # Force write to Windows disk
                    except Exception as e:
                        print(f"❌ PROD LOG ERROR: {e}")
                break 

        return {
            "detected_id": detected_id,
            "confidence": conf,
            "annotated_frame": annotated_frame,
            "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH"
        }