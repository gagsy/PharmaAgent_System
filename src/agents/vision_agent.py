import streamlit as st
import os
import cv2
import json
import sys
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import pathlib


@st.cache_resource
def load_yolo_model(model_path):
    """Loads model into RAM once and shares it across all reruns"""
    return YOLO(model_path, task='detect')

def draw_ar_corners(self, img, box, color, thickness=2, length=20):
    """Draws AR-style corner brackets around a detected object"""
    x1, y1, x2, y2 = box
    # Top Left
    cv2.line(img, (x1, y1), (x1 + length, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + length), color, thickness)
    # Top Right
    cv2.line(img, (x2, y1), (x2 - length, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + length), color, thickness)
    # Bottom Left
    cv2.line(img, (x1, y2), (x1 + length, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - length), color, thickness)
    # Bottom Right
    cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)

    
class VisionAgent:
    def __init__(self):
        self.model = None
        self.model_loaded_from = None
        
        # Absolute project root discovery
        self.project_root = pathlib.Path(__file__).parent.parent.parent
        
        # Priority paths for Docker, Local (XAMPP), and Streamlit Cloud
        model_paths = [
            "/app/models/best.onnx", # Docker Prod
            r"C:\xampp\htdocs\PharmaAgent_System\runs\detect\runs\pharma\exp_augmented_final\weights\best.onnx", # Local Windows
            os.path.join(self.project_root, "models/best.onnx"), # Git/Cloud
            "models/best.onnx"
        ]
        
        for path in model_paths:
            if os.path.exists(path):
                try:
                    self.model = load_yolo_model(path)
                    self.model_loaded_from = path
                    print(f"✅ SUCCESS: Loaded model from {path}", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"❌ FAILED to load {path}: {e}", file=sys.stderr)
        
        # Fallback logic
        if self.model is None:
            try:
                self.model = load_yolo_model("yolo11n.pt")
                self.model_loaded_from = "yolo11n.pt (FALLBACK)"
            except Exception as e:
                raise RuntimeError("No YOLO model found. Ensure medicine_v1.onnx is in /models/")
            
        self.model_names = self.model.names 
        
        if os.environ.get('STREAMLIT_SERVER_PORT'):
            self.history_file = "/tmp/audit_trail.csv"
        else:
            self.history_file = os.path.join(self.project_root, "data/logs/audit_trail.csv")
        
        self._init_csv()
    
    def _init_csv(self):
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            if not os.path.exists(self.history_file):
                with open(self.history_file, "w", encoding='utf-8') as f:
                    f.write("status,message,timestamp,model_source,confidence\n")
        except Exception as e:
            print(f"❌ CSV INIT ERROR: {e}", file=sys.stderr)

    def _preprocess_frame(self, frame):
        """Fixes Blue-appearing-Yellow issue by converting RGB to BGR"""
        if frame is None:
            return None
        # WebRTC provides RGB; OpenCV/YOLO expects BGR
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def analyze_frame(self, frame, target_id):
        if frame is None:
            return {"detected_id": "none", "confidence": 0.0, "match_status": "ERROR"}
        
        frame = self._preprocess_frame(frame)
        
        try:
            # We remove classes=[0,1,2,3,4] to ensure it uses your custom classes
            results = self.model(frame, conf=0.45, verbose=False)
        except Exception as e:
            return {"detected_id": "none", "confidence": 0.0, "match_status": "ERROR"}
        
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

                    # Step 3: Align and Match Logic
                    # Compare camera detection to the dropdown selection (target_id)
                    is_match = (detected_id == target_id)
                    
                    # Green Box (0, 255, 0) for match, Red Box (0, 0, 255) for mismatch
                    box_color = (0, 255, 0) if is_match else (0, 0, 255)
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 4)
                    
                    # High-visibility label
                    label_text = f"{detected_id} ({conf:.1%})"
                    cv2.putText(annotated_frame, label_text, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                    
                    # Step 4: Verified Detections (>80% confidence)
                    if conf > 0.80:
                        # Human-friendly messages for the Audit Ledger
                        status = "✅ VERIFIED" if is_match else "❌ MISMATCH"
                        msg = f"Correct: {detected_id}" if is_match else f"Alert! Found {detected_id} instead of {target_id}"
                        
                        try:
                            # Write exactly 4 columns to match the main.py UI
                            with open(self.history_file, "a", encoding='utf-8') as f:
                                f.write(f"{status},{msg},{timestamp},{conf:.2%}\n")
                                f.flush() # Force write to disk immediately
                        except Exception as e:
                            print(f"❌ LOG ERROR: {e}", file=sys.stderr)
                    
                    # Process only the top detection per frame
                    break

                
        return {
            "detected_id": detected_id,
            "confidence": conf,
            "annotated_frame": annotated_frame,
            "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH",
            "model_source": self.model_loaded_from
        }


        