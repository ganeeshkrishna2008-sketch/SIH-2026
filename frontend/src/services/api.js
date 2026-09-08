const API_BASE = '/api';

export const fetchCameras = async () => {
  const res = await fetch(`${API_BASE}/cameras`);
  if (!res.ok) throw new Error('Failed to fetch cameras');
  return res.json();
};

export const fetchDetections = async (limit = 50, camera_id = '', plate_number = '') => {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  if (camera_id) params.append('camera_id', camera_id);
  if (plate_number) params.append('plate_number', plate_number);
  
  const res = await fetch(`${API_BASE}/detections?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch detections');
  return res.json();
};

export const fetchUniquePlates = async () => {
  const res = await fetch(`${API_BASE}/detections/plates`);
  if (!res.ok) throw new Error('Failed to fetch unique plates');
  return res.json();
};

export const fetchTrajectory = async (plateNumber) => {
  const res = await fetch(`${API_BASE}/trajectories/${encodeURIComponent(plateNumber)}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error('Failed to fetch vehicle trajectory');
  }
  return res.json();
};

export const fetchAnalyticsSummary = async () => {
  const res = await fetch(`${API_BASE}/analytics/summary`);
  if (!res.ok) throw new Error('Failed to fetch traffic analytics summary');
  return res.json();
};

export const fetchAlerts = async () => {
  const res = await fetch(`${API_BASE}/alerts`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
};

export const reviewAlert = async (alertId, status, reviewedBy, notes) => {
  const res = await fetch(`${API_BASE}/alerts/${alertId}/review`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, reviewed_by: reviewedBy, notes })
  });
  if (!res.ok) throw new Error('Failed to update alert');
  return res.json();
};

// ─── Phase 3: Multi-Camera Vehicle Association ─────────────────────────────

export const fetchVehicleTracks = async (multiCameraOnly = false) => {
  const params = new URLSearchParams();
  if (multiCameraOnly) params.append('multi_camera_only', 'true');
  const res = await fetch(`${API_BASE}/associations/tracks?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch vehicle tracks');
  return res.json();
};

export const fetchVehicleTrack = async (plateNumber) => {
  const res = await fetch(`${API_BASE}/associations/tracks/${encodeURIComponent(plateNumber)}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error('Failed to fetch vehicle track');
  }
  return res.json();
};

export const searchVehicleTracks = async (query) => {
  const res = await fetch(`${API_BASE}/associations/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) {
    if (res.status === 404) return [];
    throw new Error('Failed to search vehicle tracks');
  }
  return res.json();
};

export const fetchAssociationStats = async () => {
  const res = await fetch(`${API_BASE}/associations/stats`);
  if (!res.ok) throw new Error('Failed to fetch association stats');
  return res.json();
};

export const fetchCameraVehicles = async (cameraId, limit = 100) => {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  const res = await fetch(`${API_BASE}/cameras/${encodeURIComponent(cameraId)}/vehicles?${params.toString()}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`Failed to fetch vehicles for camera ${cameraId}`);
  }
  return res.json();
};

