import os
import cv2
import json
from ultralytics import YOLO
from datetime import datetime

# FILE: src/agents/vision_agent.py
class VisionAgent:
    def __init__(self):
        # ... (Existing __init__ code remains exactly the same)
        print("--- DOCKER FILE SYSTEM CHECK ---")
        found_onnx = None
        found_pt = None
        for root, dirs, files in os.walk("/usr/src/app/runs"):
            for file in files:
                if file == "best.onnx":
                    found_onnx = os.path.join(root, file)
                    print(f"🎯 FOUND PRODUCTION MODEL: {found_onnx}")
                elif file == "best.pt":
                    found_pt = os.path.join(root, file)
                    print(f"🎯 FOUND TRAINING MODEL: {found_pt}")

        model_path = "/usr/src/app/runs/detect/runs/pharma/exp_augmented_final/weights/best.onnx"
        if not os.path.exists(model_path):
            model_path = found_onnx if found_onnx else found_pt
        
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)
            print(f"✅ SUCCESS: {os.path.basename(model_path)} loaded.")
        else:
            print("❌ ERROR: Custom model not found. Falling back to generic yolo11n.pt")
            self.model = YOLO("yolo11n.pt")        
            
        self.model_names = self.model.names 
        # Path for the persistent audit history file
        self.history_file = "/usr/src/app/data/logs/audit_trail.csv"

    def save_history_record(self, record):
        """Safely appends a new detection record to the JSON history file."""
        try:
            # Ensure the data directory exists
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            # Load existing data or start a new list if file doesn't exist
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    try:
                        history_data = json.load(f)
                    except json.JSONDecodeError:
                        history_data = []
            else:
                history_data = []

            # Append new record and save
            history_data.append(record)
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=4)
            return True
        except Exception as e:
            print(f"⚠️ Audit Log Error: {e}")
            return False


    def analyze_pill(self, image_path):
        # ... (Existing analyze_pill code remains exactly the same)
        results = self.model(image_path, conf=0.25, classes=[0, 1, 2, 3, 4])
        img = cv2.imread(image_path)
        for r in results:
            if len(r.boxes) > 0:
                box = r.boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                detected_id = self.model_names.get(class_id, "Unknown")
                conf = float(box.conf[0])
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 4)
                label = f"{detected_id} {conf:.2f}"
                cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.imwrite(image_path, img)
                return {"status": "SUCCESS", "detected_pill_id": detected_id, "confidence": conf}
        return {"status": "UNKNOWN", "detected_pill_id": "none"}

    def analyze_frame(self, frame, target_id):
        """
        Processes live frames and saves EVERY detection to the CSV audit trail.
        Matches use 'SAFE', Mismatches use 'DANGER'.
        """
        # 1. Run inference
        results = self.model(frame, conf=0.5, verbose=False, classes=[0, 1, 2, 3, 4])
        
        detected_id = "none"
        conf = 0.0
        annotated_frame = frame.copy()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for r in results:
            if len(r.boxes) > 0:
                # 2. Extract detection data
                box = r.boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                detected_id = self.model_names.get(class_id, "Unknown")
                conf = float(box.conf[0])

                # 3. Dynamic Visuals (Green for Match, Red for Mismatch)
                is_match = (detected_id == target_id)
                box_color = (0, 255, 0) if is_match else (0, 0, 255)
                
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 4)
                label = f"{detected_id} ({conf:.2f})"
                cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                
                # --- UPDATED AUDIT LOGGING LOGIC ---
                # Log ALL detections with confidence > 0.70 to your CSV
                if conf > 0.70:
                    status = "SAFE" if is_match else "DANGER"
                    msg = f"Verified: {detected_id}" if is_match else f"Mismatch! Detected {detected_id}"
                    
                    # CSV Format: status,msg,timestamp
                    audit_line = f"{status},{msg},{timestamp}\n"
                    
                    try:
                        # Absolute path used for Docker volume stability
                        csv_path = "/usr/src/app/data/logs/audit_trail.csv"
                        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                        with open(csv_path, "a") as f:
                            f.write(audit_line)
                            f.flush()            # Forces data out of Python's memory
                            os.fsync(f.fileno())  # Forces Windows to update the file on disk
                    except Exception as e:
                        print(f"⚠️ Audit Save Error: {e}")
                # -------------------------------------
                break 

        return {
            "detected_id": detected_id,
            "confidence": conf,
            "timestamp": timestamp,
            "match_status": "VERIFIED" if detected_id == target_id else "MISMATCH",
            "annotated_frame": annotated_frame
        }



        