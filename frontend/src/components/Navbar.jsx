import React from 'react';
import { ShieldCheck, Activity, Cpu } from 'lucide-react';
import DemoDataBadge from './DemoDataBadge';

export default function Navbar() {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-sky-500/10 border border-sky-500/30 rounded-lg text-sky-400">
          <Cpu className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-slate-100 text-base tracking-tight">SIH26127</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800 font-mono">MVP Prototype</span>
          </div>
          <p className="text-xs text-slate-400">Multi-Camera ANPR Trajectory Tracking & Traffic Analytics</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <DemoDataBadge />
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Engine Live
        </div>
      </div>
    </header>
  );
}
