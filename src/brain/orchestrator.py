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
            # STEP 1: AI Vision Analysis
            # Actually use the agent to detect the pill in the image
            vision_result = self.vision.analyze_pill(image_path)
            detected_pill = vision_result.get("detected_pill_id")

            # STEP 2: Safety Cross-Reference
            # Compare what the camera sees vs. what the user selected
            if detected_pill != target_id:
                msg = f"MISMATCH DETECTED: Camera saw {detected_pill}, but you selected {target_id}."
                status = "DANGER"
            else:
                msg = f"SUCCESS: Identity Verified for {target_id}."
                status = "SAFE"

            # STEP 3: Immutable Logging
            final_report = {
                "status": status,
                "msg": msg,
                "pill_id": target_id,
                "timestamp": "2026-02-09"
            }
            self.auditor.log_transaction(final_report)

            return final_report

        except Exception as e:
            return {"status": "ERROR", "msg": f"System Failure: {str(e)}"}