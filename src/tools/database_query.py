import json

def get_medicine_data(pill_id):
    # This simulates a real hospital database query
    with open('data/inventory.json', 'r') as f:
        db = json.load(f)
    return db.get(pill_id)