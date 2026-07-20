# Carbon Footprint Calculator — Complete Roadmap & Cheat Sheet

This document provides a practical guide to set up, run, build, and deploy the Carbon Footprint Calculator app.

## 1. Project Overview

This project is a Streamlit web app that lets users estimate their monthly carbon footprint based on lifestyle inputs such as transport, waste, energy, diet, and consumption.

### Main Files
- app.py — main Streamlit app entry point
- functions.py — helper functions for preprocessing, chart generation, and tab navigation
- requirements.txt — Python package dependencies
- models/ — trained model and scaler files
- style/ — CSS, JS, markdown, and fonts
- media/ — images and assets

---

## 2. Requirements

### System Requirements
- macOS / Linux / Windows
- Python 3.10 or 3.11 recommended
- Internet access for installing packages
- Terminal access

### Required Python Packages
Install these dependencies:

```bash
pip install streamlit pandas numpy matplotlib scikit-learn Pillow
```

If you prefer using the repository requirements file:

```bash
pip install -r requirements.txt
```

---

## 3. Local Development Setup

### Option A — Create a Virtual Environment

```bash
cd /path/to/Carbon-Footprint-Calculator-App-main
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
```

On Windows:

```bash
cd \path\to\Carbon-Footprint-Calculator-App-main
python -m venv .venv
.venv\Scripts\activate
```

### Option B — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import streamlit, pandas, numpy, matplotlib, sklearn, PIL; print('All dependencies installed')"
```

---

## 4. How to Run the Project Locally

From the project folder:

```bash
cd /path/to/Carbon-Footprint-Calculator-App-main
source .venv/bin/activate
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

### Useful Run Command

```bash
streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501
```

---

## 5. Development Workflow Cheat Sheet

### Start the app
```bash
source .venv/bin/activate
streamlit run app.py
```

### Stop the app
Press:
```bash
Ctrl + C
```

### Install a missing package
```bash
pip install package-name
```

### Save installed packages
```bash
pip freeze > requirements.txt
```

### Check Python version
```bash
python --version
```

### Check installed package versions
```bash
pip show streamlit pandas scikit-learn
```

---

## 6. Build / Packaging Notes

This project is a Streamlit app, so there is no traditional build step like a compiled frontend bundle.

### Typical Build Flow
1. Install dependencies
2. Run locally with Streamlit
3. Test UI interactions and model prediction flow
4. Prepare for deployment

### Optional Production-Ready Checklist
- Verify all media files exist
- Confirm model files are present in the models directory
- Test all form inputs
- Ensure the app runs without missing file errors

---

## 7. Deployment Options

### A. Streamlit Community Cloud
Best for quick public deployment.

Steps:
1. Push the repository to GitHub
2. Go to Streamlit Community Cloud
3. Create a new app
4. Select the repository and main file: app.py
5. Deploy

### B. Local Server / VPS Deployment
For a more controlled deployment:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Use this when deploying on a cloud server, Docker host, or VM.

### C. Docker Deployment (Optional)
A Dockerfile can be added if you want containerized deployment.

Example structure:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

---

## 8. Common Issues & Fixes

### Error: Streamlit not found
```bash
pip install streamlit
```

### Error: ModuleNotFoundError
Install missing dependencies:
```bash
pip install -r requirements.txt
```

### Error: Port already in use
Use a different port:
```bash
streamlit run app.py --server.port 8502
```

### Error: App opens the remote deployment page
Run locally using:
```bash
streamlit run app.py
```

### Error: Old packages incompatible with Python version
Use Python 3.10 or 3.11 with a fresh virtual environment.

---

## 9. Recommended Development Commands

```bash
# Create environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

---

## 10. Quick Start Summary

If you want the fastest path:

```bash
cd /path/to/Carbon-Footprint-Calculator-App-main
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
./.venv/bin/streamlit run app.py --server.headless true --server.port 8502
---

## 11. Deployment Checklist

- [ ] Python dependencies installed
- [ ] Models present in models/
- [ ] App runs locally
- [ ] Static assets load correctly
- [ ] GitHub repository pushed
- [ ] Deployment target selected
- [ ] Environment variables configured if needed

---

## 12. Final Note

This app is lightweight and ideal for local development and Streamlit-based deployment. For production, always test the app thoroughly before publishing it publicly.
