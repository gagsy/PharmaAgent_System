from src.agents.vision_agent import VisionAgent
from src.agents.pharma_agent import PharmaAgent
from src.agents.auditor_agent import AuditorAgent

class Orchestrator:
    def __init__(self):
        self.vision = VisionAgent()
        self.safety = PharmaAgent()
        self.auditor = AuditorAgent()

    def process_order(self, image_path, target_id):
        try:
            # 1. RUN VISION AGENT
            vision_result = self.vision.analyze_pill(image_path)
            detected_id = vision_result.get("detected_pill_id")

            # 2. RUN SAFETY CHECK
            if detected_id == target_id:
                status = "SAFE"
                msg = f"Identity Verified: {target_id} matches the scanned medication."
            else:
                status = "DANGER"
                msg = f"MISMATCH: Scanned {detected_id} does not match prescribed {target_id}."

            # 3. LOG TO AUDIT TRAIL
            report = {"status": status, "msg": msg, "pill": target_id}
            self.auditor.log_transaction(report)

            return report

        except Exception as e:
            return {"status": "ERROR", "msg": f"System Failure: {str(e)}"}