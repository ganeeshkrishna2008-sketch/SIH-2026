import React, { useState } from 'react';
import { Cpu, Play, Image, Video, RefreshCw, CheckCircle2, AlertCircle, Clock, Zap, ChevronDown, ChevronUp, Upload, X } from 'lucide-react';
import DemoDataBadge from '../components/DemoDataBadge';
import { fetchVehicleDetails } from '../services/api';

const API_BASE = '/api';

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}


async function apiPostFormData(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.statusText}`);
  return res.json();
}

function StatusBadge({ value, good = true }) {
  return (
    <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
      good ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
           : 'bg-red-500/20 text-red-400 border border-red-500/30'
    }`}>
      {value}
    </span>
  );
}

function DetectionRow({ det, idx }) {
  const [expanded, setExpanded] = useState(false);
  const [vehicleDetails, setVehicleDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const conf = det.confidence ?? 0;
  const confColor = conf >= 0.85 ? 'text-emerald-400' : conf >= 0.60 ? 'text-amber-400' : 'text-red-400';

  const toggleExpand = async () => {
    const nextState = !expanded;
    setExpanded(nextState);
    if (nextState && !vehicleDetails) {
      try {
        setLoadingDetails(true);
        const details = await fetchVehicleDetails(det.plate_number);
        setVehicleDetails(details);
      } catch (e) {
        console.error("Failed to fetch vehicle details", e);
      } finally {
        setLoadingDetails(false);
      }
    }
  };

  return (
    <div className="border border-slate-800 rounded-lg bg-slate-950 overflow-hidden">
      <div
        className="flex items-center justify-between px-4 py-2.5 cursor-pointer hover:bg-slate-900 transition"
        onClick={toggleExpand}
      >
        <div className="flex items-center gap-3">
          <span className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center text-[11px] font-mono font-bold">
            {idx + 1}
          </span>
          <span className="font-mono font-bold text-sky-300 tracking-wide">{det.plate_number}</span>
          <span className={`font-mono font-semibold text-sm ${confColor}`}>
            {(conf * 100).toFixed(1)}%
          </span>
          <span className="text-xs text-slate-400">{det.camera_id}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="font-mono">{new Date(det.timestamp).toLocaleTimeString()}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </div>
      {expanded && (
        <div className="px-4 py-3 border-t border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-400 bg-slate-900/40">
          <div className="space-y-1.5">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Detection Context</h4>
            <div>Location: <span className="text-slate-200">{det.location_name}</span></div>
            <div>Direction: <span className="text-slate-200">{det.direction}</span></div>
            <div>Coordinates: <span className="font-mono text-slate-200">{det.latitude?.toFixed(4)}, {det.longitude?.toFixed(4)}</span></div>
            <div>Source: <span className="text-sky-400">{det.source ?? 'anpr'}</span></div>
          </div>
          
          <div className="space-y-1.5 border-l border-slate-800 pl-4">
            <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">RTO / Vahan Details</h4>
            {loadingDetails ? (
              <div className="text-slate-500 italic animate-pulse">Fetching registration records...</div>
            ) : vehicleDetails ? (
              <>
                <div>Type & Color: <span className="text-slate-200">{vehicleDetails.vehicle_type} • {vehicleDetails.color}</span></div>
                <div>Owner Name: <span className="text-slate-200">{vehicleDetails.owner_name}</span></div>
                <div>Reg Date: <span className="text-slate-200">{vehicleDetails.registration_date}</span></div>
                <div>Chassis No: <span className="font-mono text-slate-200">{vehicleDetails.chassis_number}</span></div>
                <div>Engine No: <span className="font-mono text-slate-200">{vehicleDetails.engine_number}</span></div>
                {vehicleDetails.is_watchlist && (
                  <div className="mt-1 text-red-400 font-bold bg-red-500/10 inline-block px-2 py-0.5 rounded">
                    ⚠️ WATCHLIST FLAG
                  </div>
                )}
              </>
            ) : (
              <div className="text-slate-500 italic">No registration details available.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ANPRView() {
  const [engineStatus, setEngineStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  const [generating, setGenerating] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  const [noiseLevel, setNoiseLevel] = useState('low');
  const [inputSource, setInputSource] = useState('demo-video');
  const [selectedFile, setSelectedFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  const [cameraId, setCameraId] = useState('CAM-01');
  const [minConf, setMinConf] = useState(0.50);

  const checkStatus = async () => {
    try {
      setLoadingStatus(true);
      const status = await apiGet('/anpr/status');
      setEngineStatus(status);
    } catch (err) {
      setTestError(`Status check failed: ${err.message}`);
    } finally {
      setLoadingStatus(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setVideoUrl(URL.createObjectURL(file));
  };

  const runTest = async () => {
    try {
      setGenerating(true);
      setTestResult(null);
      setTestError(null);
      setShowDiagnostics(false);
      
      let result;
      if (inputSource === 'upload-video') {
        if (!selectedFile) throw new Error("Please select a video file first.");
        const formData = new FormData();
        formData.append('video', selectedFile);
        formData.append('camera_id', cameraId);
        formData.append('min_confidence', minConf);
        formData.append('frame_sample_interval', 30);
        result = await apiPostFormData('/anpr/upload-video', formData);
      } else {
        result = await apiPost('/anpr/generate-test', {
          generate_video: inputSource === 'demo-video',
          run_anpr: true,
          camera_id: cameraId,
          noise_level: noiseLevel,
          plates: ['TS09AB1234', 'DL01CZ4567', 'KA05MH8899', 'MH12TR3321'],
        });
      }
      setTestResult(result);
    } catch (err) {
      setTestError(`ANPR pipeline error: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100">ANPR / OCR Processing Engine</h2>
              <span className="px-2 py-0.5 text-xs font-bold rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 font-mono">Phase 2</span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Plate detection via contour analysis · OCR via EasyOCR · Conservative confidence thresholding · Detections stored to existing pipeline
            </p>
          </div>
          <button
            onClick={checkStatus}
            disabled={loadingStatus}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-slate-800 text-slate-200 border border-slate-700 hover:border-sky-500 hover:text-sky-400 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loadingStatus ? 'animate-spin' : ''}`} />
            Check Engine Status
          </button>
        </div>

        {/* Engine Status Panel */}
        {engineStatus && (
          <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-1">OpenCV</span>
              <StatusBadge value={engineStatus.libraries?.opencv ?? 'N/A'} good={engineStatus.opencv_available} />
            </div>
            <div>
              <span className="text-slate-400 block mb-1">EasyOCR</span>
              <StatusBadge value={engineStatus.libraries?.easyocr ?? 'N/A'} good={engineStatus.easyocr_available} />
            </div>
            <div>
              <span className="text-slate-400 block mb-1">PyTorch</span>
              <StatusBadge value={engineStatus.libraries?.torch ?? 'N/A'} good={engineStatus.libraries?.torch !== 'Not installed'} />
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Engine</span>
              <StatusBadge value={engineStatus.anpr_engine} good={true} />
            </div>
          </div>
        )}
      </div>

      {/* Phase 2 Pipeline Flow Diagram */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl space-y-3">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Phase 2 ANPR Pipeline</h3>
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          {[
            'Synthetic Frame/Video',
            'Frame Extraction',
            'Contour Plate Detector',
            'OCR Preprocessing',
            'EasyOCR Engine',
            'Confidence Filter (≥50%)',
            'Normalize Plate Text',
            'Store → Detection DB',
          ].map((step, i, arr) => (
            <React.Fragment key={step}>
              <span className={`px-2.5 py-1 rounded-lg border ${
                i === 0 ? 'bg-sky-500/10 border-sky-500/30 text-sky-300'
                : i === arr.length - 1 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-900 border-slate-700 text-slate-300'
              }`}>{step}</span>
              {i < arr.length - 1 && <span className="text-slate-600 font-bold">→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Test Controls */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl space-y-5">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Run ANPR Test (Synthetic Authorized Footage)</h3>
          <DemoDataBadge />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Camera Node</label>
            <select
              value={cameraId}
              onChange={e => setCameraId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500"
            >
              {['CAM-01', 'CAM-04', 'CAM-07', 'CAM-09'].map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="col-span-1 sm:col-span-2 lg:col-span-2">
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Input Source</label>
            <div className="flex gap-2">
              <button
                onClick={() => setInputSource('demo-video')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  inputSource === 'demo-video' ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Video className="w-3.5 h-3.5" /> Demo Video
              </button>
              <button
                onClick={() => setInputSource('demo-images')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  inputSource === 'demo-images' ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Image className="w-3.5 h-3.5" /> Demo Images
              </button>
              <button
                onClick={() => setInputSource('upload-video')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  inputSource === 'upload-video' ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Upload className="w-3.5 h-3.5" /> Upload Video
              </button>
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Image Noise (Demo Only)</label>
            <select
              disabled={inputSource === 'upload-video'}
              value={noiseLevel}
              onChange={e => setNoiseLevel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500 disabled:opacity-50"
            >
              <option value="low">Low (Clear)</option>
              <option value="medium">Medium (Blurred)</option>
              <option value="high">High (Compressed)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Min OCR Confidence</label>
            <div className="flex items-center gap-2">
              <input
                type="range" min="0.3" max="0.95" step="0.05"
                value={minConf}
                onChange={e => setMinConf(parseFloat(e.target.value))}
                className="flex-1 accent-sky-500"
              />
              <span className="text-xs font-mono text-sky-400 w-10 text-right">{(minConf * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        
        {inputSource === 'upload-video' && (
          <div className="pt-4 border-t border-slate-800">
            <label className="block text-xs text-slate-400 mb-2 font-medium">Select Local Video File (.mp4, .avi, .mov, .mkv)</label>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".mp4,.avi,.mov,.mkv"
                onChange={handleFileSelect}
                className="hidden"
                id="video-upload"
              />
              <label
                htmlFor="video-upload"
                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-slate-800 text-slate-200 border border-slate-700 hover:border-sky-500 hover:text-sky-400 transition"
              >
                <Upload className="w-4 h-4" />
                Choose File
              </label>
              {selectedFile && (
                <div className="flex items-center gap-3 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  <span className="text-sm text-sky-300 font-mono">{selectedFile.name}</span>
                  <span className="text-xs text-slate-500">{(selectedFile.size / (1024 * 1024)).toFixed(1)} MB</span>
                  <button onClick={() => { setSelectedFile(null); setVideoUrl(null); }} className="text-slate-500 hover:text-red-400">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-4">
          <p className="text-xs text-slate-400">
            Generates synthetic license plate images/video → runs full plate detection and OCR → stores real detections (marked <span className="text-sky-400 font-mono">is_demo=0</span>) into the existing observation database.
          </p>
          <button
            onClick={runTest}
            disabled={generating}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-600 text-white font-bold text-sm transition shadow-lg shadow-sky-500/20 disabled:opacity-60 shrink-0"
          >
            {generating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run ANPR Pipeline
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {testError && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <strong className="text-red-300">Pipeline Error:</strong> {testError}
          </div>
        </div>
      )}

      {/* Results Panel */}
      {testResult && (
        <div className="space-y-4">
          {/* Summary Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: 'Frames Processed', value: testResult.total_frames_sampled, color: 'sky' },
              { label: 'Plates Detected', value: testResult.detections?.length ?? 0, color: 'emerald' },
              { label: 'Stored to DB', value: testResult.detections_stored, color: 'purple' },
              { label: 'Rejected (Format)', value: testResult.rejected_invalid_format || 0, color: 'red' },
              { label: 'Rejected (Low Conf)', value: testResult.rejected_low_confidence || 0, color: 'amber' },
            ].map(m => (
              <div key={m.label} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">{m.label}</div>
                <div className={`text-3xl font-bold font-mono tracking-tight ${
                  m.color === 'sky' ? 'text-sky-400' :
                  m.color === 'emerald' ? 'text-emerald-400' :
                  m.color === 'purple' ? 'text-purple-400' :
                  m.color === 'red' ? 'text-red-400' : 'text-amber-400'
                }`}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Pipeline Compliance Note */}
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-sm text-slate-300 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-sky-400 shrink-0" />
              <span>
                <strong>Balanced Validation Active:</strong> Strict Indian plate format verification prevents non-plate text (e.g. CAMERA, SAFEPRO) from entering the database, while genuine vehicle plates are accepted.
              </span>
            </div>
            <button
              onClick={() => setShowDiagnostics(!showDiagnostics)}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors duration-200 shrink-0 border border-slate-700 whitespace-nowrap active:scale-95"
            >
              {showDiagnostics ? 'Hide Diagnostic Log' : 'Show Diagnostic Log'}
            </button>
          </div>

          {/* Diagnostic Logs Drawer */}
          {showDiagnostics && (
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl overflow-hidden mt-6">
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-900/50">
                <h4 className="text-slate-300 uppercase tracking-wider font-semibold font-sans text-xs">
                  Candidate Region Analysis ({testResult.debug_candidates?.length || 0} Candidates)
                </h4>
                <span className="text-slate-500 text-[10px] uppercase">Real-time candidate classifier log</span>
              </div>
              <div className="max-h-96 overflow-y-auto overflow-x-hidden divide-y divide-slate-800/40">
                {testResult.debug_candidates?.length > 0 ? (
                  testResult.debug_candidates.map((cand, i) => {
                    const decision = cand.decision ?? 'REJECTED';
                    const reason = cand.reason ?? '';
                    const isAccepted = decision === 'ACCEPTED';
                    const displayText = cand.raw_text || cand.plate_number;
                    const statusLabel = `${decision}: ${reason.toUpperCase()}`;
                    return (
                      <div key={i} className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800/60 last:border-0 font-mono text-xs gap-4 hover:bg-slate-900/60 transition-colors duration-150">
                        <div className="flex items-center gap-6 min-w-0">
                          <span className="text-slate-500 shrink-0 tabular-nums">Frame {cand.frame_index ?? (i + 1)}</span>
                          <span className={`font-bold truncate ${displayText ? 'text-slate-200' : 'text-slate-500 italic'}`}>
                            {displayText ? `"${displayText}"` : '[No OCR Text]'}
                          </span>
                        </div>
                        <div className="flex items-center gap-6 shrink-0">
                          <span className="text-slate-400 tabular-nums">Conf: {((cand.confidence ?? 0) * 100).toFixed(1)}%</span>
                          <span className={`px-2.5 py-1 rounded text-[10px] font-bold tracking-wider uppercase whitespace-nowrap ${
                            isAccepted
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-red-500/10 text-red-500 border border-red-500/30'
                          }`}>
                            {statusLabel}
                          </span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-slate-500 text-xs text-center py-8 px-4">No candidates analyzed in this run.</div>
                )}
              </div>
            </div>
          )}

          {/* Detection List */}
          {testResult.detections?.length > 0 && (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                  Detections from ANPR Pipeline ({testResult.detections.length})
                </h3>
                <span className="text-xs px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
                  is_demo = 0 (Real ANPR)
                </span>
              </div>
              <div className="space-y-2">
                {testResult.detections.map((det, idx) => (
                  <DetectionRow key={`det-${idx}`} det={det} idx={idx} />
                ))}
              </div>
            </div>
          )}

          {testResult.detections?.length === 0 && (
            <div className="p-5 rounded-xl bg-amber-500/5 border border-amber-500/20 text-amber-300 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>
                No plates detected above the confidence threshold ({(minConf * 100).toFixed(0)}%). 
                Try lowering the confidence threshold, or check engine status to confirm OpenCV and EasyOCR are installed.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
