import os
import pandas as pd

class AuditorAgent:
    def __init__(self, log_path="data/logs/audit_trail.csv"):
        self.log_path = log_path

    def log_transaction(self, data):
        # 1. GET THE PARENT DIRECTORY (data/logs)
        log_dir = os.path.dirname(self.log_path)
        
        # 2. CREATE THE DIRECTORY IF IT DOES NOT EXIST
        # 'exist_ok=True' prevents errors if the folder is already there
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        # 3. SAVE THE DATA
        df = pd.DataFrame([data])
        # Use mode='a' to append and header check to only write headers once
        df.to_csv(self.log_path, mode='a', index=False, 
                  header=not os.path.exists(self.log_path))
        return {"status": "LOGGED", "file": self.log_path}