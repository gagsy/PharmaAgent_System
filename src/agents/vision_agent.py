import os
import cv2
import json
import sys
import numpy as np
from ultralytics import YOLO
from datetime import datetime

class VisionAgent:
    def __init__(self):
        # PROD MODEL RESOLUTION
        self.prod_path = "/usr/src/app/runs/detect/exp_augmented_final/weights/best.onnx"
        self.alt_path = "/usr/src/app/models/best.pt"
        self.fallback_path = "yolo11n.pt"
        
        self.model = None
        self.model_loaded_from = None
        
        # Debug: print available paths
        print(f"🔍 DEBUG: Checking for models...", file=sys.stderr)
        print(f"   PROD path exists: {os.path.exists(self.prod_path)}", file=sys.stderr)
        print(f"   ALT path exists: {os.path.exists(self.alt_path)}", file=sys.stderr)
        print(f"   PROD directory: {os.path.dirname(self.prod_path)}", file=sys.stderr)
        if os.path.exists(os.path.dirname(self.prod_path)):
            print(f"   Contents: {os.listdir(os.path.dirname(self.prod_path))}", file=sys.stderr)
        
        # Try loading in order
        for path, desc in [
            (self.prod_path, "ONNX"),
            (self.alt_path, "PyTorch"),
        ]:
            if os.path.exists(path):
                try:
                    self.model = YOLO(path)
                    self.model_loaded_from = path
                    print(f"✅ PROD: Successfully loaded {desc} model from {path}", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"❌ PROD: Failed to load {desc} from {path}: {e}", file=sys.stderr)
        
        # Only fallback if no custom model loaded
        if self.model is None:
            print(f"⚠️ PROD WARNING: Custom models not found. Falling back to {self.fallback_path}", file=sys.stderr)
            try:
                self.model = YOLO(self.fallback_path)
                self.model_loaded_from = self.fallback_path
                print(f"⚠️ USING FALLBACK MODEL - Medicine detection may not work!", file=sys.stderr)
            except Exception as e:
                print(f"❌ FATAL: Cannot load any model: {e}", file=sys.stderr)
                raise RuntimeError("No model could be loaded. Check Docker volumes and paths.")
            
        self.model_names = self.model.names 
        print(f"📦 Model class names: {self.model_names}", file=sys.stderr)
        
        self.history_file = "/usr/src/app/data/logs/audit_trail.csv"
        
        # Initialize CSV with headers if it doesn't exist
        self._init_csv()
    
    def _init_csv(self):
        """Ensure CSV file has headers"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            if not os.path.exists(self.history_file):
                with open(self.history_file, "w", encoding='utf-8') as f:
                    f.write("status,message,timestamp,model_source,confidence\n")
                    f.flush()
                    os.fsync(f.fileno())
                print(f"✅ Initialized CSV at {self.history_file}", file=sys.stderr)
        except Exception as e:
            print(f"❌ CSV INIT ERROR: {e}", file=sys.stderr)

    def _preprocess_frame(self, frame):
        """
        Preprocess frame to ensure consistent format.
        WebRTC sends RGB, but YOLO training might expect BGR.
        """
        if frame is None:
            return None
        
        # If frame is RGB (3 channels), convert to BGR for consistency
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            # Check if it looks like RGB (common in WebRTC)
            # If Red channel is much higher than blue, it's probably RGB
            if np.mean(frame[:,:,0]) > np.mean(frame[:,:,2]):
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Ensure frame is uint8
        if frame.dtype != np.uint8:
            frame = (frame * 255).astype(np.uint8) if frame.max() <= 1.0 else frame.astype(np.uint8)
        
        return frame

    def analyze_frame(self, frame, target_id):
        """
        CORE MEDICINE DETECTION: This function is the heartbeat of your system.
        It runs inference and then logs the result to PROD storage.
        """
        if frame is None:
            return {
                "detected_id": "none",
                "confidence": 0.0,
                "annotated_frame": None,
                "match_status": "ERROR",
                "error": "Frame is None"
            }
        
        # Preprocess frame
        frame = self._preprocess_frame(frame)
        
        # 1. RUN DETECTION
        try:
            results = self.model(frame, conf=0.5, verbose=False, classes=[0, 1, 2, 3, 4])
        except Exception as e:
            print(f"❌ INFERENCE ERROR: {e}", file=sys.stderr)
            return {
                "detected_id": "none",
                "confidence": 0.0,
                "annotated_frame": frame.copy(),
                "match_status": "ERROR",
                "error": str(e)
            }
        
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
                
                # Debug log every detection
                print(f"🎯 DETECTION: {detected_id} (conf={conf:.3f}) vs target={target_id} → {'MATCH' if is_match else 'MISMATCH'}", file=sys.stderr)
                
                # 3. PROD LOGGING: Write directly to the persistent CSV
                # LOWERED THRESHOLD to catch more detections in PROD
                if conf > 0.45:  # ⬇️ LOWERED from 0.60 for PROD robustness
                    status = "SAFE" if is_match else "DANGER"
                    msg = f"Verified: {detected_id}" if is_match else f"Mismatch! Detected {detected_id}"
                    
                    try:
                        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
                        with open(self.history_file, "a", encoding='utf-8') as f:
                            f.write(f"{status},{msg},{timestamp},{self.model_loaded_from},{conf:.3f}\n")
                            f.flush()
                            os.fsync(f.fileno())
                    except Exception as e:
                        print(f"❌ PROD LOG ERROR: {e}", file=sys.stderr)
                break 
            else:
                # No detections
                print(f"⚠️ NO DETECTIONS in frame", file=sys.stderr)

        return {
            "detected_id": detected_id,
            "confidence": conf,
            "annotated_frame": annotated_frame,
            "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH",
            "model_source": self.model_loaded_from
        }