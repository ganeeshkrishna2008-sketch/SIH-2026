SIH26127 — PROTOTYPE IMPLEMENTATION PLAN

City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking and Urban Traffic Analytics

Practical MVP plan for Antigravity • Focus: ANPR/OCR + Multi-Camera Trajectory + Traffic Analytics

1. Prototype Goal

Build a working, demo-ready prototype that demonstrates the three core capabilities described in SIH26127: (1) ANPR/OCR, (2) single-plate trajectory tracking across multiple cameras, and (3) macro traffic-flow and movement analytics. The prototype should prioritize a reliable end-to-end demonstration over unnecessary advanced features.

2. Core Demonstration

The complete demo flow must be:

Authorized video/camera input → Vehicle detection → Number-plate detection → OCR/ANPR → Vehicle observation → Cross-camera association → Trajectory → Location/timestamp display → Traffic analytics

3. Scope: MUST HAVE vs OPTIONAL

MUST HAVE — ANPR/OCR: process a controlled/authorized test video and produce a vehicle/plate observation.

MUST HAVE — Multi-camera trajectory: show the same plate observed at multiple cameras in chronological order.

MUST HAVE — Time/location history: display camera, location, timestamp and direction for the selected vehicle.

MUST HAVE — Simple map: show camera locations and, preferably, connect the selected vehicle's observed route.

MUST HAVE — Traffic analytics: table/chart showing vehicle counts by camera and by time interval.

OPTIONAL — Authorized watchlist alert: simple match against a demo watchlist and mark it for human review.

NOT REQUIRED for MVP — predictive policing, facial recognition, complex traffic prediction, full city-wide CCTV integration, sophisticated GIS, cloud-scale deployment, or movement prediction.

4. Phase 0 — Project Inspection & Architecture

Inspect the existing Antigravity project before creating files.

Create a clean modular structure for frontend, backend, AI/CV processing, data and configuration.

Choose a practical stack based on what is already installed. Prefer Python for AI/backend and a simple web UI if that speeds up the MVP.

Create a README with setup and run instructions.

Do not build the whole system in one step; complete and test each phase before moving on.

5. Phase 1 — Demo Data & Dashboard

Goal: get the complete UI working before integrating AI.

Create synthetic/demo camera data for 3–4 cameras.

Create synthetic vehicle observations for several vehicles.

Each observation must contain: plate number, camera ID, timestamp, location, direction, vehicle type and confidence.

Create a dashboard showing connected cameras, total observations, vehicle counts and recent detections.

Create a vehicle-search page where selecting a plate displays its complete observation history.

Clearly label synthetic information as DEMO DATA.

Example trajectory:

TS09AB1234 → CAM-01 → CAM-04 → CAM-07 → CAM-09

Each observation has its own timestamp and location.

6. Phase 2 — ANPR/OCR

Goal: replace/augment synthetic observations with actual observations from an authorized test video.

Accept an authorized local test video.

Detect vehicles using a suitable object-detection model.

Detect/crop number plates using a suitable plate detector.

Run OCR on the plate crop.

Return plate text and confidence.

Store each observation with timestamp and camera ID.

Handle low-confidence OCR conservatively; do not invent or silently correct plate numbers.

Display the original video and/or annotated detection result where practical.

Validate on a small controlled dataset before making accuracy claims.

Do not claim the SIH target accuracy unless the team has actually tested and measured it.

7. Phase 3 — Multi-Camera Vehicle Association

Goal: connect observations of the same vehicle across cameras.

Start with exact/normalized plate matching for the MVP.

Add timestamp ordering.

Add camera location/direction constraints to reject obviously impossible matches.

Structure the code so future vehicle-attribute/re-identification features can be added.

Do not claim perfect identity matching.

MVP example:

09:02 — CAM-01 — TS09AB1234

09:09 — CAM-04 — TS09AB1234

09:16 — CAM-07 — TS09AB1234

09:25 — CAM-09 — TS09AB1234

8. Phase 4 — Trajectory Reconstruction

Sort observations by timestamp.

Group observations by vehicle/plate.

Generate a trajectory containing camera sequence, timestamps, locations and directions.

Calculate simple travel intervals between consecutive camera observations.

Display the trajectory as a clear table.

Add a simple map with camera markers and a line joining the selected vehicle's observations if feasible.

The table is the primary evidence; the map is a simple visual representation of the route, not a complex GIS platform.

9. Phase 5 — Traffic Analytics

Goal: satisfy the macro traffic-flow/movement analytics requirement with simple, understandable analytics.

Count vehicles per camera.

Count vehicles per time interval.

Show a table such as 09:00–09:10 → 63 vehicles; 09:10–09:20 → 93 vehicles.

Add a simple line/bar chart for vehicle count over time.

Show busiest camera and peak time interval.

Optionally calculate simple route/corridor counts.

Do not build predictive traffic AI for the MVP.

10. Phase 6 — Authorized Alerts (Optional)

This is an additional expected capability, not the main focus. Implement only after the three core requirements work.

Create a small DEMO authorized watchlist.

If a detected plate matches, create an alert containing plate, camera, timestamp and confidence.

Label the alert as 'Authorized Watchlist Match — Requires Human Review'.

Do not identify or accuse a person.

Do not build facial recognition or person tracking.

11. Final Prototype Screens

1. Dashboard — overall traffic and detection summary.

2. ANPR/Video — authorized test video with vehicle/plate observations.

3. Vehicle Search — select a plate and view its observations.

4. Trajectory — timestamp/location/direction table plus simple route map.

5. Traffic Analytics — vehicle counts by time interval and camera.

6. Alerts — optional authorized watchlist matches.

12. Suggested Technical Architecture

Use the simplest reliable architecture that the team can finish. A recommended structure is:

Video/Input → CV/ANPR service → Observation records → Association/Trajectory engine → Analytics API → Web dashboard

AI/CV: Python, OpenCV, PyTorch, YOLO-family detector, OCR library such as EasyOCR/PaddleOCR.

Backend: FastAPI or another lightweight Python API.

Database: SQLite for the first MVP; PostgreSQL/PostGIS only if needed for the final architecture/demo.

Frontend: React if the team is comfortable with it; otherwise Streamlit is acceptable for a fast MVP.

Map: Leaflet/OpenStreetMap or another simple map component.

13. Data Model

cameras: camera_id, camera_name, latitude, longitude, direction

vehicles: vehicle_id, plate_number, vehicle_type

detections: detection_id, camera_id, vehicle_id/plate, timestamp, confidence, location

trajectories: vehicle_id, ordered observations, start_time, end_time

alerts (optional): plate/vehicle_id, camera_id, timestamp, alert_type, status

14. Testing Checklist

Test one vehicle across 3–4 demo cameras.

Test multiple vehicles with different plates.

Test repeated observations of the same vehicle.

Test missing observations at one camera.

Test low-confidence OCR.

Verify timestamps remain correctly ordered.

Verify traffic counts match the underlying observation records.

Verify the selected vehicle's route changes when another vehicle is selected.

Run the complete demo from input to dashboard without manual database editing.

15. SIH Demo Scenario

Use one simple story for the final demonstration:

1. Start with an authorized traffic video/demo feed.

2. System detects a vehicle and obtains its plate through ANPR/OCR.

3. The observation is stored with camera and timestamp.

4. The same plate is observed at CAM-04 and CAM-07.

5. Vehicle Search displays the complete time/location history.

6. Trajectory view shows CAM-01 → CAM-04 → CAM-07 on the simple map.

7. Traffic Analytics shows vehicle counts by camera and time interval.

8. If implemented, an authorized watchlist match generates a human-review alert.

16. Antigravity Working Rules

Build incrementally and test after every phase.

Do not replace working components with more complex technology without a reason.

Do not create fake AI results and present them as real detections.

Demo/synthetic data must be clearly labeled.

Do not invent performance metrics.

Do not claim city-scale deployment unless it has actually been tested.

Keep configuration separate from source code.

Keep the code modular so ANPR, trajectory and analytics can be independently improved.

Prioritize a working end-to-end MVP over visual complexity.

17. Definition of Done

The MVP is complete when a judge can select or observe a vehicle and see: (1) its plate, (2) where and when it was observed, (3) its sequence across multiple cameras, (4) its reconstructed route, and (5) how the observations contribute to city traffic counts/analytics.