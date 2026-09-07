import React from 'react';
import { LayoutDashboard, Search, Navigation, BarChart3, AlertTriangle, ScanLine } from 'lucide-react';

export default function Sidebar({ currentTab, setCurrentTab, alertCount = 0 }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard Overview', icon: LayoutDashboard },
    { id: 'anpr', label: 'ANPR / OCR Engine', icon: ScanLine, badge: 'Phase 2' },
    { id: 'search', label: 'Vehicle Search & History', icon: Search },
    { id: 'trajectory', label: 'Trajectory & Route Map', icon: Navigation },
    { id: 'analytics', label: 'Traffic Flow Analytics', icon: BarChart3 },
    { id: 'alerts', label: 'Authorized Alerts', icon: AlertTriangle, badge: alertCount },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 flex flex-col justify-between shrink-0">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          Core Capabilities
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                typeof item.badge === 'string' ? (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    isActive ? 'bg-white/20 text-white' : 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                  }`}>
                    {item.badge}
                  </span>
                ) : item.badge > 0 ? (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    isActive ? 'bg-white/20 text-white' : 'bg-red-500/20 text-red-400 border border-red-500/30'
                  }`}>
                    {item.badge}
                  </span>
                ) : null
              )}
            </button>
          );
        })}
      </div>

      <div className="p-4 border-t border-slate-900">
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-1.5">
          <div className="flex justify-between items-center text-slate-300 font-medium">
            <span>Prototype Phase</span>
            <span className="text-sky-400 font-mono">Phase 3</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Multi-Camera Vehicle Association + ANPR Trajectory
          </p>
        </div>
      </div>
    </aside>
  );
}
