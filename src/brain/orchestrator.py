from agents.vision_agent import VisionAgent
from agents.pharma_agent import PharmaAgent
from agents.auditor_agent import AuditorAgent

class Orchestrator:
    def __init__(self):
        self.vision = VisionAgent()
        self.safety = PharmaAgent()
        self.auditor = AuditorAgent()

    def process_order(self, image_path, target_id):
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