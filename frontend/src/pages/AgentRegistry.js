import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { UserPlus, Shield, Zap, AlertTriangle, RefreshCw } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GRADE_COLORS = { AAA: '#39FF14', AA: '#00F0FF', A: '#00F0FF', BBB: '#FFD300', BB: '#FFD300', B: '#FF8C00', CCC: '#FF003C', D: '#FF003C' };

const StatusBadge = ({ status }) => {
  const styles = {
    active: "border-green-500/50 text-green-400 bg-green-500/10",
    frozen: "border-red-500/50 text-red-400 bg-red-500/10",
    paused: "border-yellow-500/50 text-yellow-400 bg-yellow-500/10",
  };
  return (
    <span className={`font-mono uppercase text-[10px] tracking-wider border px-2 py-0.5 ${styles[status] || styles.paused}`} data-testid={`status-badge-${status}`}>
      {status}
    </span>
  );
};

const AgentCard = ({ agent, onRefresh, scores }) => {
  const score = scores.find(s => s.agent_id === agent.id);
  const handleToggleStatus = async () => {
    const newStatus = agent.status === "active" ? "paused" : "active";
    if (agent.status === "frozen") return toast.error("Cannot change status of frozen agent");
    try {
      await axios.patch(`${API}/agents/${agent.id}/status?status=${newStatus}`);
      toast.success(`Agent ${newStatus}`);
      onRefresh();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to update");
    }
  };

  return (
    <div className="cyber-card corner-cut p-4" data-testid={`agent-card-${agent.id}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-heading font-bold text-base text-foreground uppercase tracking-tight">{agent.name}</h3>
        <div className="flex items-center gap-2">
          {score && (
            <span className="font-heading font-bold text-sm px-2 py-0.5 border" style={{ borderColor: (GRADE_COLORS[score.grade] || '#858585') + '50', color: GRADE_COLORS[score.grade] || '#858585' }} data-testid={`grade-${agent.id}`}>
              {score.grade}
            </span>
          )}
          <StatusBadge status={agent.status} />
        </div>
      </div>
      <div className="space-y-2 font-mono text-xs">
        <div className="flex justify-between">
          <span className="text-avaira-muted">WALLET</span>
          <span className="text-foreground truncate ml-2 max-w-[140px]">{agent.wallet_address}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-avaira-muted">COLLATERAL</span>
          <span className="text-avaira-cyan">{agent.collateral_remaining.toFixed(4)} / {agent.collateral_amount.toFixed(4)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-avaira-muted">REPUTATION</span>
          <span style={{ color: agent.reputation >= 80 ? '#39FF14' : agent.reputation >= 50 ? '#FFD300' : '#FF003C' }}>
            {agent.reputation.toFixed(0)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-avaira-muted">EXECUTIONS</span>
          <span className="text-foreground">{agent.successful_executions}/{agent.total_executions}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-avaira-muted">MISSION</span>
          <span className="text-foreground truncate ml-2 max-w-[180px]">{agent.mission_intent}</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-avaira-border flex items-center justify-between">
        <span className="font-mono text-[10px] text-avaira-dim">
          {new Date(agent.registered_at).toLocaleDateString()}
        </span>
        <button
          data-testid={`toggle-status-${agent.id}`}
          onClick={handleToggleStatus}
          disabled={agent.status === "frozen"}
          className="font-mono text-[10px] uppercase tracking-wider px-2 py-1 border border-avaira-border text-avaira-muted hover:text-avaira-cyan hover:border-avaira-cyan transition-colors disabled:opacity-30"
        >
          {agent.status === "active" ? "PAUSE" : agent.status === "frozen" ? "FROZEN" : "ACTIVATE"}
        </button>
      </div>
    </div>
  );
};

export default function AgentRegistry() {
  const [agents, setAgents] = useState([]);
  const [scores, setScores] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "", wallet_address: "", collateral_amount: "1.0", mission_intent: "",
    max_tx_value: "10.0", max_daily_txns: "50", allowed_actions: "transfer,swap,stake", max_slippage: "0.05"
  });

  const fetchAgents = useCallback(async () => {
    try {
      const [aRes, sRes] = await Promise.all([
        axios.get(`${API}/agents`),
        axios.get(`${API}/scores/all`)
      ]);
      setAgents(aRes.data);
      setScores(sRes.data);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/agents/register`, {
        name: form.name,
        wallet_address: form.wallet_address || "0x" + Array(40).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        collateral_amount: parseFloat(form.collateral_amount),
        mission_intent: form.mission_intent,
        risk_envelope: {
          max_tx_value: parseFloat(form.max_tx_value),
          max_daily_txns: parseInt(form.max_daily_txns),
          allowed_actions: form.allowed_actions.split(",").map(s => s.trim()),
          max_slippage: parseFloat(form.max_slippage)
        }
      });
      toast.success("Agent registered successfully");
      setOpen(false);
      setForm({ name: "", wallet_address: "", collateral_amount: "1.0", mission_intent: "", max_tx_value: "10.0", max_daily_txns: "50", allowed_actions: "transfer,swap,stake", max_slippage: "0.05" });
      fetchAgents();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Registration failed");
    }
  };

  const InputField = ({ label, name, type = "text", placeholder }) => (
    <div>
      <label className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest block mb-1">{label}</label>
      <input
        data-testid={`register-${name}`}
        type={type}
        value={form[name]}
        onChange={(e) => setForm(prev => ({ ...prev, [name]: e.target.value }))}
        placeholder={placeholder}
        className="w-full bg-black border border-white/20 focus:border-avaira-cyan text-white font-mono text-sm p-2 outline-none transition-colors"
      />
    </div>
  );

  return (
    <div data-testid="agent-registry-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">Agent Registry</h1>
          <p className="font-mono text-xs text-avaira-muted mt-1">{agents.length} AGENTS REGISTERED</p>
        </div>
        <div className="flex items-center gap-2">
          <button data-testid="refresh-agents-btn" onClick={fetchAgents} className="p-2 border border-avaira-border text-avaira-muted hover:text-avaira-cyan hover:border-avaira-cyan transition-colors">
            <RefreshCw size={14} />
          </button>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <button data-testid="register-agent-btn" className="cyber-btn bg-avaira-cyan text-black px-4 py-2 font-heading text-sm flex items-center gap-2">
                <UserPlus size={14} /> REGISTER AGENT
              </button>
            </DialogTrigger>
            <DialogContent className="bg-avaira-card border-avaira-border rounded-none max-w-md">
              <DialogHeader>
                <DialogTitle className="font-heading font-bold text-lg text-foreground uppercase tracking-tight">Register New Agent</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleRegister} className="space-y-3 mt-2" data-testid="register-agent-form">
                <InputField label="Agent Name" name="name" placeholder="TradingBot-Alpha" />
                <InputField label="Wallet Address (optional)" name="wallet_address" placeholder="0x..." />
                <InputField label="Collateral (AVAX)" name="collateral_amount" type="number" placeholder="1.0" />
                <InputField label="Mission Intent" name="mission_intent" placeholder="DeFi yield optimization" />
                <div className="border-t border-avaira-border pt-3">
                  <p className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-cyan mb-2">Risk Envelope</p>
                  <div className="grid grid-cols-2 gap-3">
                    <InputField label="Max TX Value" name="max_tx_value" type="number" />
                    <InputField label="Max Daily TXNs" name="max_daily_txns" type="number" />
                    <InputField label="Allowed Actions" name="allowed_actions" placeholder="transfer,swap,stake" />
                    <InputField label="Max Slippage" name="max_slippage" type="number" />
                  </div>
                </div>
                <button data-testid="submit-register-btn" type="submit" className="w-full cyber-btn bg-avaira-cyan text-black py-2 font-heading text-sm mt-2">
                  REGISTER & STAKE COLLATERAL
                </button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {agents.length === 0 ? (
        <div className="cyber-card p-12 text-center">
          <Shield size={40} className="text-avaira-dim mx-auto mb-3" strokeWidth={1} />
          <p className="font-heading text-lg text-avaira-muted uppercase">No Agents Registered</p>
          <p className="font-mono text-xs text-avaira-dim mt-1">Register an agent or run a simulation from the dashboard</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map(agent => <AgentCard key={agent.id} agent={agent} onRefresh={fetchAgents} scores={scores} />)}
        </div>
      )}
    </div>
  );
}
