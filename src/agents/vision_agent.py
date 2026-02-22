import streamlit as st
import os
import cv2
import numpy as np
from ultralytics import YOLO
import pathlib

@st.cache_resource
def load_yolo_model(model_path):
    # Strictly using YOLO with the ONNX backend as per your Dockerfile
    model = YOLO(model_path, task='detect')
    # Warm-up with a blank frame to prevent lag on first scan
    model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
    return model

class VisionAgent:
    def __init__(self):
        # According to your Dockerfile, the model is at /app/models/besttwo.onnx
        # We use a dynamic check to work both locally and in Docker
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = pathlib.Path(self.base_dir).parent.parent
        
        # Priority 1: Docker path | Priority 2: Local path
        model_path = "/app/models/besttwo.onnx"
        if not os.path.exists(model_path):
            model_path = os.path.join(self.project_root, "models", "besttwo.onnx")

        self.model = load_yolo_model(model_path)
        self.model_names = self.model.names
        
        # Optimization: Map names to IDs for class filtering
        self.name_to_id = {v: k for k, v in self.model_names.items()}
        
        self.frame_count = 0
        self.last_id = "none"
        self.last_count = 0

    def analyze_frame(self, frame, target_id):
        if frame is None:
            return {"detected_id": "none", "current_count": 0, "match_status": "ERROR"}
        
        self.frame_count += 1
        
        # FIX: WebRTC gives RGB. YOLO ONNX needs BGR for correct medicine colors.
        processed_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        annotated_frame = processed_frame.copy()
        
        # Performance: Skip frames to maintain high FPS on the web
        if self.frame_count % 3 != 0:
            return {
                "detected_id": self.last_id,
                "current_count": self.last_count,
                "annotated_frame": cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                "match_status": "SKIPPED"
            }

        try:
            # OPTIMIZATION: Tell YOLO to only look for the medicine selected in main.py
            target_class_id = self.name_to_id.get(target_id)
            
            if target_class_id is not None:
                # This classes filter prevents 'Traffic Light' detections
                results = self.model(processed_frame, classes=[target_class_id], conf=0.45, verbose=False)
            else:
                results = self.model(processed_frame, conf=0.45, verbose=False)

            current_count = 0
            detected_id = "none"

            for r in results:
                if r.boxes:
                    current_count = len(r.boxes)
                    box = r.boxes[0]
                    detected_id = self.model_names.get(int(box.cls[0]), "Unknown")
                    conf = float(box.conf[0])

                    # Color logic: Green if matched, Red if mismatch
                    is_match = (detected_id == target_id)
                    color = (0, 255, 0) if is_match else (0, 0, 255)
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
                    
                    label = f"{detected_id} {conf:.0%}"
                    cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    break

            self.last_id, self.last_count = detected_id, current_count

            return {
                "detected_id": detected_id,
                "current_count": current_count,
                "annotated_frame": cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH"
            }
        except Exception:
            return {"detected_id": "none", "current_count": 0, "annotated_frame": frame}