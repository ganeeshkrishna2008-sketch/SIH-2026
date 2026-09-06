import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function DemoDataBadge({ className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide uppercase bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}>
      <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
      DEMO DATA
    </span>
  );
}
