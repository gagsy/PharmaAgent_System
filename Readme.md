# 🏥 PharmaAgent System: Agentic Hospital Automation

[![Enterprise Ready](https://img.shields.io/badge/Status-Production--Ready-green)](https://acquire.com)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org/)

A high-fidelity, multi-agent AI system designed to automate pharmacy verification and safety protocols. This "Agentic" solution uses a modular orchestration layer to manage specialized Vision, Safety, and Audit agents.

## 💎 Strategic IP Assets (Value Proposition)
* **Agentic Multi-Model Architecture**: Clear separation of Vision (YOLO), Pharma (Rules), and Audit (Compliance) layers.
* **Enterprise Security**: Native OIDC (OpenID Connect) integration with Google/Microsoft for secure hospital access.
* **Immutable Audit Trail**: Automatic HIPAA-ready logging of every verification transaction.
* **Scalable Data Layer**: JSON-driven inventory management allows for instant database updates.

## 🛠 Tech Stack
* **Orchestration**: Custom Agentic Brain (OODA Loop inspired).
* **Vision**: YOLO11 (Real-time object detection).
* **Backend**: Streamlit Enterprise (Headless implementation).
* **Containerization**: Optimized Docker/Docker-Compose on Debian Trixie.

## 📂 Project Structure
Managed via a professional `src/` layout to ensure maintainability and separation of concerns.
- `src/agents/`: Modular AI logic.
- `src/brain/`: Multi-agent orchestration layer.
- `data/logs/`: Immutable transaction records.

## 🚀 Quick Start (Deployment)
Ensure Docker and Docker Compose are installed.

1. **Configure Secrets**: Populate `.streamlit/secrets.toml` with OIDC credentials.
2. **Launch System**:
   ```bash
   docker compose up --build