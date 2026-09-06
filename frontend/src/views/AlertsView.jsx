import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldCheck, CheckCircle2, XCircle, Clock, UserCheck } from 'lucide-react';
import DemoDataBadge from '../components/DemoDataBadge';
import { fetchAlerts, reviewAlert } from '../services/api';

export default function AlertsView({ onSelectPlate }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const data = await fetchAlerts();
      setAlerts(data);
    } catch (err) {
      console.error('Error loading alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleReview = async (alertId, newStatus) => {
    try {
      setUpdatingId(alertId);
      const officer = "Duty Officer (Badge #8821)";
      const note = newStatus === 'REVIEWED' ? 'Confirmed by operator. Continuous trajectory tracking initiated.' : 'Dismissed by operator.';
      await reviewAlert(alertId, newStatus, officer, note);
      await loadAlerts();
    } catch (err) {
      alert(`Failed to update alert: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100">Authorized Watchlist Alerts</h2>
              <DemoDataBadge />
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Synthetic demonstration of authorized watchlist matches. Every alert requires human verification.
            </p>
          </div>
        </div>

        {/* SIH Compliance Note */}
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-300 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-red-200">Protocol Notice:</strong> All flagged plates are classified as <em>"Authorized Watchlist Match — Requires Human Review"</em>. No automated punitive action or individual identity profiling is performed.
          </div>
        </div>
      </div>

      {/* Alert List */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Active Watchlist Notifications ({alerts.length})
          </h3>
          <button
            onClick={loadAlerts}
            className="text-xs text-sky-400 hover:text-sky-300 transition"
          >
            Refresh Feed
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">No active alerts recorded.</div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alertItem) => {
              const isPending = alertItem.status === 'PENDING_REVIEW';
              return (
                <div
                  key={alertItem.id}
                  className={`p-4 rounded-xl border transition ${
                    isPending
                      ? 'bg-slate-950 border-red-500/40 shadow-lg shadow-red-500/5'
                      : 'bg-slate-950/60 border-slate-800'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-3">
                        <span className="text-base font-mono font-bold text-white tracking-wide">
                          {alertItem.plate_number}
                        </span>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          isPending
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {alertItem.status.replace('_', ' ')}
                        </span>
                        <span className="text-xs font-mono text-emerald-400">
                          {(alertItem.confidence * 100).toFixed(1)}% OCR Match
                        </span>
                      </div>
                      <div className="text-xs text-slate-300 font-medium">
                        {alertItem.alert_type}
                      </div>
                      <div className="text-xs text-slate-400 flex flex-wrap gap-3 pt-1">
                        <span>Observed at: <strong className="text-sky-400 font-mono">{alertItem.camera_id}</strong> ({alertItem.location_name})</span>
                        <span>Timestamp: <strong className="text-slate-200 font-mono">{new Date(alertItem.timestamp).toLocaleTimeString()}</strong></span>
                      </div>
                      {alertItem.notes && (
                        <p className="text-xs text-slate-400 italic pt-1 border-t border-slate-900">
                          Note: {alertItem.notes} {alertItem.reviewed_by ? `(Reviewed by: ${alertItem.reviewed_by})` : ''}
                        </p>
                      )}
                    </div>

                    <div className="flex sm:flex-col items-end gap-2 shrink-0">
                      <button
                        onClick={() => onSelectPlate(alertItem.plate_number)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30 hover:bg-sky-500 hover:text-white transition"
                      >
                        Inspect Route
                      </button>

                      {isPending && (
                        <div className="flex gap-2">
                          <button
                            disabled={updatingId === alertItem.id}
                            onClick={() => handleReview(alertItem.id, 'REVIEWED')}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-white transition disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Confirm
                          </button>
                          <button
                            disabled={updatingId === alertItem.id}
                            onClick={() => handleReview(alertItem.id, 'DISMISSED')}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition disabled:opacity-50"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            Dismiss
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
