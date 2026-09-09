import React, { useState, useEffect } from "react";
import { Camera, Clock, Navigation, CheckCircle2, Search, ArrowRight } from "lucide-react";
import DemoDataBadge from "../components/DemoDataBadge";
import { fetchCameras, fetchCameraVehicles } from "../services/api";
import { mapVehicleType } from "../utils/vehicleType";

export default function CameraActivityView({ onNavigateToVehicleHistory }) {
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState("");
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadCameras() {
      try {
        const list = await fetchCameras();
        setCameras(list);
        if (list.length > 0) {
          setSelectedCamera(list[0].camera_id);
          fetchActivity(list[0].camera_id);
        }
      } catch (err) {
        console.error("Error fetching cameras:", err);
        setError("Failed to load cameras.");
      }
    }
    loadCameras();
  }, []);

  const fetchActivity = async (cameraId) => {
    if (!cameraId) return;
    setLoading(true);
    setError(null);
    setActivityData(null);
    
    try {
      const data = await fetchCameraVehicles(cameraId);
      if (data) {
        setActivityData(data);
      } else {
        setError(`No vehicle history found for camera: ${cameraId}`);
      }
    } catch (err) {
      console.error(err);
      setError(`Failed to fetch activity for camera: ${cameraId}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCameraChange = (e) => {
    const camId = e.target.value;
    setSelectedCamera(camId);
    fetchActivity(camId);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Camera className="text-blue-600" /> Camera Activity
          </h2>
          <p className="text-gray-600 dark:text-gray-400">View chronological vehicle history for a specific camera</p>
        </div>
        <DemoDataBadge />
      </div>

      <div className="bg-slate-900/60 p-6 rounded-xl border border-slate-800 shadow-sm">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Select Camera
        </label>
        <select
          value={selectedCamera}
          onChange={handleCameraChange}
          className="w-full md:w-1/2 p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 focus:ring-2 focus:ring-sky-500 outline-none"
        >
          {cameras.map(cam => (
            <option key={cam.camera_id} value={cam.camera_id}>
              {cam.camera_id} — {cam.name || cam.location_name}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="space-y-6 animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900/60 h-24 rounded-xl border border-slate-800"></div>
            <div className="bg-slate-900/60 h-24 rounded-xl border border-slate-800"></div>
          </div>
          <div className="bg-slate-900/60 h-64 rounded-xl border border-slate-800"></div>
        </div>
      )}

      {error && !loading && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl flex items-start gap-3">
          <Search className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {activityData && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900/60 p-6 rounded-xl border border-slate-800 shadow-sm flex items-center gap-4">
              <div className="bg-sky-500/10 p-3 rounded-full text-sky-400 border border-sky-500/20">
                <Camera className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Detections</p>
                <p className="text-2xl font-bold text-slate-100 tabular-nums tracking-tight">{activityData.total_detections}</p>
              </div>
            </div>
            
            <div className="bg-slate-900/60 p-6 rounded-xl border border-slate-800 shadow-sm flex items-center gap-4">
              <div className="bg-emerald-500/10 p-3 rounded-full text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Unique Vehicles</p>
                <p className="text-2xl font-bold text-slate-100 tabular-nums tracking-tight">{activityData.unique_vehicles}</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/60 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-950">
              <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                <Clock className="h-5 w-5 text-slate-400" />
                Chronological Vehicle Observations
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800">
                <thead className="bg-slate-950">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Plate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Confidence</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Direction</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-slate-900/60 divide-y divide-slate-800">
                  {activityData.vehicles.map((v, i) => (
                    <tr key={i} className="hover:bg-slate-800/40 transition-colors duration-200">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300 tabular-nums">
                        {new Date(v.timestamp).toLocaleTimeString([], {hour: "2-digit", minute:"2-digit", second:"2-digit"})}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 font-mono font-bold text-sm border border-amber-500/20">
                          {v.plate_number}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                        {mapVehicleType(v.vehicle_type)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium tabular-nums ${
                          v.confidence > 0.9 
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}>
                          {(v.confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                        <div className="flex items-center gap-1">
                          <Navigation className="h-3 w-3" />
                          {v.direction}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => onNavigateToVehicleHistory && onNavigateToVehicleHistory(v.normalized_plate)}
                          className="text-sky-400 hover:text-sky-300 transition-colors duration-200 flex items-center justify-end gap-1 w-full"
                        >
                          View History <ArrowRight className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {activityData.vehicles.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-12">
                        <div className="flex flex-col items-center justify-center text-slate-400">
                          <Camera className="w-10 h-10 mb-3 text-slate-600" />
                          <h4 className="text-lg font-medium text-slate-300">No Vehicles Detected</h4>
                          <p className="text-sm mt-1">This camera has not recorded any vehicle activity yet.</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
