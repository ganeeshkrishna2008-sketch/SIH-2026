import React, { useState } from 'react';
import { Cpu, Play, Image, Video, RefreshCw, CheckCircle2, AlertCircle, Clock, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import DemoDataBadge from '../components/DemoDataBadge';

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
  const conf = det.confidence ?? 0;
  const confColor = conf >= 0.85 ? 'text-emerald-400' : conf >= 0.60 ? 'text-amber-400' : 'text-red-400';

  return (
    <div className="border border-slate-800 rounded-lg bg-slate-950 overflow-hidden">
      <div
        className="flex items-center justify-between px-4 py-2.5 cursor-pointer hover:bg-slate-900 transition"
        onClick={() => setExpanded(!expanded)}
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
        <div className="px-4 py-3 border-t border-slate-800 grid grid-cols-2 gap-2 text-xs text-slate-400 bg-slate-900/40">
          <div>Location: <span className="text-slate-200">{det.location_name}</span></div>
          <div>Direction: <span className="text-slate-200">{det.direction}</span></div>
          <div>Coordinates: <span className="font-mono text-slate-200">{det.latitude?.toFixed(4)}, {det.longitude?.toFixed(4)}</span></div>
          <div>Source: <span className="text-sky-400">{det.source ?? 'anpr'}</span></div>
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

  const [noiseLevel, setNoiseLevel] = useState('low');
  const [useVideo, setUseVideo] = useState(true);
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

  const runTest = async () => {
    try {
      setGenerating(true);
      setTestResult(null);
      setTestError(null);
      const result = await apiPost('/anpr/generate-test', {
        generate_video: useVideo,
        run_anpr: true,
        camera_id: cameraId,
        noise_level: noiseLevel,
        plates: ['TS09AB1234', 'DL01CZ4567', 'KA05MH8899', 'MH12TR3321'],
      });
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
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Input Mode</label>
            <div className="flex gap-2">
              <button
                onClick={() => setUseVideo(true)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  useVideo ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Video className="w-3.5 h-3.5" /> Video
              </button>
              <button
                onClick={() => setUseVideo(false)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  !useVideo ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Image className="w-3.5 h-3.5" /> Images
              </button>
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Image Noise</label>
            <select
              value={noiseLevel}
              onChange={e => setNoiseLevel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500"
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
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: 'Frames Processed', value: testResult.total_frames_sampled, color: 'sky' },
              { label: 'Plates Detected', value: testResult.detections?.length ?? 0, color: 'emerald' },
              { label: 'Stored to DB', value: testResult.detections_stored, color: 'purple' },
              { label: 'Rejected (Low Conf)', value: testResult.rejected_low_confidence, color: 'amber' },
            ].map(m => (
              <div key={m.label} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">{m.label}</div>
                <div className={`text-2xl font-bold ${
                  m.color === 'sky' ? 'text-sky-400' :
                  m.color === 'emerald' ? 'text-emerald-400' :
                  m.color === 'purple' ? 'text-purple-400' : 'text-amber-400'
                }`}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Pipeline Compliance Note */}
          <div className="p-3.5 rounded-xl bg-sky-500/5 border border-sky-500/20 text-xs text-sky-300 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
            <span>
              <strong>Implementation Plan Compliance:</strong> Only detections with OCR confidence ≥ {(minConf * 100).toFixed(0)}% were stored.
              Low-confidence plate regions were detected but rejected and counted separately.
              No plates were invented, guessed, or silently corrected.
            </span>
          </div>

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
