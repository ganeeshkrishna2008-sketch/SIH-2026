# SIH26127 — City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics

**Prototype Implementation: Phase 0 (Architecture & Foundation) & Phase 1 (Synthetic Trajectory & Analytics MVP)**

---

## 🌟 Overview
This repository contains the working implementation of **SIH26127**, designed to demonstrate:
1. **Multi-Camera Vehicle Association & Trajectory Reconstruction**: Chronologically mapping vehicle observations across distributed camera nodes with transit time intervals, speeds, and an interactive Leaflet/OpenStreetMap route.
2. **Macro Urban Traffic Analytics**: Aggregated temporal flow analysis (10-minute intervals), camera volume distribution, modal share breakdown, and peak congestion detection.
3. **Vehicle Search & History**: Fast plate search and observation timeline reconstruction.
4. **Authorized Watchlist Alerting**: Flagging demo watchlist plates labeled strictly as *"Authorized Watchlist Match — Requires Human Review"*.

> **Note on Prototype Data**: All baseline cameras and initial observations are explicitly tagged with `[DEMO DATA]` badges to ensure compliance with prototype verification guidelines.

---

## 🏗️ Project Architecture

```
SIH 2026/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, CORS, routers
│   │   ├── config.py                # Environment & SQLite path configuration
│   │   ├── database.py              # SQLite engine & session provider
│   │   ├── models/                  # SQLAlchemy models (Camera, Vehicle, Detection, Alert)
│   │   ├── schemas/                 # Pydantic validation schemas (DTOs)
│   │   ├── routers/                 # REST API endpoints (/cameras, /detections, /trajectories, /analytics, /alerts)
│   │   └── services/
│   │       ├── trajectory_engine.py # Spatio-temporal association & Haversine distance/speed
│   │       └── analytics_engine.py  # 10-min interval flow aggregation & peak analytics
│   ├── seed_data.py                 # Seeds 4 cameras & rich multi-camera trajectories
│   ├── test_api.py                  # Automated backend API integration tests
│   └── requirements.txt
│
├── frontend/                        # Modern React + Vite Dashboard
│   ├── src/
│   │   ├── components/              # Navbar, Sidebar, TrajectoryMap (Leaflet), MetricCard, DemoBadge
│   │   ├── views/                   # DashboardView, VehicleSearchView, TrajectoryView, AnalyticsView, AlertsView
│   │   └── services/api.js          # REST Client
│   ├── package.json
│   └── vite.config.js
│
├── ai_cv/                           # Modular AI/CV package (Reserved for Phase 2 ANPR/OCR)
│   └── __init__.py
└── README.md
```

---

## 🚀 How to Run the Application

### 1. Start the Backend API (FastAPI)
```bash
# From workspace root:
# Install Python dependencies:
python -m pip install -r backend/requirements.txt

# (Optional) Re-seed synthetic database:
python backend/seed_data.py

# Run FastAPI server on port 8000:
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
* Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

---

### 2. Start the Frontend Dashboard (React + Vite)
```bash
# In a second terminal, navigate to frontend:
cd frontend

# Install Node dependencies:
npm install

# Start Vite development server:
npm run dev
```
* Dashboard URL: `http://localhost:3000`

---

## 🧪 Testing and Verification

To run the automated backend test suite:
```bash
python backend/test_api.py
```
This validates:
- `GET /` (Health & version info)
- `GET /api/cameras` (Verifies all 4 synthetic camera nodes)
- `GET /api/detections` (Recent vehicle sightings)
- `GET /api/trajectories/TS09AB1234` (Multi-camera sequence `CAM-01 -> CAM-04 -> CAM-07 -> CAM-09`)
- `GET /api/analytics/summary` (Temporal 10-min volume histogram & peak hour calculation)
- `GET /api/alerts` (Watchlist match notifications)

---

## 📋 Phase 0 & Phase 1 Scope vs Phase 2 Readiness

| Feature / Capability | Phase 0 & 1 (Current) | Phase 2 (Upcoming) |
| :--- | :--- | :--- |
| **System Architecture & Database** | ✅ Complete (FastAPI + SQLite + React) | Preserved & extended |
| **Interactive Leaflet Route Map** | ✅ Complete (Waypoints & Polylines) | Connected to live inference |
| **Multi-Camera Trajectory Engine** | ✅ Complete (Calculates $\Delta t$, distance, speeds) | Extended with CV re-id |
| **Macro Urban Traffic Analytics** | ✅ Complete (10-min buckets, peak load, modal share) | Fed by live streams |
| **Authorized Alerts Interface** | ✅ Complete (Human-in-the-loop review actions) | Fed by live detections |
| **Real Video ANPR / OCR Pipeline**| ⏳ Stubbed in `ai_cv/` | 🎯 Next: YOLO plate crop + OCR |
