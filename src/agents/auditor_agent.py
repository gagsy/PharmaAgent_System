import time
import pandas as pd
import os

class AuditorAgent:
    def __init__(self, log_path='data/logs/audit_trail.csv'):
        self.log_path = log_path

    def log_transaction(self, entry):
        entry['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        df = pd.DataFrame([entry])
        
        # Append to CSV or create new if not exists
        df.to_csv(self.log_path, mode='a', header=not os.path.exists(self.log_path), index=False)
        return entry