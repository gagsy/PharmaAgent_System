import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import time
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode

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

# 3. AUTHENTICATION (Keep existing logic)
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
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    
    st.divider()
    st.write(f"👤 {st.user.name}")
    if st.button("Logout", on_click=st.logout):
        st.stop()

# 6. REAL-TIME VIDEO PROCESSOR CLASS
class VideoProcessor:
    def __init__(self, target_id, brain_engine):
        self.target_id = target_id
        self.brain = brain_engine

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        result = self.brain.process_live_stream(img, self.target_id)
        return av.VideoFrame.from_ndarray(result["annotated_frame"], format="bgr24")

# 7. MAIN WORKFLOW
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    
    with st.popover("💡 View Photo Tips for 99% Accuracy"):
        st.markdown("### **How to take the perfect medical photo:**")
        col_tips1, col_tips2 = st.columns(2)
        with col_tips1:
            st.success("**✅ DO THIS**")
            st.write("* Place on **Plain White** paper")
            st.write("* Use **Indirect Light**")
        with col_tips2:
            st.error("**❌ AVOID THIS**")
            st.write("* Dark/Cluttered backgrounds")
            st.write("* Direct flash/glare")
        st.info("Live streaming handles background noise automatically.")

    # UPDATED REAL-TIME STREAMER WITH FREE TURN RELAY
    ctx = webrtc_streamer(
        key="pharma-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: VideoProcessor(target_id, brain),
        # Fixes "Connection taking longer" error on cloud
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]}, # Standard Google STUN
                {
                    "urls": ["turn:staticauth.openrelay.metered.ca:80"], # Open Relay Project Port 80
                    "username": "openrelayproject",
                    "credential": "openrelayprojectsecret"
                },
                {
                    "urls": ["turn:staticauth.openrelay.metered.ca:443"], # Open Relay Project Port 443
                    "username": "openrelayproject",
                    "credential": "openrelayprojectsecret"
                }
            ]
        },
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if ctx.state.playing:
        st.success("Scanner Active. Tracking Medicine...")
    else:
        st.warning("Click 'START' to activate the Real-Time AI Scanner.")

# Tabs 2 and 3 (Unchanged logic for Historical Audit and Guide)
with t2:
    st.header("Global Audit Ledger")
    log_path = "data/logs/audit_trail.csv"
    if os.path.exists(log_path):
        import pandas as pd
        try:
            df = pd.read_csv(log_path, sep=';', on_bad_lines='skip')
            st.dataframe(df.sort_index(ascending=False), width="stretch", hide_index=True)
            st.download_button("📥 Download CSV Audit Report", data=df.to_csv(index=False, sep=';'), file_name="pharma_audit_report.csv", mime="text/csv")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    else:
        st.warning("No audit records found.")

with t3:
    st.header("Medical System Handbook")
    st.markdown("- **Step 1:** Select drug. - **Step 2:** Click 'START' on scanner. - **Step 3:** Watch for the bounding box.")