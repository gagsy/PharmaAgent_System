from agents.vision_agent import VisionAgent
from agents.pharma_agent import PharmaAgent
from agents.auditor_agent import AuditorAgent

class Orchestrator:
    def __init__(self):
        self.vision = VisionAgent()
        self.safety = PharmaAgent()
        self.auditor = AuditorAgent()

    def process_order(self, image_path, target_id):
        """Maintains existing functionality for static image uploads"""
        try:
            # 1. Execute AI Vision
            vision_data = self.vision.analyze_pill(image_path)
            detected_id = vision_data.get("detected_pill_id")
            
            # 2. Safety Logic
            if detected_id == target_id:
                res = {"status": "SAFE", "msg": f"Verified: {target_id} matches."}
            else:
                res = {"status": "DANGER", "msg": f"Mismatch: Found {detected_id}."}
            
            # 3. Audit Logging
            self.auditor.log_transaction(res)
            return res
        except Exception as e:
            return {"status": "ERROR", "msg": f"Failed: {str(e)}"}

    def process_live_stream(self, frame, target_id):
        """UPDATED: Handles real-time video frames and medicine counting"""
        try:
            # 1. Direct frame analysis (returns annotated frame with bounding boxes)
            # We call your existing vision agent here
            vision_data = self.vision.analyze_frame(frame, target_id)
            
            # 2. Extract detected ID for background logic
            detected_id = vision_data.get("detected_id")
            
            # --- NEW: Extract and Pass the Count ---
            # We take 'current_count' from vision_data so the VideoProcessor can see it
            vision_data["current_count"] = vision_data.get("current_count", 0)
            # ------------------------------------------------
            
            # 3. Real-time Status Check
            if detected_id == target_id:
                vision_data["status"] = "SAFE"
            else:
                vision_data["status"] = "DANGER"
                
            return vision_data
            
        except Exception as e:
            # Return original frame with 0 count if AI fails to prevent screen flickering
            return {
                "annotated_frame": frame, 
                "status": "ERROR", 
                "detected_id": "none",
                "current_count": 0
            } 