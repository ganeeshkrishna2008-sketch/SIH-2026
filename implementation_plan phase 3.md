# Phase 3 — Multi-Camera Vehicle Association

## Existing Phase 0–2 Architecture (Findings)

The current project has a clean, working architecture:

- **Backend**: FastAPI + SQLAlchemy + SQLite ([main.py](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/app/main.py))
- **Frontend**: React 19 + Vite + Tailwind CSS + Leaflet + Recharts
- **AI/CV**: OpenCV + EasyOCR pipeline in `ai_cv/`

**Data Models** (SQLite):
- `Camera`: camera_id, name, location_name, lat/lon, direction, status
- `Vehicle`: plate_number, vehicle_type, color, is_watchlist
- `Detection`: camera_id, plate_number, vehicle_type, confidence, lat/lon, timestamp, location_name, direction, is_demo
- `Alert`: plate_number, camera_id, alert_type, status

**Key Observation**: The existing `TrajectoryEngine` already does plate-based grouping to reconstruct trajectories — it queries all `Detection` rows matching a plate and orders them chronologically. However, it has **no formal association layer** — it simply queries by exact plate match. There is no `VehicleTrack` model, no plate normalization, no temporal/spatial plausibility checks, and no concept of a "vehicle track ID".

Phase 3 adds the **formal multi-camera association layer** between raw detections and trajectory display.

---

## Proposed Changes

### Backend — New Association Service

#### [NEW] [association_engine.py](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/app/services/association_engine.py)

Core Phase 3 logic:

1. **Plate Normalization**: `normalize_plate()` — uppercase, strip spaces/hyphens/dots, remove non-alphanumeric chars
2. **`VehicleTrack`** data class — groups observations by normalized plate, assigns a track ID (e.g. `VT-001`), retains all metadata
3. **Temporal/Spatial Plausibility Check**: `is_transition_plausible()` — given two observations at different cameras, check if the time gap is within a configurable window (e.g. 1 min to 120 min) and if the implied speed is plausible (e.g. < 200 km/h). Uses existing Haversine distance.
4. **`associate_observations()`** — main function that:
   - Loads all detections from DB
   - Normalizes plates
   - Groups by normalized plate
   - Within each group, orders chronologically
   - Validates transitions between consecutive observations using plausibility checks
   - Splits into separate tracks if a transition is implausible (e.g. same plate, but 12 hours apart → different journey)
   - Returns list of `VehicleTrack` objects
5. **`search_vehicle(plate)`** — searches for a specific vehicle's track with all cross-camera observations
6. **Configurable thresholds** — all temporal/spatial limits as module-level constants, easy to tune

#### [NEW] [association.py (schema)](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/app/schemas/association.py)

Pydantic schemas for the association API response:
- `AssociationObservation`: camera_id, camera_name, timestamp, lat/lon, confidence, vehicle_type, direction, location_name, transit_time, distance_km, speed_kmh, plausibility_status
- `VehicleTrackResponse`: track_id, normalized_plate, vehicle_type, observations list, total_cameras, first_seen, last_seen, association_method

#### [NEW] [associations.py (router)](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/app/routers/associations.py)

New API endpoints:
- `GET /api/associations/tracks` — returns all vehicle tracks with cross-camera associations
- `GET /api/associations/tracks/{plate}` — returns a specific vehicle's track (by plate search)
- `GET /api/associations/search?q=TS09AB` — fuzzy plate search returning matching tracks
- `GET /api/associations/stats` — association summary stats (total tracks, multi-camera count, single-camera count)

#### [MODIFY] [main.py](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/app/main.py)
- Register the new `associations_router`
- Update phase label to "Phase 3"

#### [MODIFY] [__init__.py (routers)](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/app/routers/__init__.py)
- Import and export `associations_router`

---

### Backend — Multi-Camera Demo Data

#### [NEW] [seed_multicam.py](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/seed_multicam.py)

Generates clearly labelled synthetic multi-camera test data with:
- **6 cameras** (adds CAM-02, CAM-05 to existing 4)
- **Vehicle A** (TS09AB1234): CAM-01 → CAM-04 → CAM-07 (plausible times)
- **Vehicle B** (DL01CZ4567): CAM-02 → CAM-05 (plausible times)
- **Vehicle C** (KA05MH8899): CAM-01 → CAM-07 (plausible times)
- **Vehicle D with OCR variants**: "TS 09 AB 1234" and "TS09AB1234" should merge
- **Implausible transition**: same plate at two far cameras within 30 seconds → should NOT merge into same journey segment
- **Distinct vehicles** that should remain separate

Preserves existing seed data structure and simply adds additional Phase 3 demo records.

---

### Backend — Tests

#### [NEW] [test_phase3.py](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/backend/test_phase3.py)

Tests for:
1. Same plate at multiple cameras → correctly associated
2. Different plates → remain separate tracks
3. OCR formatting normalization (spaces, hyphens) → correctly unified
4. Implausible temporal/spatial transition → handled per rules
5. Phase 2 ANPR workflow still works (health check)
6. Vehicle search returns chronological cross-camera observations

---

### Frontend — Vehicle Search Enhancement

#### [MODIFY] [api.js](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/frontend/src/services/api.js)
- Add `fetchVehicleTracks()`, `fetchVehicleTrack(plate)`, `searchVehicleTracks(query)`, `fetchAssociationStats()`

#### [MODIFY] [VehicleSearchView.jsx](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/frontend/src/views/VehicleSearchView.jsx)
- Integrate with the new association API to show track-based cross-camera results
- Display track ID, normalized plate, and association metadata
- Keep existing UI structure, just enhance the data source

#### [MODIFY] [Sidebar.jsx](file:///c:/Users/Bala/OneDrive/Documents/SIH%202026/frontend/src/components/Sidebar.jsx)
- Update phase indicator from "Phase 0/1" to "Phase 3"

---

## What Is NOT Changed

- `Detection` model — unchanged (no schema migration needed)
- `Camera` model — unchanged 
- `Vehicle` model — unchanged
- `TrajectoryEngine` — unchanged (still works for existing trajectory view)
- `AnalyticsEngine` — unchanged
- `ANPRView` — unchanged
- Phase 2 ANPR pipeline — unchanged
- All existing API endpoints — unchanged

## Verification Plan

### Automated Tests
```bash
python backend/test_phase3.py
```
Tests all 6 required test cases.

### Manual Verification
1. Run `python backend/seed_multicam.py` to load demo data
2. Start backend: `python -m uvicorn app.main:app --app-dir backend --port 8000`
3. Start frontend: `cd frontend && npm run dev`
4. Open dashboard → Vehicle Search → enter "TS09AB1234"
5. Verify cross-camera timeline: CAM-01 → CAM-04 → CAM-07
6. Verify different vehicles remain separate
7. Verify existing Phase 2 ANPR page still works
