import streamlit as st
import os
import cv2
import json
import sys
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import pathlib

# 1. CACHED MODEL LOADER
@st.cache_resource
def load_yolo_model(model_path):
    """Loads model once into RAM for immediate access"""
    model = YOLO(model_path, task='detect')
    model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
    return model

class VisionAgent:
    def __init__(self):
        self.project_root = pathlib.Path(__file__).parent.parent.parent
        model_path = os.path.join(self.project_root, "models", "best.pt")
        
        self.model = load_yolo_model(model_path)
        self.model_names = self.model.names
        
        # Mapping for the Dropdown names to YOLO Numeric IDs
        self.name_to_id = {v: k for k, v in self.model_names.items()}
        
        self.frame_count = 0
        self.last_id = "none"
        self.last_count = 0
        
        self.med_metadata = {
            "drug_crocin_advance": {
                "name": "Crocin Advance",
                "dose": "500mg",
                "warnings": "Fast-absorbing paracetamol; do not exceed 4000mg/day."
            },
            "drug_paracetamol_650": {
                "name": "Paracetamol (Dolo 650)",
                "dose": "650mg",
                "warnings": "Leave at least 4-6 hours between doses."
            }
        }

    def _draw_outlined_text(self, img, text, pos, color):
        x, y = pos
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

    def _preprocess_frame(self, frame):
        # Ensure frame is in BGR for YOLO processing
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def analyze_frame(self, frame, target_id):
        if frame is None:
            return {"detected_id": "none", "current_count": 0, "match_status": "ERROR"}
        
        self.frame_count += 1
        processed_frame = self._preprocess_frame(frame)
        annotated_frame = processed_frame.copy()
        
        # Cache results for skipped frames to prevent lag
        if self.frame_count % 3 != 0:
            return {
                "detected_id": self.last_id,
                "current_count": self.last_count,
                "annotated_frame": cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                "match_status": "SKIPPED"
            }

        try:
            # PERFORMANCE OPTIMIZATION: Filter by class ID
            target_class_id = self.name_to_id.get(target_id)
            
            if target_class_id is not None:
                # Model strictly looks ONLY for the selected medicine
                results = self.model(processed_frame, classes=[target_class_id], conf=0.45, verbose=False, imgsz=640)
            else:
                results = self.model(processed_frame, conf=0.45, verbose=False, imgsz=640)

            current_count = 0
            detected_id = "none"
            conf = 0.0

            for r in results:
                if r.boxes:
                    current_count = len(r.boxes)
                    box = r.boxes[0] 
                    detected_id = self.model_names.get(int(box.cls[0]), "Unknown")
                    conf = float(box.conf[0])

                    is_match = (detected_id == target_id)
                    color = (0, 200, 0) if is_match else (0, 0, 200)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 4)
                    self._draw_outlined_text(annotated_frame, f"{detected_id} ({conf:.1%})", (x1, y1 - 10), color)
                    break

            med_info = self.med_metadata.get(detected_id, {"dose": "N/A", "warnings": "No safety data available."})
            self.last_id, self.last_count = detected_id, current_count

            return {
                "detected_id": detected_id,
                "current_count": current_count,
                "dose": med_info["dose"],
                "warnings": med_info["warnings"],
                "annotated_frame": cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB),
                "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH"
            }
        except Exception as e:
            return {"detected_id": "none", "current_count": 0, "annotated_frame": frame}