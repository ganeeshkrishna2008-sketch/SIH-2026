import React, { useState, useEffect } from 'react';
import { Search, Car, Calendar, Navigation, ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';
import DemoDataBadge from '../components/DemoDataBadge';
import { fetchUniquePlates, fetchTrajectory } from '../services/api';

export default function VehicleSearchView({ initialPlate = '', onNavigateToTrajectory }) {
  const [plates, setPlates] = useState([]);
  const [searchPlate, setSearchPlate] = useState(initialPlate || 'TS09AB1234');
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const quickDemoPlates = ['TS09AB1234', 'DL01CZ4567', 'KA05MH8899', 'MH12TR3321', 'HR26DQ5544'];

  useEffect(() => {
    async function loadPlates() {
      try {
        const list = await fetchUniquePlates();
        setPlates(list);
      } catch (err) {
        console.error('Error fetching plates:', err);
      }
    }
    loadPlates();
  }, []);

  const handleSearch = async (plateToSearch) => {
    const target = (plateToSearch || searchPlate).trim().toUpperCase();
    if (!target) return;
    setSearchPlate(target);
    setLoading(true);
    setError(null);

    try {
      const data = await fetchTrajectory(target);
      if (data) {
        setTrajectoryData(data);
      } else {
        setTrajectoryData(null);
        setError(`No detection history found for license plate: ${target}`);
      }
    } catch (err) {
      setError(`Failed to retrieve vehicle data: ${err.message}`);
      setTrajectoryData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch(initialPlate || 'TS09AB1234');
  }, [initialPlate]);

  return (
    <div className="space-y-6">
      {/* Search Header Bar */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100">Vehicle Search & Observation History</h2>
              <DemoDataBadge />
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Query plate records to reconstruct chronological camera observations and transit timeline.
            </p>
          </div>
        </div>

        {/* Input Form & Quick Pills */}
        <div className="space-y-3 pt-2">
          <form onSubmit={(e) => { e.preventDefault(); handleSearch(searchPlate); }} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Enter Plate Number (e.g. TS09AB1234)..."
                value={searchPlate}
                onChange={(e) => setSearchPlate(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold transition flex items-center gap-2 shadow-lg shadow-sky-500/20 disabled:opacity-50"
            >
              <Search className="w-4 h-4" />
              <span>{loading ? 'Searching...' : 'Search'}</span>
            </button>
          </form>

          {/* Quick Demo Plates Pills */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-medium">Quick Demo Samples:</span>
            {quickDemoPlates.map((p) => (
              <button
                key={p}
                onClick={() => handleSearch(p)}
                className={`px-2.5 py-1 rounded-lg font-mono font-semibold transition ${
                  searchPlate === p
                    ? 'bg-sky-500 text-white border border-sky-400'
                    : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700 hover:text-white'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {trajectoryData && (
        <div className="space-y-6">
          {/* Vehicle Metadata Summary */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-sky-500/10 border border-sky-500/30 rounded-xl text-sky-400">
                  <Car className="w-7 h-7" />
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-mono font-bold text-white tracking-wide">
                      {trajectoryData.plate_number}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                      {trajectoryData.vehicle_type}
                    </span>
                    {trajectoryData.is_watchlist && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30 flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" />
                        Authorized Watchlist
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex flex-wrap gap-4">
                    <span>Total Observations: <strong className="text-slate-200">{trajectoryData.total_observations}</strong></span>
                    <span>First Detected: <strong className="text-slate-200 font-mono">{new Date(trajectoryData.first_seen).toLocaleTimeString()}</strong></span>
                    <span>Last Detected: <strong className="text-slate-200 font-mono">{new Date(trajectoryData.last_seen).toLocaleTimeString()}</strong></span>
                    <span>Total Span: <strong className="text-amber-400 font-mono">{trajectoryData.total_duration_minutes} mins</strong></span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => onNavigateToTrajectory(trajectoryData.plate_number)}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500 hover:text-slate-900 font-semibold text-xs transition shrink-0"
              >
                <Navigation className="w-4 h-4" />
                <span>Open Trajectory Map</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Chronological Observation Table */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Chronological Camera Observations
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                {trajectoryData.trajectory.length} Sightings Recorded
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Seq #</th>
                    <th className="py-2.5 px-3">Camera Node</th>
                    <th className="py-2.5 px-3">Location Name</th>
                    <th className="py-2.5 px-3">Direction</th>
                    <th className="py-2.5 px-3">Timestamp</th>
                    <th className="py-2.5 px-3">Transit Time</th>
                    <th className="py-2.5 px-3">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {trajectoryData.trajectory.map((step) => (
                    <tr key={step.step_number} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-3 font-mono font-bold">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs">
                          {step.step_number}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono text-sky-400 font-bold">
                        {step.camera_id} ({step.camera_name})
                      </td>
                      <td className="py-3 px-3 text-slate-200">{step.location_name}</td>
                      <td className="py-3 px-3 text-slate-400">{step.direction}</td>
                      <td className="py-3 px-3 font-mono text-slate-300">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-3 px-3 font-mono">
                        {step.time_diff_formatted ? (
                          <span className="text-amber-400 font-medium">
                            +{step.time_diff_formatted} ({step.distance_from_prev_km} km)
                          </span>
                        ) : (
                          <span className="text-slate-500 font-sans italic">Origin point</span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-mono">
                        <span className="text-emerald-400 font-semibold">
                          {(step.confidence * 100).toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
