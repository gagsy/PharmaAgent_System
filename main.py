import streamlit as st
import json
import numpy as np
import cv2
from src.brain.orchestrator import Orchestrator

# 1. PROFESSIONAL UI CONFIGURATION
st.set_page_config(page_title="PharmaAgent Enterprise", layout="wide")

# Inject CSS to hide Streamlit 'Deploy' button and footer
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 2. AUTHENTICATION GATE (OIDC)
# Securely checks login status using st.user (Native in 2026)
if not st.user.is_logged_in:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("Authorized Personnel Only. Please log in to proceed.")
    if st.button("Log in with Google", on_click=st.login):
        st.stop() # Stops execution until authenticated
    st.stop()

# 3. DYNAMIC DATA LOADING
@st.cache_data
def load_med_data():
    with open('data/inventory.json', 'r') as f:
        return json.load(f)

med_data = load_med_data()

# Sidebar: Map readable names to technical IDs
selected_name = st.sidebar.selectbox(
    "Select Target Medication", 
    options=[details['name'] for details in med_data.values()]
)
# Reverse lookup to find the correct ID (e.g., pill_001)
target_pill_id = next(k for k, v in med_data.items() if v['name'] == selected_name)

# 4. PROTECTED WORKFLOW
st.sidebar.write(f"Logged in as: **{st.user.name}**")
if st.sidebar.button("Logout", on_click=st.logout):
    st.stop()

st.title(f"Verifying: {selected_name}")
brain = Orchestrator()
img_file = st.camera_input("Scan pill for verification")

if img_file:
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, 1)
    
    # Save frame for Vision Agent processing
    cv2.imwrite("temp_scan.jpg", frame)
    
    with st.spinner("Agents performing cross-reference safety checks..."):
        result = brain.process_order("temp_scan.jpg", target_pill_id)
        
    if result['status'] == "SAFE":
        st.success(f"✅ {result['msg']}")
    else:
        st.error(f"🚨 {result['msg']}")

    st.subheader("Immutable Audit Log")
    st.json(result) # Showing the data trail buyers value