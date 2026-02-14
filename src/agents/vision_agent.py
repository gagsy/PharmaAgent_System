import os
import cv2
import json
from ultralytics import YOLO

# FILE: src/agents/vision_agent.py
class VisionAgent:
    def __init__(self):
        # 1. Print every file in the app directory to find best.pt or best.onnx
        print("--- DOCKER FILE SYSTEM CHECK ---")
        found_onnx = None
        found_pt = None
        
        for root, dirs, files in os.walk("/usr/src/app/runs"):
            for file in files:
                # Prioritize finding the production ONNX model
                if file == "best.onnx":
                    found_onnx = os.path.join(root, file)
                    print(f"🎯 FOUND PRODUCTION MODEL: {found_onnx}")
                elif file == "best.pt":
                    found_pt = os.path.join(root, file)
                    print(f"🎯 FOUND TRAINING MODEL: {found_pt}")

        # 2. Path Logic: Use ONNX if available, otherwise use PT, otherwise fallback
        # Primary production path check
        model_path = "/usr/src/app/runs/detect/runs/pharma/exp_augmented_final/weights/best.onnx"
        
        # If the specific augmented path doesn't exist, use the one found during walk
        if not os.path.exists(model_path):
            model_path = found_onnx if found_onnx else found_pt
        
        if model_path and os.path.exists(model_path):
            self.model = YOLO(model_path)
            print(f"✅ SUCCESS: {os.path.basename(model_path)} loaded.")
        else:
            print("❌ ERROR: Custom model not found. Falling back to generic yolo11n.pt")
            self.model = YOLO("yolo11n.pt")        
            
        # Mapping for detected classes
        self.model_names = self.model.names 

    def analyze_pill(self, image_path):
        """
        Processes a static image upload and draws bounding boxes.
        """
        # Run inference with a higher confidence threshold for pharmaceutical accuracy.
        # Force the model to ONLY see your 5 medicines
        results = self.model(image_path, conf=0.25, classes=[0, 1, 2, 3, 4])
        # Load image for visual annotation
        img = cv2.imread(image_path)
        
        for r in results:
            if len(r.boxes) > 0:
                # 1. Extract box coordinates
                box = r.boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 2. Get label and confidence
                class_id = int(box.cls[0])
                detected_id = self.model_names.get(class_id, "Unknown")
                conf = float(box.conf[0])

                # 3. Draw Green Bounding Box for static detections
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 4)
                
                # 4. Add Text Label
                label = f"{detected_id} {conf:.2f}"
                cv2.putText(img, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                # 5. Save the annotated image
                cv2.imwrite(image_path, img)
                
                return {
                    "status": "SUCCESS",
                    "detected_pill_id": detected_id,
                    "confidence": conf
                }
        
        return {"status": "UNKNOWN", "detected_pill_id": "none"}

    def analyze_frame(self, frame, target_id):
        """
        Processes live video frames with dynamic box colors based on target medicine.
        """
        # Run real-time inference. Lower confidence threshold allows for flicker-free video.
        # Set verbose=False to keep the console clean.
        # Add the classes filter here too to keep live video clean
        results = self.model(frame, conf=0.5, verbose=False, classes=[0, 1, 2, 3, 4])
        
        detected_id = "none"
        annotated_frame = frame.copy()

        for r in results:
            if len(r.boxes) > 0:
                # Prioritize top detection for live performance
                box = r.boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                class_id = int(box.cls[0])
                detected_id = self.model_names.get(class_id, "Unknown")
                conf = float(box.conf[0])

                # DYNAMIC COLOR LOGIC: 
                # Green if correct medicine, Red if wrong.
                box_color = (0, 255, 0) if detected_id == target_id else (0, 0, 255)
                
                # Draw visual markers on the frame
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 4)
                label = f"{detected_id} ({conf:.2f})"
                cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                
                # Break to ensure only the highest confidence drug is labeled per frame
                break 

        return {
            "detected_id": detected_id,
            "annotated_frame": annotated_frame
        }