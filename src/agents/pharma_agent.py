import json

class PharmaAgent:
    def __init__(self, inventory_path='data/inventory.json'):
        with open(inventory_path, 'r') as f:
            self.db = json.load(f)

    def verify_safety(self, detected_id, expected_id):
        drug = self.db.get(detected_id)
        if not drug:
            return {"status": "ERROR", "msg": "Medication not found in database."}
        
        if detected_id == expected_id:
            return {"status": "SAFE", "msg": f"Verified: {drug['name']}."}
        else:
            return {"status": "DANGER", "msg": f"Mismatch! Detected {drug['name']}."}