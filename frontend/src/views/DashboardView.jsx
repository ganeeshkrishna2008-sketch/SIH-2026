import React, { useState, useEffect } from 'react';
import { Camera, Car, Activity, Zap, ArrowUpRight, Search, Clock } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import DemoDataBadge from '../components/DemoDataBadge';
import { fetchCameras, fetchDetections, fetchAnalyticsSummary } from '../services/api';
import { mapVehicleType } from '../utils/vehicleType';

export default function DashboardView({ onSelectPlate }) {
  const [cameras, setCameras] = useState([]);
  const [recentDetections, setRecentDetections] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [cams, dets, summary] = await Promise.all([
          fetchCameras(),
          fetchDetections(15),
          fetchAnalyticsSummary(),
        ]);
        setCameras(cams);
        setRecentDetections(dets);
        setAnalytics(summary);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredDetections = recentDetections.filter(d => 
    d.plate_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.camera_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium">Loading Dashboard Data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100">Urban Traffic & Multi-Camera Monitoring</h2>
            <DemoDataBadge />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time feed aggregation, camera grid status, and synchronized vehicle observation telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>Active Window: 09:00 - 10:00 UTC</span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Cameras"
          value={analytics?.active_cameras || cameras.length}
          subtitle="4 nodes operational"
          icon={Camera}
          color="sky"
        />
        <MetricCard
          title="Total Observations"
          value={analytics?.total_detections || 0}
          subtitle="Processed frames"
          icon={Activity}
          color="emerald"
        />
        <MetricCard
          title="Unique Vehicles"
          value={analytics?.unique_vehicles || 0}
          subtitle="Tracked plates"
          icon={Car}
          color="purple"
        />
        <MetricCard
          title="Peak Traffic Window"
          value={analytics?.peak_time_interval?.interval || '09:10 - 09:20'}
          subtitle={`${analytics?.peak_time_interval?.count || 0} detections (Peak load)`}
          icon={Zap}
          color="amber"
        />
      </div>

      {/* Connected Cameras Status Grid */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Connected Camera Nodes (4 Synthetic Nodes)
          </h3>
          <span className="text-xs text-slate-400">All Nodes Online</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {cameras.map((cam) => (
            <div
              key={cam.camera_id}
              className="bg-slate-950 border border-slate-800/80 rounded-lg p-4 space-y-2 hover:border-slate-700 transition"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sky-400 font-mono text-sm">{cam.camera_id}</span>
                <span className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  {cam.status}
                </span>
              </div>
              <div className="text-sm font-medium text-slate-200 truncate" title={cam.name}>
                {cam.name}
              </div>
              <div className="text-xs text-slate-400 truncate">{cam.location_name}</div>
              <div className="pt-2 border-t border-slate-900 flex justify-between items-center text-[11px] text-slate-400">
                <span>Facing: <strong className="text-slate-300">{cam.direction}</strong></span>
                <span className="font-mono text-slate-400">{cam.latitude.toFixed(2)}, {cam.longitude.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Detections Stream Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Live Observation Feed
            </h3>
            <p className="text-xs text-slate-400">Recent vehicle detections across all connected camera nodes</p>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by plate or camera..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-64"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Plate Number</th>
                <th className="py-2.5 px-3">Camera Node</th>
                <th className="py-2.5 px-3">Location</th>
                <th className="py-2.5 px-3">Direction</th>
                <th className="py-2.5 px-3">Vehicle Type</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filteredDetections.map((det) => (
                <tr key={det.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 font-mono font-bold text-sky-400">
                    {det.plate_number}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-300">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {det.camera_id}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">{det.location_name}</td>
                  <td className="py-2.5 px-3 text-slate-400">{det.direction}</td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                      {mapVehicleType(det.vehicle_type)}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-400">
                    {new Date(det.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-2.5 px-3 font-mono">
                    <span className={`font-semibold ${
                      det.confidence >= 0.95 ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {(det.confidence * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => onSelectPlate(det.plate_number)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded bg-sky-500/10 text-sky-400 border border-sky-500/30 hover:bg-sky-500 hover:text-white transition"
                    >
                      Track Route
                      <ArrowUpRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
