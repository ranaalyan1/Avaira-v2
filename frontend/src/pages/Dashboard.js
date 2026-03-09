import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Activity, Users, Zap, ShieldOff, Wallet, TrendingUp, Play, AlertTriangle } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const StatCard = ({ icon: Icon, label, value, color, delay }) => (
  <div className={`cyber-card p-4 animate-slide-in stagger-${delay}`} data-testid={`stat-${label.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="flex items-center gap-3">
      <div className={`p-2 border`} style={{ borderColor: `${color}40`, background: `${color}10` }}>
        <Icon size={16} strokeWidth={1.5} style={{ color }} />
      </div>
      <div>
        <p className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest">{label}</p>
        <p className="font-heading font-bold text-xl text-foreground mt-0.5" style={{ color: value > 0 ? undefined : undefined }}>{value}</p>
      </div>
    </div>
  </div>
);

const COLORS = ['#00F0FF', '#39FF14', '#FFD300', '#FF003C', '#7000FF'];
const STATUS_COLORS = { completed: '#39FF14', rejected_deviation: '#FF003C', permit_invalid: '#FFD300', pending_validation: '#00F0FF', freeze: '#FF003C', slash: '#FFD300', execution: '#00F0FF' };

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-avaira-card border border-avaira-border p-2 font-mono text-xs">
        <p className="text-avaira-muted">{label}</p>
        {payload.map((p, i) => <p key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</p>)}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [simulating, setSimulating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, activityRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/dashboard/activity`)
      ]);
      setStats(statsRes.data);
      setActivity(activityRes.data);
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const runSimulation = async () => {
    setSimulating(true);
    try {
      const res = await axios.post(`${API}/simulate/lifecycle`);
      toast.success(`Simulation complete: ${res.data.steps.length} steps executed`);
      fetchData();
    } catch (e) {
      toast.error("Simulation failed");
    }
    setSimulating(false);
  };

  const pieData = stats ? [
    { name: 'Active', value: stats.active_agents || 0 },
    { name: 'Frozen', value: stats.frozen_agents || 0 },
    { name: 'Completed', value: stats.completed_executions || 0 },
    { name: 'Failed', value: stats.failed_executions || 0 },
  ].filter(d => d.value > 0) : [];

  const treasuryData = stats ? [
    { name: 'TrustPool', value: stats.trust_pool_balance || 0 },
    { name: 'Revenue', value: stats.protocol_revenue || 0 },
  ].filter(d => d.value > 0) : [];

  return (
    <div data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">
            Protocol Overview
          </h1>
          <p className="font-mono text-xs text-avaira-muted mt-1">REAL-TIME EXECUTION MONITORING</p>
        </div>
        <button
          data-testid="simulate-lifecycle-btn"
          onClick={runSimulation}
          disabled={simulating}
          className="cyber-btn bg-avaira-cyan text-white px-4 py-2 font-heading text-sm flex items-center gap-2 disabled:opacity-50"
        >
          <Play size={14} />
          {simulating ? "SIMULATING..." : "SIMULATE LIFECYCLE"}
        </button>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
          <StatCard icon={Users} label="Total Agents" value={stats.total_agents} color="#00F0FF" delay={1} />
          <StatCard icon={Activity} label="Active Agents" value={stats.active_agents} color="#39FF14" delay={2} />
          <StatCard icon={Zap} label="Executions" value={stats.total_executions} color="#7000FF" delay={3} />
          <StatCard icon={ShieldOff} label="Frozen" value={stats.frozen_agents} color="#FF003C" delay={4} />
          <StatCard icon={Wallet} label="Total Fees" value={stats.total_fees_collected.toFixed(4)} color="#FFD300" delay={5} />
          <StatCard icon={TrendingUp} label="Trust Pool" value={stats.trust_pool_balance.toFixed(4)} color="#00F0FF" delay={6} />
        </div>
      )}

      {/* Charts + Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Activity Feed */}
        <div className="lg:col-span-2 cyber-card p-4">
          <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-4 flex items-center gap-2">
            <Activity size={14} className="text-avaira-cyan" /> Recent Activity
          </h2>
          {activity.length === 0 ? (
            <div className="text-center py-8">
              <p className="font-mono text-xs text-avaira-dim">NO ACTIVITY YET</p>
              <p className="font-mono text-[10px] text-avaira-dim mt-1">Run a simulation to generate data</p>
            </div>
          ) : (
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {activity.map((item, i) => (
                <div key={item.id + i} className="flex items-center gap-3 p-2 hover:bg-white/[0.02] transition-colors" data-testid={`activity-item-${i}`}>
                  <div className={`status-dot ${item.status === 'completed' ? 'active' : item.status === 'freeze' || item.status === 'rejected_deviation' ? 'frozen' : 'paused'}`} />
                  <div className="flex-1 min-w-0">
                    <p className="font-mono text-xs text-foreground truncate">{item.description}</p>
                    <p className="font-mono text-[10px] text-avaira-dim">{new Date(item.timestamp).toLocaleString()}</p>
                  </div>
                  <span className="font-mono text-[10px] px-2 py-0.5 border" style={{ borderColor: (STATUS_COLORS[item.status] || '#333') + '50', color: STATUS_COLORS[item.status] || '#858585' }}>
                    {item.type.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Charts */}
        <div className="space-y-4">
          {/* Agent Distribution */}
          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3 flex items-center gap-2">
              <Users size={14} className="text-avaira-cyan" /> Distribution
            </h2>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} paddingAngle={2} dataKey="value" stroke="none">
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center">
                <p className="font-mono text-xs text-avaira-dim">NO DATA</p>
              </div>
            )}
            <div className="flex flex-wrap gap-3 mt-2">
              {pieData.map((d, i) => (
                <div key={d.name} className="flex items-center gap-1.5">
                  <div className="w-2 h-2" style={{ background: COLORS[i % COLORS.length] }} />
                  <span className="font-mono text-[10px] text-avaira-muted">{d.name}: {d.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Treasury Split */}
          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3 flex items-center gap-2">
              <Wallet size={14} className="text-avaira-cyan" /> Treasury Split
            </h2>
            {treasuryData.length > 0 ? (
              <div className="space-y-2">
                {treasuryData.map((d, i) => (
                  <div key={d.name}>
                    <div className="flex justify-between font-mono text-xs mb-1">
                      <span className="text-avaira-muted">{d.name}</span>
                      <span className="text-foreground">{d.value.toFixed(6)} AVAX</span>
                    </div>
                    <div className="h-1.5 bg-avaira-surface">
                      <div className="h-full transition-all duration-500" style={{
                        width: `${((d.value / (stats?.total_fees_collected || 1)) * 100)}%`,
                        background: i === 0 ? '#00F0FF' : '#7000FF'
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-20 flex items-center justify-center">
                <p className="font-mono text-xs text-avaira-dim">NO FEES COLLECTED</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
