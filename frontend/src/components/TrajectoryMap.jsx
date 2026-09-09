import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';

// Component to dynamically fit bounds when trajectory or cameras change
function AutoFitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points && points.length > 0) {
      const bounds = L.latLngBounds(points.map(p => [p.latitude, p.longitude]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [points, map]);
  return null;
}

// Component to invalidate size when map container dimensions change (e.g. from display: none to display: block)
function AutoInvalidateSize() {
  const map = useMap();
  useEffect(() => {
    if (!map) return;
    const observer = new ResizeObserver(() => {
      map.invalidateSize();
    });
    observer.observe(map.getContainer());
    return () => {
      observer.disconnect();
    };
  }, [map]);
  return null;
}

const TrajectoryMap = React.memo(function TrajectoryMap({ cameras = [], trajectorySteps = [], selectedPlate = null }) {
  const center = [17.3850, 78.4867];
  const [mapStatus, setMapStatus] = useState('loading'); // 'loading', 'loaded', 'error'

  // Create custom marker icons using L.divIcon
  const createCameraIcon = (cameraId) => {
    return L.divIcon({
      className: 'custom-camera-pin',
      html: `
        <div style="
          background: #0284c7;
          color: #ffffff;
          font-weight: bold;
          font-size: 10px;
          padding: 4px 6px;
          border-radius: 6px;
          border: 2px solid #38bdf8;
          box-shadow: 0 4px 10px rgba(0,0,0,0.5);
          white-space: nowrap;
          display: flex;
          align-items: center;
          gap: 3px;
        ">
          📷 ${cameraId}
        </div>
      `,
      iconSize: [60, 24],
      iconAnchor: [30, 12],
    });
  };

  const createStepIcon = (stepNumber) => {
    return L.divIcon({
      className: 'custom-step-pin',
      html: `
        <div style="
          background: #f59e0b;
          color: #0f172a;
          font-weight: 800;
          font-size: 12px;
          width: 26px;
          height: 26px;
          border-radius: 50%;
          border: 3px solid #ffffff;
          box-shadow: 0 4px 12px rgba(245,158,11,0.7);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          ${stepNumber}
        </div>
      `,
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });
  };

  const polylinePositions = useMemo(() => {
    if (!trajectorySteps || trajectorySteps.length === 0) return [];
    return trajectorySteps.map(step => [step.latitude, step.longitude]);
  }, [trajectorySteps]);

  const fitPoints = useMemo(() => {
    if (trajectorySteps && trajectorySteps.length > 0) return trajectorySteps;
    return cameras;
  }, [trajectorySteps, cameras]);

  return (
    <div className="w-full h-full min-h-[420px] rounded-xl overflow-hidden border border-slate-800 shadow-inner relative z-0 bg-slate-900">
      
      {/* State Overlays */}
      {mapStatus === 'loading' && (
        <div className="absolute inset-0 z-[2000] bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center transition-opacity duration-300 pointer-events-none">
          <div className="flex flex-col items-center gap-3 px-6 py-4 bg-slate-950/80 border border-slate-800 rounded-2xl shadow-2xl">
            <div className="w-6 h-6 border-2 border-sky-500/30 border-t-sky-500 rounded-full animate-spin"></div>
            <div className="text-xs font-semibold text-sky-400 tracking-wider uppercase">Loading map...</div>
          </div>
        </div>
      )}

      {mapStatus === 'error' && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[2000] pointer-events-none">
          <div className="bg-slate-950/90 border border-amber-500/30 px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></div>
            <span className="text-xs font-medium text-amber-400">Map tiles temporarily unavailable - showing route data only</span>
          </div>
        </div>
      )}

      <MapContainer
        center={center}
        zoom={11}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', background: '#0f172a' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{
            loading: () => setMapStatus('loading'),
            load: () => setMapStatus('loaded'),
            tileerror: () => setMapStatus('error')
          }}
        />

        <AutoFitBounds points={fitPoints} />
        <AutoInvalidateSize />

        {/* Camera Base Markers */}
        {cameras.map((cam) => (
          <Marker
            key={cam.camera_id}
            position={[cam.latitude, cam.longitude]}
            icon={createCameraIcon(cam.camera_id)}
          >
            <Popup>
              <div className="text-xs space-y-1 p-1">
                <div className="font-bold text-sky-400 text-sm">{cam.name}</div>
                <div className="text-slate-300">{cam.location_name}</div>
                <div className="text-slate-400">Direction: <span className="text-slate-200">{cam.direction}</span></div>
                <div className="text-slate-400">Coordinates: <span className="font-mono text-slate-300">{cam.latitude.toFixed(4)}, {cam.longitude.toFixed(4)}</span></div>
                <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                  {cam.status}
                </span>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Trajectory Route Polyline */}
        {polylinePositions.length > 1 && (
          <Polyline
            positions={polylinePositions}
            pathOptions={{
              color: '#f59e0b',
              weight: 4,
              opacity: 0.9,
              dashArray: '8, 8',
              lineCap: 'round',
            }}
          />
        )}

        {/* Trajectory Step Markers */}
        {trajectorySteps.map((step) => (
          <Marker
            key={`step-${step.step_number}-${step.camera_id}`}
            position={[step.latitude, step.longitude]}
            icon={createStepIcon(step.step_number)}
          >
            <Popup>
              <div className="text-xs space-y-1.5 p-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-bold text-amber-400 text-sm">Step #{step.step_number}</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 font-mono text-[10px]">
                    {step.camera_id}
                  </span>
                </div>
                <div className="font-semibold text-slate-100">{step.location_name}</div>
                <div className="text-slate-400">Timestamp: <span className="text-slate-200 font-mono">{new Date(step.timestamp).toLocaleTimeString()}</span></div>
                <div className="text-slate-400">Direction: <span className="text-slate-200">{step.direction}</span></div>
                <div className="text-slate-400">Confidence: <span className="text-emerald-400 font-mono">{(step.confidence * 100).toFixed(1)}%</span></div>
                {step.time_diff_formatted && (
                  <div className="text-slate-400 border-t border-slate-800 pt-1">
                    Transit Time: <span className="text-amber-300 font-medium">{step.time_diff_formatted}</span>
                    {step.distance_from_prev_km && (
                      <span className="text-slate-400 ml-1">({step.distance_from_prev_km} km @ {step.estimated_speed_kmh} km/h)</span>
                    )}
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-lg p-3 text-xs text-slate-300 space-y-1.5 z-[1000] shadow-xl pointer-events-none">
        <div className="font-semibold text-slate-200 mb-1 border-b border-slate-800 pb-1">Map Legend</div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-sky-500 border border-sky-300"></span>
          <span>Camera Nodes ({cameras.length})</span>
        </div>
        {selectedPlate && (
          <>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-amber-500 border border-white"></span>
              <span>Observed Waypoints</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-0.5 border-t-2 border-dashed border-amber-500"></span>
              <span className="font-mono">{selectedPlate} Route</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
});

export default TrajectoryMap;
