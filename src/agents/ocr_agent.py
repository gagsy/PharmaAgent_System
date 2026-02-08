import pytesseract
import re
from datetime import datetime
from PIL import Image

class OCRAgent:
    def extract_expiry(self, image_path):
        # 1. Load and recognize text
        text = pytesseract.image_to_string(Image.open(image_path))
        
        # 2. Use Regex to find common date patterns (MM/YYYY or DD-MM-YYYY)
        date_pattern = r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{2}/\d{4})'
        matches = re.findall(date_pattern, text)
        
        if not matches:
            return {"status": "UNKNOWN", "msg": "No expiry date detected."}
            
        # 3. Logic to check if expired
        expiry_str = matches[0]
        # (Simplified) Compare with datetime.now()
        return {"status": "SUCCESS", "date": expiry_str, "msg": f"Detected Expiry: {expiry_str}"}