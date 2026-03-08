import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { TrendingUp, Trophy, ArrowUp, ArrowDown, RefreshCw } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-avaira-card border border-avaira-border p-2 font-mono text-xs">
        {payload.map((p, i) => <p key={i} style={{ color: p.fill || p.color }}>{p.name}: {p.value}</p>)}
      </div>
    );
  }
  return null;
};

const getRepColor = (score) => {
  if (score >= 100) return '#39FF14';
  if (score >= 80) return '#00F0FF';
  if (score >= 50) return '#FFD300';
  return '#FF003C';
};

export default function Reputation() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [history, setHistory] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      const [lbRes, histRes] = await Promise.all([
        axios.get(`${API}/reputation/leaderboard`),
        axios.get(`${API}/reputation/history`)
      ]);
      setLeaderboard(lbRes.data);
      setHistory(histRes.data);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const chartData = leaderboard.slice(0, 10).map(a => ({
    name: a.name.length > 10 ? a.name.slice(0, 10) + '...' : a.name,
    score: a.reputation,
    fill: getRepColor(a.reputation)
  }));

  return (
    <div data-testid="reputation-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">Reputation Engine</h1>
          <p className="font-mono text-xs text-avaira-muted mt-1">AGENT TRUST SCORES</p>
        </div>
        <button data-testid="refresh-reputation-btn" onClick={fetchData} className="p-2 border border-avaira-border text-avaira-muted hover:text-avaira-cyan hover:border-avaira-cyan transition-colors">
          <RefreshCw size={14} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Leaderboard */}
        <div className="lg:col-span-2 cyber-card p-4">
          <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3 flex items-center gap-2">
            <Trophy size={14} className="text-avaira-yellow" /> Leaderboard
          </h2>
          {leaderboard.length === 0 ? (
            <p className="font-mono text-xs text-avaira-dim text-center py-8">NO AGENTS</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Agent</th>
                    <th>Status</th>
                    <th className="text-right">Score</th>
                    <th className="text-right">Executions</th>
                    <th className="text-right">Success Rate</th>
                    <th className="text-right">Collateral</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((agent, i) => {
                    const rate = agent.total_executions > 0 ? ((agent.successful_executions / agent.total_executions) * 100).toFixed(0) : '-';
                    return (
                      <tr key={agent.id} data-testid={`lb-row-${i}`}>
                        <td className="text-avaira-dim">{i + 1}</td>
                        <td className="text-foreground font-semibold">{agent.name}</td>
                        <td>
                          <span className={`status-dot ${agent.status === 'active' ? 'active' : agent.status === 'frozen' ? 'frozen' : 'paused'}`} />
                        </td>
                        <td className="text-right">
                          <span className="font-bold" style={{ color: getRepColor(agent.reputation) }}>
                            {agent.reputation.toFixed(0)}
                          </span>
                        </td>
                        <td className="text-right text-foreground">{agent.total_executions}</td>
                        <td className="text-right" style={{ color: rate !== '-' && parseInt(rate) >= 80 ? '#39FF14' : rate !== '-' && parseInt(rate) >= 50 ? '#FFD300' : rate === '-' ? '#858585' : '#FF003C' }}>
                          {rate}{rate !== '-' ? '%' : ''}
                        </td>
                        <td className="text-right text-avaira-cyan">{agent.collateral_remaining.toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Score Chart + History */}
        <div className="space-y-4">
          {/* Bar Chart */}
          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">Score Distribution</h2>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" horizontal={false} />
                  <XAxis type="number" domain={[0, 200]} tick={{ fill: '#858585', fontSize: 9, fontFamily: 'JetBrains Mono' }} />
                  <YAxis dataKey="name" type="category" width={80} tick={{ fill: '#858585', fontSize: 9, fontFamily: 'JetBrains Mono' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="score" name="Reputation" radius={[0, 2, 2, 0]}>
                    {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-48 flex items-center justify-center">
                <p className="font-mono text-xs text-avaira-dim">NO DATA</p>
              </div>
            )}
          </div>

          {/* Recent Changes */}
          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">Recent Changes</h2>
            {history.length === 0 ? (
              <p className="font-mono text-xs text-avaira-dim text-center py-6">NO HISTORY</p>
            ) : (
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {history.slice(0, 15).map(h => (
                  <div key={h.id} className="p-2 hover:bg-white/[0.02] border-b border-white/[0.04] flex items-center gap-2" data-testid={`rep-history-${h.id}`}>
                    {h.delta > 0 ? <ArrowUp size={12} className="text-avaira-green" /> : <ArrowDown size={12} className="text-avaira-red" />}
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-xs text-foreground truncate">{h.agent_name}</p>
                      <p className="font-mono text-[10px] text-avaira-dim truncate">{h.reason}</p>
                    </div>
                    <span className="font-mono text-xs font-bold" style={{ color: h.delta > 0 ? '#39FF14' : '#FF003C' }}>
                      {h.delta > 0 ? '+' : ''}{h.delta}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
