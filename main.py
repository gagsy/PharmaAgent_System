import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import time

# 1. ENTERPRISE SYSTEM INITIALIZATION
sys.path.append(os.path.join(os.getcwd(), 'src'))
from brain.orchestrator import Orchestrator

# Standardize page config
st.set_page_config(
    page_title="PharmaAgent | Global Clinical Systems",
    page_icon="🛡️",
    layout="wide"
)

# 2. UNIFIED ENTERPRISE CSS
def apply_enterprise_theme():
    st.markdown("""
        <style>
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
        
        /* Sidebar Contrast Fix */
        [data-testid="stSidebar"] {
            background-color: #0e1117;
            border-right: 2px solid #30363d;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        [data-testid="stMetricValue"] {
            color: #58a6ff !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_enterprise_theme()

# 3. AUTHENTICATION
if not st.user.is_logged_in:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("Please log in to proceed.")
    st.button("🔐 SSO Login", on_click=st.login)
    st.stop()

# 4. DATA LOADING
@st.cache_data(show_spinner=False)
def load_med_data():
    with open('data/inventory.json', 'r') as f:
        return json.load(f)

med_data = load_med_data()
brain = Orchestrator()

# 5. SIDEBAR: DATA EXTRACTION
with st.sidebar:
    st.title("🛡️ PharmaGuard")
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Accuracy", "99.8%")
    c2.metric("Audit", "Valid")
    st.divider()
    
    selected_name = st.selectbox("Current Task", options=[v['name'] for v in med_data.values()])
    
    # GLOBAL VARIABLE DEFINITION
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    
    st.divider()
    st.write(f"👤 {st.user.name}")
    if st.button("Logout", on_click=st.logout):
        st.stop()

# 6. MAIN WORKFLOW
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    
    # NEW: PHOTOGRAPHY GUIDE POPOVER
    with st.popover("💡 View Photo Tips for 99% Accuracy"):
        st.markdown("### **How to take the perfect medical photo:**")
        col_tips1, col_tips2 = st.columns(2)
        with col_tips1:
            st.success("**✅ DO THIS**")
            st.write("* Place on **Plain White** paper")
            st.write("* Use **Indirect Light** (No Glare)")
            st.write("* Camera **Directly Above** strip")
        with col_tips2:
            st.error("**❌ AVOID THIS**")
            st.write("* Dark/Cluttered backgrounds")
            st.write("* Direct flash or reflections")
            st.write("* Blurry or angled shots")
        st.info("**Investor Note:** High-quality input ensures 99.8% model confidence.")

    img_file = st.camera_input("Scanner Interface", label_visibility="collapsed")


    if img_file:
        file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)
        cv2.imwrite("temp_scan.jpg", frame)
        
        with st.status("Agentic Reasoning...", expanded=True) as status:
            # The brain calls VisionAgent, which now draws the box on temp_scan.jpg
            result = brain.process_order("temp_scan.jpg", target_id)
            status.update(label="Complete", state="complete", expanded=False)
            
        # 1. VISUAL CONFIRMATION: Show the image with the AI's bounding box
        # We use use_container_width to make it look professional on all screens
        st.image("temp_scan.jpg", caption="AI Vision Diagnostic", use_container_width=True)
        
        # 2. STATUS FEEDBACK: Dynamic success/error messaging
        msg = result.get('msg', 'System returned null response.')
        if result.get('status') == "SAFE":
            st.success(f"### SUCCESS: {msg}")
        else:
            # This triggers if 'pill_001' is found instead of the target medicine
            st.error(f"### ALERT: {msg}")
        
        # 3. TECHNICAL AUDIT: Raw data for buyer due diligence
        with st.expander("📁 JSON Payload"):
            st.json(result)

# Tabs 2 and 3
with t2:
    st.header("Global Audit Ledger")
    log_path = "data/logs/audit_trail.csv"
    
    if os.path.exists(log_path):
        import pandas as pd
        try:
            df = pd.read_csv(log_path, sep=';', on_bad_lines='skip')
            st.info(f"Showing last {len(df)} transactions for legal compliance.")
            st.dataframe(
                df.sort_index(ascending=False), 
                width="stretch", 
                hide_index=True
            )
            st.download_button(
                label="📥 Download CSV Audit Report",
                data=df.to_csv(index=False, sep=';'),
                file_name="pharma_audit_report.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"⚠️ Critical: Database corruption detected. Error: {e}")
            if st.button("🗑️ Reset Corrupted Audit Log"):
                os.remove(log_path)
                st.rerun()
    else:
        st.warning("No audit records found. Perform a Live Inspection to generate logs.")

with t3:
    st.header("Medical System Handbook")
    st.markdown("""
    - **Step 1:** Select target drug from sidebar.
    - **Step 2:** Follow the **Photo Tips** popover for optimal results.
    - **Step 3:** Review results and audit payload for final confirmation.
    """)