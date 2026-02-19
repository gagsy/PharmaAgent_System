import streamlit as st
import json
import numpy as np
import cv2
import sys
import os
import av
import pandas as pd
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import time

# 1. INITIALIZATION & PATH FIXING
# This dynamically finds the root directory of your project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure 'src' is in the path for both local and Docker
sys.path.append(os.path.join(BASE_DIR, 'src'))
from brain.orchestrator import Orchestrator

st.set_page_config(page_title="PharmaAgent | AI Scanner", page_icon="🛡️", layout="wide")

# Helper to build dynamic paths
def get_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

# --- CONFIGURATION ---
TIMEOUT_SECONDS = 600  # 10 minutes (600 seconds)
DEMO_PIN = "9@26"

# 1. INITIALIZE SESSION STATE
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = time.time()

# 2. CHECK FOR TIMEOUT (Auto-logout logic)
if st.session_state["authenticated"]:
    current_time = time.time()
    elapsed_time = current_time - st.session_state["last_activity"]
    
    if elapsed_time > TIMEOUT_SECONDS:
        st.session_state["authenticated"] = False
        st.warning("Session expired due to inactivity. Please log in again.")
        st.rerun()
    else:
        # Update last activity timestamp on every interaction
        st.session_state["last_activity"] = current_time

# 3. STABLE AUTHENTICATION GATE
if not st.session_state["authenticated"]:
    st.title("🏥 PharmaAgent Secure Access")
    st.info("System is ready for Live AI Inspection.")
    access_code = st.text_input("Security PIN", type="password", help="Enter demo pin to start")
    
    if st.button("Unlock System"):
        if access_code == DEMO_PIN: 
            st.session_state["authenticated"] = True
            st.session_state["last_activity"] = time.time() # Reset timer on login
            st.rerun()
        else:
            st.error("Invalid PIN")
    st.stop()
    
# 3. LOAD DATA & AI ENGINE
# Updated to use dynamic paths for inventory and history
inventory_path = get_path('data/inventory.json')
history_file = get_path('data/history.json')

with open(inventory_path, 'r') as f:
    med_data = json.load(f)

brain = Orchestrator()

# 4. SIDEBAR LOGIC & LIVE AUDIT VIEW
with st.sidebar:
    st.title("🛡️ PharmaGuard")
    st.divider()
    selected_name = st.selectbox("Current Task", options=[v['name'] for v in med_data.values()])
    target_id = next(k for k, v in med_data.items() if v['name'] == selected_name)
    
    st.divider()
    st.subheader("📋 Recent Detections")
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history_data = json.load(f)
            
            if history_data:
                df_side = pd.DataFrame(history_data)
                st.table(df_side[['timestamp', 'medicine', 'confidence']].iloc[::-1].head(5))
                
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
        # Ensure we call the correct agent method
        result = self.brain.agent.analyze_frame(img, self.target_id)
        
        # We return the annotated frame exactly as before to maintain stability
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
    
    # 1. Use caching with clear capability to ensure fresh data
    @st.cache_data(show_spinner=False)
    def load_fresh_logs(path):
        if os.path.exists(path):
            return pd.read_csv(path, on_bad_lines='skip')
        return None

    log_path = get_path('data/logs/audit_trail.csv')

    # 2. Refresh Button for the "Simple Man"
    if st.button("🔄 Check for New Detections"):
        load_fresh_logs.clear()
        st.rerun()

    if os.path.exists(log_path):
        try:
            df = load_fresh_logs(log_path)
            
            if df is not None and not df.empty:
                # --- PAGINATION LOGIC START ---
                # Reverse to show newest results first
                df_display = df.iloc[::-1].reset_index(drop=True)
                
                # Pagination Controls
                col_p1, col_p2, col_p3 = st.columns([2, 2, 3])
                with col_p1:
                    rows_per_page = st.selectbox("Rows per page", options=[10, 20, 50, 100], index=0)
                
                total_rows = len(df_display)
                total_pages = max(1, (total_rows - 1) // rows_per_page + 1)
                
                with col_p2:
                    current_page = st.number_input("Page", min_value=1, max_value=total_pages, step=1, value=1)
                
                with col_p3:
                    st.markdown(f"**Total Records:** {total_rows} | **Page:** {current_page}/{total_pages}")

                # Slice the dataframe for the current page
                start_idx = (current_page - 1) * rows_per_page
                end_idx = start_idx + rows_per_page
                paginated_df = df_display.iloc[start_idx:end_idx]

                # Display the Paginated Table
                st.dataframe(paginated_df, use_container_width=True, hide_index=True)
                # --- PAGINATION LOGIC END ---

                # Actions Row
                col1, col2 = st.columns(2)
                with col1:
                    csv_download = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV Audit Report",
                        data=csv_download,
                        file_name=f"pharma_audit_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    if st.button("🗑️ Reset Audit Ledger"):
                        os.makedirs(os.path.dirname(log_path), exist_ok=True)
                        with open(log_path, "w") as f:
                            f.write("Result,Inspection Notes,Time,AI Certainty\n")
                        load_fresh_logs.clear()
                        st.rerun()
            else:
                st.info("Log file is currently empty.")

        except Exception as e:
            st.error(f"⚠️ Error loading audit logs: {e}")
            st.info(f"Diagnostic Path: {log_path}")
    else:
        st.warning("No audit records found. Detected medicines will appear here automatically.")


with t3:
    st.header("Medical System Handbook")
    st.markdown("""
    - **Step 1:** Select the drug from the 'Current Task' dropdown.
    - **Step 2:** Click 'START' on the Live Inspection tab.
    - **Step 3:** Align the medicine strip. A **Green Box** confirms a match.
    - **Step 4:** Verified detections (>80% confidence) are logged automatically.
    """)