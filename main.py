import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import av
import pandas as pd # Added for data handling
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# 1. INITIALIZATION
sys.path.append(os.path.join(os.getcwd(), 'src'))
from brain.orchestrator import Orchestrator

st.set_page_config(page_title="PharmaAgent | AI Scanner", page_icon="🛡️", layout="wide")

# 2. STABLE AUTHENTICATION GATE
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("System is ready for Live AI Inspection.")
    access_code = st.text_input("Security PIN", type="password", help="Enter demo pin to start")
    if st.button("Unlock System"):
        if access_code == "1234": 
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid PIN")
    st.stop()

# 3. LOAD DATA & AI ENGINE
med_data = json.load(open('data/inventory.json', 'r'))
brain = Orchestrator()
history_file = "data/history.json" # Path used by VisionAgent

# 4. SIDEBAR LOGIC & LIVE AUDIT VIEW
with st.sidebar:
    st.title("🛡️ PharmaGuard")
    st.divider()
    selected_name = st.selectbox("Current Task", options=[v['name'] for v in med_data.values()])
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    
    st.divider()
    st.subheader("📋 Recent Detections")
    
    # Live Sidebar History Logic
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
            
            if history_data:
                df_side = pd.DataFrame(history_data)
                # Show last 5 detections for quick glance
                st.table(df_side[['timestamp', 'medicine', 'confidence']].iloc[::-1].head(5))
                
                # Download Button for the sidebar
                csv = df_side.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export History (CSV)",
                    data=csv,
                    file_name=f"pharma_audit_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No detections yet.")
        except Exception as e:
            st.error(f"Log Error: {e}")
    
    st.divider()
    if st.button("Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# 5. LIVE VIDEO PROCESSOR
class VideoProcessor:
    def __init__(self, target_id, brain_engine):
        self.target_id = target_id
        self.brain = brain_engine

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        result = self.brain.process_live_stream(img, self.target_id)
        return av.VideoFrame.from_ndarray(result["annotated_frame"], format="bgr24")

# 6. MAIN INTERFACE
t1, t2, t3 = st.tabs(["⚡ Live Inspection", "📊 Historical Audit", "📘 Guide"])

with t1:
    st.header(f"Inspecting: {selected_name}")
    
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
with t2:
    st.header("📊 Global Audit Ledger")
    
    # Path must match where VisionAgent writes the CSV inside the container
    log_path = "data/logs/audit_trail.csv"
    
    if os.path.exists(log_path):
        import pandas as pd
        try:
            # 1. Read the CSV using comma separator to match VisionAgent's write format
            df = pd.read_csv(log_path, on_bad_lines='skip')
            
            # 2. Display the Audit Table
            # We show the newest records at the top
            st.dataframe(
                df.iloc[::-1], 
                use_container_width=True, 
                hide_index=True
            )
            
            # 3. Download & Management Tools
            col1, col2 = st.columns(2)
            with col1:
                # Convert current dataframe to CSV for download
                csv_download = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV Audit Report",
                    data=csv_download,
                    file_name=f"pharma_audit_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Option to clear the ledger (use with caution in prod)
                if st.button("🗑️ Reset Audit Ledger"):
                    # Create a fresh file with just the header to avoid panda errors next load
                    with open(log_path, "w") as f:
                        f.write("status,msg,timestamp\n")
                    st.rerun()

        except Exception as e:
            st.error(f"⚠️ Error loading audit logs: {e}")
            # Diagnostic help for the developer
            st.info(f"Checking path: {os.path.abspath(log_path)}")
    else:
        # Shown if the 'logs' folder or file hasn't been created yet
        st.warning("No audit records found. Detected medicines will appear here automatically.")
        
with t3:
    st.header("Medical System Handbook")
    st.markdown("""
    - **Step 1:** Select the drug from the 'Current Task' dropdown.
    - **Step 2:** Click 'START' on the Live Inspection tab.
    - **Step 3:** Align the medicine strip. A **Green Box** confirms a match.
    - **Step 4:** Verified detections (>80% confidence) are logged automatically to the Sidebar and Audit tab.
    """)