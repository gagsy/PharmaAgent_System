import os
import pandas as pd
from datetime import datetime
import uuid

class AuditorAgent:
    def __init__(self, log_path="data/logs/audit_trail.csv"):
        self.log_path = log_path

    def log_transaction(self, entry_data):
        """
        Records the agentic decision into an immutable CSV ledger.
        """
        try:
            # 1. ENSURE DIRECTORY INTEGRITY [cite: 99]
            log_dir = os.path.dirname(self.log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 2. ENRICH DATA FOR AUDIT COMPLIANCE
            # Add Timestamp and a unique ID for every scan
            enriched_data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Transaction_ID": str(uuid.uuid4())[:8],
                **entry_data # Merge with the original scan result
            }
            
            # 3. APPEND TO PERMANENT STORAGE [cite: 61]
            df = pd.DataFrame([enriched_data])
            df.to_csv(
                self.log_path, 
                mode='a', 
                index=False, 
                header=not os.path.exists(self.log_path)
            )
            
            # 4. RETURN CONFIRMATION TO ORCHESTRATOR 
            # Include the enriched data so the UI can show the Timestamp
            return enriched_data

        except Exception as e:
            # Fallback to prevent app crash
            return {"status": "LOG_ERROR", "msg": str(e)}