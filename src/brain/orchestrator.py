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
        """NEW: Handles real-time video frames for the Live Scanner"""
        try:
            # 1. Direct frame analysis (returns annotated frame with bounding boxes)
            # Ensure your updated VisionAgent has the 'analyze_frame' method
            vision_data = self.vision.analyze_frame(frame, target_id)
            
            # 2. Extract detected ID for background logic
            detected_id = vision_data.get("detected_id")
            
            # 3. Real-time Status Check
            # Note: We skip heavy audit logging here to maintain high FPS (Frames Per Second)
            if detected_id == target_id:
                vision_data["status"] = "SAFE"
            else:
                vision_data["status"] = "DANGER"
                
            return vision_data
            
        except Exception as e:
            # Return original frame if AI fails to prevent screen flickering
            return {"annotated_frame": frame, "status": "ERROR", "detected_id": "none"}