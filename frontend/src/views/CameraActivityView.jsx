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

      <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Camera
        </label>
        <select
          value={selectedCamera}
          onChange={handleCameraChange}
          className="w-full md:w-1/2 p-3 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
        >
          {cameras.map(cam => (
            <option key={cam.camera_id} value={cam.camera_id}>
              {cam.camera_id} � {cam.name || cam.location_name}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-500">Fetching camera activity...</span>
        </div>
      )}

      {error && !loading && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 p-4 rounded-xl flex items-start gap-3">
          <Search className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {activityData && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm flex items-center gap-4">
              <div className="bg-blue-100 dark:bg-blue-900/50 p-3 rounded-full text-blue-600 dark:text-blue-400">
                <Camera className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Detections</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{activityData.total_detections}</p>
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm flex items-center gap-4">
              <div className="bg-green-100 dark:bg-green-900/50 p-3 rounded-full text-green-600 dark:text-green-400">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Unique Vehicles</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{activityData.unique_vehicles}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <h3 className="font-semibold text-gray-800 dark:text-white flex items-center gap-2">
                <Clock className="h-5 w-5 text-gray-500" />
                Chronological Vehicle Observations
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Plate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Confidence</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Direction</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {activityData.vehicles.map((v, i) => (
                    <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-300">
                        {new Date(v.timestamp).toLocaleTimeString([], {hour: "2-digit", minute:"2-digit", second:"2-digit"})}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2.5 py-1 rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-500 font-mono font-bold text-sm border border-yellow-200 dark:border-yellow-700/50">
                          {v.plate_number}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-400">
                        {mapVehicleType(v.vehicle_type)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          v.confidence > 0.9 
                            ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" 
                            : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
                        }`}>
                          {(v.confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                          <Navigation className="h-3 w-3" />
                          {v.direction}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => onNavigateToVehicleHistory && onNavigateToVehicleHistory(v.normalized_plate)}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 flex items-center justify-end gap-1 w-full"
                        >
                          View History <ArrowRight className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {activityData.vehicles.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                        No vehicle observations recorded for this camera.
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
