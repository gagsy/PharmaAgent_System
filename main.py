import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# 1. INITIALIZATION
sys.path.append(os.path.join(os.getcwd(), 'src'))
from brain.orchestrator import Orchestrator

st.set_page_config(page_title="PharmaAgent | AI Scanner", page_icon="🛡️", layout="wide")

# 2. STABLE AUTHENTICATION GATE (Fixes AttributeError)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("System is ready for Live AI Inspection.")
    access_code = st.text_input("Security PIN", type="password", help="Enter demo pin to start")
    if st.button("Unlock System"):
        if access_code == "1234": # Your secure demo PIN
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid PIN")
    st.stop()

# 3. LOAD DATA & AI ENGINE
med_data = json.load(open('data/inventory.json', 'r'))
brain = Orchestrator()

# 4. SIDEBAR LOGIC
with st.sidebar:
    st.title("🛡️ PharmaGuard")
    st.divider()
    selected_name = st.selectbox("Current Task", options=[v['name'] for v in med_data.values()])
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# 5. LIVE VIDEO PROCESSOR
class VideoProcessor:
    def __init__(self, target_id, brain_engine):
        self.target_id = target_id
        self.brain = brain_engine

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        # Direct call to your AI Brain
        result = self.brain.process_live_stream(img, self.target_id)
        return av.VideoFrame.from_ndarray(result["annotated_frame"], format="bgr24")

# 6. MAIN INTERFACE
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    
    # STABLE WEB-RTC (Fixes "Connection taking longer" and 3.13 crashes)
    ctx = webrtc_streamer(
        key="pharma-scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: VideoProcessor(target_id, brain),
        rtc_configuration={
            "iceServers": [
                {"urls": ["stun:stun.l.google.com:19302"]},
                {
                    "urls": ["turn:staticauth.openrelay.metered.ca:80"],
                    "username": "openrelayproject",
                    "credential": "openrelayprojectsecret"
                }
            ]
        },
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if ctx and ctx.state.playing:
        st.success("AI Active. Place medicine strip in view.")
    else:
        st.warning("Click 'START' to activate the Real-Time Scanner.")

# Tab 2 & 3 logic remains exactly as you had it
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