import React, { useState, useEffect, useMemo } from 'react';
import { BarChart3, TrendingUp, Camera, PieChart as PieIcon, Activity, Flame, Clock } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import DemoDataBadge from '../components/DemoDataBadge';
import MetricCard from '../components/MetricCard';
import { fetchAnalyticsSummary } from '../services/api';
import { VEHICLE_TYPE_MAP, CATEGORY_COLORS, mapVehicleType } from '../utils/vehicleType';

const COLORS = ['#0284c7', '#38bdf8', '#0ea5e9', '#f59e0b', '#10b981', '#a855f7', '#ec4899', '#64748b'];

export default function AnalyticsView() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await fetchAnalyticsSummary();
        setAnalytics(data);
      } catch (err) {
        console.error('Error fetching analytics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const modalShareData = useMemo(() => {
    const raw = analytics?.vehicle_type_distribution || [];
    if (!raw.length) return [];

    const grouped = {};
    let total = 0;
    for (const item of raw) {
      const category = mapVehicleType(item.vehicle_type);
      const count = Number(item.count) || 0;
      grouped[category] = (grouped[category] || 0) + count;
      total += count;
    }

    if (total === 0) return [];

    // Filter to categories with observations and sort descending by count
    const list = Object.entries(grouped)
      .filter(([_, count]) => count > 0)
      .map(([category, count]) => ({
        vehicle_type: category,
        count,
        percentage: Number(((count / total) * 100).toFixed(1)),
      }))
      .sort((a, b) => b.count - a.count);

    // Guarantee that percentages sum to exactly 100%
    if (list.length > 0) {
      const sumPct = list.reduce((acc, curr) => acc + curr.percentage, 0);
      const diff = Number((100 - sumPct).toFixed(1));
      if (diff !== 0) {
        list[0].percentage = Number((list[0].percentage + diff).toFixed(1));
      }
    }

    return list;
  }, [analytics?.vehicle_type_distribution]);

  if (loading || !analytics) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-slate-900/60 rounded-2xl border border-slate-800"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-900/60 rounded-xl border border-slate-800"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-slate-900/60 rounded-xl border border-slate-800"></div>
          <div className="h-80 bg-slate-900/60 rounded-xl border border-slate-800"></div>
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
            <h2 className="text-xl font-bold text-slate-100">Macro Traffic Flow & Movement Analytics</h2>
            <DemoDataBadge />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Aggregate vehicle volume, temporal corridor flow rates, camera density distribution, and modal share.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Processed Detections"
          value={analytics.total_detections}
          subtitle="Aggregated observations"
          icon={Activity}
          color="emerald"
        />
        <MetricCard
          title="Busiest Camera Node"
          value={analytics.busiest_camera?.camera_id || 'CAM-01'}
          subtitle={`${analytics.busiest_camera?.count || 0} vehicles recorded`}
          icon={Camera}
          color="sky"
        />
        <MetricCard
          title="Peak Flow Interval"
          value={analytics.peak_time_interval?.interval || '09:10 - 09:20'}
          subtitle={`${analytics.peak_time_interval?.count || 0} vehicles / 10m (${analytics.peak_time_interval?.hourly_rate || 0}/hr rate)`}
          icon={Flame}
          color="amber"
        />
        <MetricCard
          title="Unique Vehicle Count"
          value={analytics.unique_vehicles}
          subtitle="Distinct license plates"
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Vehicle Volume by 10-Minute Time Interval */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Temporal Traffic Flow (10-Min Intervals)
              </h3>
              <p className="text-xs text-slate-400">Total volume observed per 10-minute time slice</p>
            </div>
            <Clock className="w-4 h-4 text-sky-400" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.volume_by_interval} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="start_time" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '12px' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Area
                  type="monotone"
                  dataKey="vehicle_count"
                  name="Vehicles Observed"
                  stroke="#0284c7"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorVolume)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Volume Distribution by Camera Node */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Volume Distribution by Camera Node
              </h3>
              <p className="text-xs text-slate-400">Total vehicle counts recorded per camera location</p>
            </div>
            <BarChart3 className="w-4 h-4 text-amber-400" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.volume_by_camera} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="camera_id" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '12px' }}
                  formatter={(value) => [`${value} Vehicles`, 'Volume']}
                  labelFormatter={(label) => `Camera Node: ${label}`}
                />
                <Bar dataKey="vehicle_count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Breakdown Table and Vehicle Type Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Table: Interval Flow Rate Summary (8 cols) */}
        <div className="lg:col-span-8 bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Traffic Interval Breakdown Table
            </h3>
            <span className="text-xs text-slate-400">UrbanSight Flow Specification</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Time Interval</th>
                  <th className="py-2.5 px-3">Vehicles Observed</th>
                  <th className="py-2.5 px-3">Hourly Flow Rate Estimate</th>
                  <th className="py-2.5 px-3">Load Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {analytics.volume_by_interval.map((row) => {
                  const isPeak = row.time_interval === analytics.peak_time_interval.interval;
                  return (
                    <tr key={row.time_interval} className={`hover:bg-slate-800/40 transition-colors duration-200 ${isPeak ? 'bg-amber-500/5' : ''}`}>
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-200 tabular-nums">
                        {row.time_interval}
                      </td>
                      <td className="py-2.5 px-3 font-mono font-bold text-sky-400 tabular-nums">
                        {row.vehicle_count} vehicles
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-300 tabular-nums">
                        ~{row.hourly_rate_estimate} veh/hr
                      </td>
                      <td className="py-2.5 px-3">
                        {isPeak ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 tracking-tight">
                            PEAK INTERVAL 🔥
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400 tracking-tight">
                            NORMAL
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal Share Distribution (4 cols) */}
        <div className="lg:col-span-4 bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                Vehicle Type Modal Share
              </h3>
              <p className="text-[11px] text-slate-400">Grouped into high-level vehicle categories</p>
            </div>
            <PieIcon className="w-4 h-4 text-purple-400" />
          </div>

          {modalShareData.length > 0 ? (
            <>
              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={modalShareData}
                      dataKey="count"
                      nameKey="vehicle_type"
                      cx="50%"
                      cy="50%"
                      innerRadius={38}
                      outerRadius={65}
                      paddingAngle={3}
                    >
                      {modalShareData.map((entry, index) => (
                        <Cell
                          key={`cell-${entry.vehicle_type}`}
                          fill={CATEGORY_COLORS[entry.vehicle_type] || COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '12px' }}
                      formatter={(value, name, props) => [`${value} (${props?.payload?.percentage ?? 0}%)`, props?.payload?.vehicle_type || name]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
                {modalShareData.map((item, idx) => (
                  <div key={item.vehicle_type} className="flex items-center justify-between text-slate-300">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: CATEGORY_COLORS[item.vehicle_type] || COLORS[idx % COLORS.length] }}
                      ></span>
                      <span>{item.vehicle_type}</span>
                    </div>
                    <span className="font-mono text-slate-400">{item.count} ({item.percentage}%)</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-44 text-slate-500 text-xs space-y-2">
              <PieIcon className="w-8 h-8 opacity-30" />
              <span>No vehicle type data available</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
