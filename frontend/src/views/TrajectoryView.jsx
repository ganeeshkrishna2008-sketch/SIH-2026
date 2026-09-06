import React, { useState, useEffect } from 'react';
import { Navigation, MapPin, Clock, ArrowRight, ShieldAlert, Sparkles, Gauge } from 'lucide-react';
import TrajectoryMap from '../components/TrajectoryMap';
import DemoDataBadge from '../components/DemoDataBadge';
import { fetchCameras, fetchTrajectory, fetchUniquePlates } from '../services/api';

export default function TrajectoryView({ selectedPlate = 'TS09AB1234' }) {
  const [activePlate, setActivePlate] = useState(selectedPlate);
  const [cameras, setCameras] = useState([]);
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [plates, setPlates] = useState([]);
  const [loading, setLoading] = useState(true);

  const demoPresets = ['TS09AB1234', 'DL01CZ4567', 'KA05MH8899'];

  useEffect(() => {
    async function init() {
      try {
        const [cams, plateList] = await Promise.all([
          fetchCameras(),
          fetchUniquePlates()
        ]);
        setCameras(cams);
        setPlates(plateList);
      } catch (err) {
        console.error('Error initializing trajectory view:', err);
      }
    }
    init();
  }, []);

  useEffect(() => {
    async function loadTrajectory() {
      if (!activePlate) return;
      try {
        setLoading(true);
        const data = await fetchTrajectory(activePlate);
        setTrajectoryData(data);
      } catch (err) {
        console.error('Error loading trajectory:', err);
      } finally {
        setLoading(false);
      }
    }
    loadTrajectory();
  }, [activePlate]);

  return (
    <div className="space-y-6">
      {/* Top Header & Plate Switcher */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100">Multi-Camera Trajectory Reconstruction</h2>
              <DemoDataBadge />
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Cross-camera plate association, spatio-temporal validation, transit duration, and geometric route mapping.
            </p>
          </div>

          {/* Vehicle Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Select Vehicle:</span>
            <div className="flex gap-1.5">
              {demoPresets.map((p) => (
                <button
                  key={p}
                  onClick={() => setActivePlate(p)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
                    activePlate === p
                      ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                      : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Route Chain Representation Banner */}
        {trajectoryData && (
          <div className="p-3.5 bg-slate-950 border border-slate-800/90 rounded-xl flex flex-wrap items-center gap-2 text-xs">
            <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
              Observed Trajectory Sequence:
            </span>
            <span className="font-mono font-bold text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/30">
              {trajectoryData.plate_number}
            </span>
            {trajectoryData.trajectory.map((step, idx) => (
              <React.Fragment key={`seq-${step.camera_id}-${step.step_number}`}>
                <span className="text-slate-600 font-bold">→</span>
                <span className="font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700">
                  {step.camera_id}
                </span>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Main Grid: Left Steps Breakdown, Right Interactive Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Timeline Steps (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Transit Step Breakdown
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {trajectoryData?.trajectory?.length || 0} Camera Nodes
              </span>
            </div>

            {loading ? (
              <div className="py-12 text-center text-xs text-slate-500 animate-pulse">
                Calculating trajectory coordinates...
              </div>
            ) : trajectoryData ? (
              <div className="space-y-3 relative before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
                {trajectoryData.trajectory.map((step) => (
                  <div
                    key={`step-card-${step.step_number}`}
                    className="relative pl-8 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-amber-500/40 transition group"
                  >
                    {/* Numbered Indicator */}
                    <div className="absolute left-1 top-3 -translate-x-1/2 w-5 h-5 rounded-full bg-amber-500 text-slate-950 font-mono font-black text-[11px] flex items-center justify-center shadow">
                      {step.step_number}
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sky-400 font-mono text-xs">
                        {step.camera_id} • {step.camera_name}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <div className="text-xs text-slate-300 mt-1 font-medium">{step.location_name}</div>
                    
                    <div className="mt-2 pt-2 border-t border-slate-900 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Facing: <strong className="text-slate-300">{step.direction}</strong></span>
                      {step.time_diff_formatted ? (
                        <span className="text-amber-400 font-medium">
                          +{step.time_diff_formatted} ({step.distance_from_prev_km} km @ {step.estimated_speed_kmh} km/h)
                        </span>
                      ) : (
                        <span className="text-emerald-400 italic">Starting Node</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-400 py-6 text-center">No trajectory loaded</div>
            )}
          </div>
        </div>

        {/* Right Column: Interactive Leaflet Map (7 cols) */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex-1 flex flex-col space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                  Reconstructed Trajectory Route Map
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                  {activePlate}
                </span>
              </div>
              <span className="text-xs text-slate-400">Leaflet / OpenStreetMap</span>
            </div>

            <div className="flex-1 min-h-[460px]">
              <TrajectoryMap
                cameras={cameras}
                trajectorySteps={trajectoryData?.trajectory || []}
                selectedPlate={activePlate}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
