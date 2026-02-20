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
    # Warm-up to prevent first-frame lag
    model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
    return model

class VisionAgent:
    def __init__(self):
        self.model = None
        self.project_root = pathlib.Path(__file__).parent.parent.parent
        self.frame_count = 0  # Counter for frame-skipping logic
        
        # 2. MEDICINE METADATA (Dose & Warnings)
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
            },
            "drug_combiflam": {
                "name": "Combiflam",
                "dose": "400mg Ibuprofen / 325mg Paracetamol",
                "warnings": "Take with food; avoid if you have asthma/ulcers."
            },
            "drug_cetirizine": {
                "name": "Cetirizine",
                "dose": "10mg",
                "warnings": "May cause mild drowsiness."
            },
            "drug_gelusil": {
                "name": "Gelusil",
                "dose": "Antacid Tablet",
                "warnings": "Take after meals or at bedtime."
            }
        }

        # Priority model paths
        model_paths = [
            "/app/models/bestperfect.onnx",
            r"C:\xampp\htdocs\PharmaAgent_System\runs\detect\runs\pharma\exp_augmented_final5\weights\best.onnx",
            os.path.join(self.project_root, "models/bestperfect.onnx"),
            "models/bestperfect.onnx"
        ]
        
        for path in model_paths:
            if os.path.exists(path):
                try:
                    self.model = load_yolo_model(path)
                    self.model_loaded_from = path
                    break
                except Exception as e:
                    print(f"❌ Load Error: {e}", file=sys.stderr)
        
        if self.model is None:
            self.model = load_yolo_model("yolo11n.pt")
            
        self.model_names = self.model.names 
        self.history_file = "/tmp/audit_trail.csv" if os.environ.get('STREAMLIT_SERVER_PORT') else os.path.join(self.project_root, "data/logs/audit_trail.csv")
        self._init_csv()

    def _init_csv(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", encoding='utf-8') as f:
                f.write("status,message,timestamp,model_source,confidence\n")

    def _draw_outlined_text(self, img, text, pos, color=(0, 200, 0)):
        """Draws dark green text with a black outline for high visibility"""
        # Black outline (thickness=4)
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
        # Darker Green foreground (thickness=2)
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    def _preprocess_frame(self, frame):
        """Standardizes color and resizes to 640px to stop camera lag"""
        if frame is None: return None
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        h, w = bgr.shape[:2]
        if h > 640:
            bgr = cv2.resize(bgr, (int(w * (640/h)), 640))
        return bgr

    def analyze_frame(self, frame, target_id):
        if frame is None:
            return {"detected_id": "none", "current_count": 0, "match_status": "ERROR"}
        
        # PERFORMANCE: Analyze every 3rd frame to eliminate hang
        self.frame_count += 1
        processed_frame = self._preprocess_frame(frame)
        annotated_frame = processed_frame.copy()
        
        if self.frame_count % 3 != 0:
            return {
                "detected_id": getattr(self, "last_id", "none"),
                "current_count": getattr(self, "last_count", 0),
                "annotated_frame": annotated_frame,
                "match_status": "SKIPPED"
            }

        try:
            results = self.model(processed_frame, conf=0.45, verbose=False, imgsz=640)
            
            # 3. COUNTING LOGIC
            current_count = 0
            detected_id = "none"
            conf = 0.0
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for r in results:
                if r.boxes:
                    current_count = len(r.boxes) # Update Count
                    box = r.boxes[0] # Focus on top detection for metadata
                    detected_id = self.model_names.get(int(box.cls[0]), "Unknown")
                    conf = float(box.conf[0])

                    # Annotation with high-visibility dark outlined text
                    is_match = (detected_id == target_id)
                    color = (0, 200, 0) if is_match else (0, 0, 200) # Darker green/red
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 4)
                    
                    self._draw_outlined_text(annotated_frame, f"{detected_id} ({conf:.1%})", (x1, y1 - 10), color)
                    break

            # 4. METADATA MAPPING (Dose/Warnings)
            med_info = self.med_metadata.get(detected_id, {"dose": "N/A", "warnings": "No safety data available."})
            
            # Cache results for skipped frames
            self.last_id, self.last_count = detected_id, current_count

            return {
                "detected_id": detected_id,
                "current_count": current_count,
                "dose": med_info["dose"],
                "warnings": med_info["warnings"],
                "annotated_frame": annotated_frame,
                "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH"
            }
        except Exception:
            return {"detected_id": "none", "current_count": 0, "annotated_frame": processed_frame}