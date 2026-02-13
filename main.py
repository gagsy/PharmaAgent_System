import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# 1. SYSTEM INITIALIZATION
sys.path.append(os.path.join(os.getcwd(), 'src'))
from brain.orchestrator import Orchestrator

st.set_page_config(page_title="PharmaAgent | Live AI", page_icon="🛡️", layout="wide")

# 2. FAIL-SAFE AUTHENTICATION (Resolves Blank Screen)
def is_authenticated():
    # Attempt to check Streamlit's built-in user object
    try:
        if hasattr(st, "user") and st.user.is_logged_in:
            return True
    except:
        pass
    # Local session fallback for manual login/bypass
    return st.session_state.get("authenticated", False)

if not is_authenticated():
    st.title("🏥 PharmaAgent Secure Access")
    
    # Try the professional SSO button
    if hasattr(st, "login"):
        st.info("System OIDC-Ready. Authenticate to proceed.")
        st.button("🔐 SSO Login", on_click=st.login)
    
    # Manual Access Gate (Prevents Blank Screen if SSO fails)
    st.divider()
    st.subheader("Manual Access")
    access_code = st.text_input("Enter Security PIN", type="password")
    if st.button("Unlock System"):
        if access_code == "1234": # Your Demo PIN
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid PIN")
    st.stop()

# 3. CORE LOGIC (Only runs if authenticated)
med_data = json.load(open('data/inventory.json', 'r'))
brain = Orchestrator()

with st.sidebar:
    st.title("🛡️ PharmaGuard")
    selected_name = st.selectbox("Current Task", options=[v['name'] for v in med_data.values()])
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.logout() if hasattr(st, "logout") else None
        st.rerun()

# 4. LIVE DETECTION PROCESSOR
class VideoProcessor:
    def __init__(self, target_id, brain_engine):
        self.target_id = target_id
        self.brain = brain_engine

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        # Ensure your Orchestrator has 'process_live_stream' method
        result = self.brain.process_live_stream(img, self.target_id)
        return av.VideoFrame.from_ndarray(result["annotated_frame"], format="bgr24")

# 5. UI TABS
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    
    # WebRTC Streamer with TURN Relay (Fixes Infinite Spinner)
    ctx = webrtc_streamer(
        key="pharma-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: VideoProcessor(target_id, brain),
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]}, # Standard STUN
                {
                    "urls": ["turn:staticauth.openrelay.metered.ca:80"], # Open Relay Project
                    "username": "openrelayproject",
                    "credential": "openrelayprojectsecret"
                }
            ]
        },
        media_stream_constraints={"video": True, "audio": False}, # Disable audio to reduce errors
        async_processing=True,
    )

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