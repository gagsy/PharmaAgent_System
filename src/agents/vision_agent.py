import os
import cv2
import json
from ultralytics import YOLO

# FILE: src/agents/vision_agent.py

class VisionAgent:
    def __init__(self, model_path="runs/detect/runs/pharma/exp_final_attempt4/weights/best.pt"):
        # 1. LOAD ONLY YOUR CUSTOM BRAIN
        # This replaces generic 'yolo11n.pt' and removes traffic lights.
        self.model = YOLO(model_path)
        """
        Initializes the YOLO model with custom medicine weights.
       
        """
        # Load custom trained YOLO brain.
        # Fallback to default path if the primary one is missing.
        if not os.path.exists(model_path):
            print(f"Warning: {model_path} not found. Loading generic YOLOv8n.")
            self.model = YOLO('yolov8n.pt') 
        else:
            self.model = YOLO(model_path)
        
        # Mapping for detected classes
        self.model_names = self.model.names 

    def analyze_pill(self, image_path):
        """
        Processes a static image upload and draws bounding boxes.
       
        """
        # Run inference with a higher confidence threshold for pharmaceutical accuracy.
        #
        # Force the model to ONLY see your 5 medicines
        results = self.model(image_path, conf=0.6, classes=[0, 1, 2, 3, 4])
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