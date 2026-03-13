import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getAnalyticsOverview, getAnalyticsGraph, getAnalyticsLive } from '../../api/client';
import { Users, MessageSquare, Clock, Zap, RefreshCw, Activity, Database, Server } from 'lucide-react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

export default function AnalyticsView() {
  const { botId } = useParams();
  const [overview, setOverview] = useState(null);
  const [graphData, setGraphData] = useState([]);
  const [liveStats, setLiveStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [includePreview, setIncludePreview] = useState(false);

  const fetchOverview = useCallback(async () => {
    const res = await getAnalyticsOverview(botId, includePreview);
    setOverview(res.data);
  }, [botId, includePreview]);

  const fetchGraph = useCallback(async () => {
    const res = await getAnalyticsGraph(botId, includePreview);
    setGraphData(res.data);
  }, [botId, includePreview]);

  const fetchLiveData = useCallback(async () => {
    try {
      const res = await getAnalyticsLive(botId, includePreview);
      setLiveStats(res.data);
    } catch (error) {
      console.error("Failed to fetch live stats", error);
    }
  }, [botId, includePreview]);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchOverview(),
        fetchGraph(),
        fetchLiveData()
      ]);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchOverview, fetchGraph, fetchLiveData]);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchLiveData, 30000);
    return () => clearInterval(interval);
  }, [fetchAllData, fetchLiveData]);

  const StatCard = ({ title, value, icon, color, subtext }) => (
    <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white/60 text-sm font-medium">{title}</h3>
        <div className={`p-2 rounded-lg ${color}`}>
          {React.createElement(icon, { size: 20 })}
        </div>
      </div>
      <div className="text-3xl font-semibold text-white">{value}</div>
      {subtext && <div className="text-xs text-white/40 mt-1">{subtext}</div>}
    </div>
  );

  const ChartCard = ({ title, children }) => (
    <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 flex flex-col h-[400px]">
      <h3 className="text-lg font-semibold text-white/90 mb-6">{title}</h3>
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );

  if (loading && !overview) return <div className="p-8 text-center text-white/40">Loading analytics...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-semibold text-white tracking-tight">Analytics <span className="text-white/60 font-normal">Dashboard</span></h2>
          <p className="text-white/40 mt-1">Real-time performance and historical trends.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label htmlFor="include-preview" className="text-sm text-white/60">Include Preview Data</label>
            <button 
              role="switch"
              aria-checked={includePreview}
              onClick={() => setIncludePreview(!includePreview)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-[#0a0a0a] ${
                includePreview ? 'bg-emerald-500' : 'bg-white/10'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out ${
                  includePreview ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          <button 
            onClick={fetchAllData}
            className="p-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-white/70 hover:bg-white/[0.06] hover:text-white transition-all duration-200 group"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Live Stats */}
      {liveStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-emerald-400/80 to-teal-500/80 backdrop-blur-lg rounded-2xl p-6 text-white shadow-lg shadow-emerald-500/10 relative overflow-hidden">
             <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2 text-white/80">
                   <Activity size={18} />
                   <span className="font-medium text-sm">Active Users (5m)</span>
                </div>
                <div className="text-4xl font-bold">{liveStats.active_sessions_5m}</div>
             </div>
             <div className="absolute right-0 bottom-0 opacity-20 transform translate-x-4 translate-y-4">
                <Users size={100} />
             </div>
          </div>
          <div className="bg-gradient-to-br from-blue-400/80 to-indigo-500/80 backdrop-blur-lg rounded-2xl p-6 text-white shadow-lg shadow-blue-500/10 relative overflow-hidden">
             <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2 text-white/80">
                   <MessageSquare size={18} />
                   <span className="font-medium text-sm">Messages (1h)</span>
                </div>
                <div className="text-4xl font-bold">{liveStats.messages_1h}</div>
             </div>
             <div className="absolute right-0 bottom-0 opacity-20 transform translate-x-4 translate-y-4">
                <MessageSquare size={100} />
             </div>
          </div>
          <div className="bg-gradient-to-br from-amber-400/80 to-orange-500/80 backdrop-blur-lg rounded-2xl p-6 text-white shadow-lg shadow-amber-500/10 relative overflow-hidden">
             <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2 text-white/80">
                   <Clock size={18} />
                   <span className="font-medium text-sm">Avg Latency (1h)</span>
                </div>
                <div className="text-4xl font-bold">{liveStats.avg_latency_1h}ms</div>
             </div>
             <div className="absolute right-0 bottom-0 opacity-20 transform translate-x-4 translate-y-4">
                <Zap size={100} />
             </div>
          </div>
        </div>
      )}

      {/* 30-Day Overview */}
      <div>
        <h3 className="text-xl font-semibold text-white/80 mb-4">Last 30 Days Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            title="Total Messages" 
            value={overview?.total_messages || 0} 
            icon={MessageSquare} 
            color="bg-blue-500/20 text-blue-300"
          />
          <StatCard 
            title="Total Sessions" 
            value={overview?.active_sessions || 0} 
            icon={Users} 
            color="bg-emerald-500/20 text-emerald-300"
          />
          <StatCard 
            title="Avg. Latency" 
            value={`${overview?.avg_latency || 0}ms`} 
            icon={Clock} 
            color="bg-purple-500/20 text-purple-300"
          />
          <StatCard 
            title="Knowledge Hit Rate" 
            value={`${overview?.knowledge_hit_rate || 0}%`} 
            icon={Database} 
            color="bg-teal-500/20 text-teal-300"
          />
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Messages per Day */}
        <ChartCard title="Messages per Day">
          <AreaChart data={graphData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="date" tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} minTickGap={30} />
            <YAxis tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} />
            <Tooltip 
               contentStyle={{borderRadius: '12px', border: 'none', background: '#1c1c1c', color: '#fff'}}
               labelStyle={{color: '#a1a1aa'}}
            />
            <Area type="monotone" dataKey="messages" stroke="#34d399" fill="rgba(52, 211, 153, 0.1)" strokeWidth={2} />
          </AreaChart>
        </ChartCard>

        {/* Active Users/Sessions */}
        <ChartCard title="Active Sessions per Day">
          <LineChart data={graphData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="date" tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} minTickGap={30} />
            <YAxis tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} />
            <Tooltip 
               contentStyle={{borderRadius: '12px', border: 'none', background: '#1c1c1c', color: '#fff'}}
               labelStyle={{color: '#a1a1aa'}}
            />
            <Line type="monotone" dataKey="sessions" stroke="#60a5fa" strokeWidth={2} dot={{r: 4, fill: '#60a5fa'}} activeDot={{r: 6, strokeWidth: 2, stroke: '#fff'}} />
          </LineChart>
        </ChartCard>

        {/* Response Time */}
        <ChartCard title="Avg Response Time (ms)">
          <LineChart data={graphData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="date" tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} minTickGap={30} />
            <YAxis tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} />
            <Tooltip 
               contentStyle={{borderRadius: '12px', border: 'none', background: '#1c1c1c', color: '#fff'}}
               labelStyle={{color: '#a1a1aa'}}
            />
            <Line type="monotone" dataKey="latency" stroke="#facc15" strokeWidth={2} dot={false} />
          </LineChart>
        </ChartCard>

        {/* Knowledge vs API Hits */}
        <ChartCard title="Knowledge Base vs API Hits">
          <BarChart data={graphData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="date" tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} minTickGap={30} />
            <YAxis tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} />
            <Tooltip 
               cursor={{fill: 'rgba(255, 255, 255, 0.05)'}}
               contentStyle={{borderRadius: '12px', border: 'none', background: '#1c1c1c', color: '#fff'}}
               labelStyle={{color: '#a1a1aa'}}
            />
            <Legend iconType="circle" wrapperStyle={{color: '#a1a1aa'}} />
            <Bar dataKey="knowledge_hits" name="Knowledge Hits" stackId="a" fill="#2dd4bf" radius={[0, 0, 4, 4]} />
            <Bar dataKey="api_hits" name="API Hits" stackId="a" fill="#818cf8" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ChartCard>

        {/* Token Usage */}
        <div className="lg:col-span-2">
           <ChartCard title="Token Usage">
             <BarChart data={graphData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
               <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255, 255, 255, 0.1)" />
               <XAxis dataKey="date" tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} minTickGap={30} />
               <YAxis tick={{fontSize: 12, fill: '#a1a1aa'}} tickLine={false} axisLine={false} />
               <Tooltip 
                  cursor={{fill: 'rgba(255, 255, 255, 0.05)'}}
                  contentStyle={{borderRadius: '12px', border: 'none', background: '#1c1c1c', color: '#fff'}}
                  labelStyle={{color: '#a1a1aa'}}
               />
               <Bar dataKey="tokens" fill="#a78bfa" radius={[4, 4, 0, 0]} barSize={40} />
             </BarChart>
           </ChartCard>
        </div>
      </div>
    </div>
  );
}
