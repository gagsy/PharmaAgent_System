from ultralytics import YOLO
import json
import os
import cv2

class VisionAgent:
    def __init__(self, model_path="models/best.pt"):
        if not os.path.exists(model_path):
            self.model = YOLO("yolov8n.pt")
        else:
            self.model = YOLO(model_path)
        
        self.model_names = self.model.names 

    def analyze_pill(self, image_path):
        results = self.model(image_path, conf=0.6)
        
        # Load image for drawing
        img = cv2.imread(image_path)
        
        for r in results:
            if len(r.boxes) > 0:
                # 1. Get box coordinates
                box = r.boxes[0]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 2. Map label and confidence
                class_id = int(box.cls[0])
                detected_id = self.model_names.get(class_id, "Unknown")
                conf = float(box.conf[0])

                # 3. Draw Bounding Box (Green)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 4)
                
                # 4. Add Label Text
                label = f"{detected_id} {conf:.2f}"
                cv2.putText(img, label, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                # 5. Overwrite the temp image with the visual markers
                cv2.imwrite(image_path, img)
                
                return {
                    "status": "SUCCESS",
                    "detected_pill_id": detected_id,
                    "confidence": conf
                }
        
        return {"status": "UNKNOWN", "detected_pill_id": "none"}