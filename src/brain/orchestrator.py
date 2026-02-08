from agents.vision_agent import VisionAgent
from agents.pharma_agent import PharmaAgent
from agents.auditor_agent import AuditorAgent

class Orchestrator:
    def __init__(self):
        self.vision = VisionAgent()
        self.safety = PharmaAgent()
        self.auditor = AuditorAgent()

    def process_order(self, image_path, expected_id):
        # Step 1: Vision Agent identifies
        detected_id = self.vision.identify_medication(image_path)
        
        # Step 2: Pharma Agent verifies
        check = self.safety.verify_safety(detected_id, expected_id)
        
        # Step 3: Auditor Agent logs everything
        return self.auditor.log_transaction(check)