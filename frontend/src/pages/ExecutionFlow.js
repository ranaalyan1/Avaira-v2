import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Send, CheckCircle, XCircle, Clock, FileKey, Shield, Zap, RefreshCw } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STEP_ICONS = { request_submitted: Send, risk_validation: Shield, permit_signed: FileKey, permit_verified: CheckCircle, transaction_executed: Zap, fee_deducted: Clock };

const TimelineStep = ({ step, isLast }) => {
  const Icon = STEP_ICONS[step.step] || Clock;
  const isComplete = step.status === "completed";
  const isFailed = step.status === "failed";

  return (
    <div className="flex gap-3 relative" data-testid={`timeline-step-${step.step}`}>
      <div className="flex flex-col items-center">
        <div className={`timeline-dot ${isComplete ? 'completed' : isFailed ? 'failed' : ''}`} />
        {!isLast && <div className="w-[2px] flex-1 min-h-[24px]" style={{ background: isComplete ? '#00F0FF40' : '#33333380' }} />}
      </div>
      <div className="pb-4 flex-1">
        <div className="flex items-center gap-2">
          <Icon size={12} strokeWidth={1.5} className={isComplete ? 'text-avaira-cyan' : isFailed ? 'text-avaira-red' : 'text-avaira-muted'} />
          <span className="font-mono text-xs uppercase tracking-wider" style={{ color: isComplete ? '#00F0FF' : isFailed ? '#FF003C' : '#858585' }}>
            {step.step.replace(/_/g, ' ')}
          </span>
          <span className={`font-mono text-[10px] px-1.5 py-0.5 border ${isComplete ? 'border-green-500/30 text-green-400' : isFailed ? 'border-red-500/30 text-red-400' : 'border-white/10 text-avaira-muted'}`}>
            {step.status}
          </span>
        </div>
        <p className="font-mono text-[11px] text-avaira-muted mt-1">{step.details}</p>
        <p className="font-mono text-[9px] text-avaira-dim mt-0.5">{new Date(step.timestamp).toLocaleString()}</p>
      </div>
    </div>
  );
};

export default function ExecutionFlow() {
  const [executions, setExecutions] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedExec, setSelectedExec] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ agent_id: "", action: "swap", target_address: "", value: "1.0", chain_id: "43113" });

  const fetchData = useCallback(async () => {
    try {
      const [execRes, agentRes] = await Promise.all([
        axios.get(`${API}/executions`),
        axios.get(`${API}/agents`)
      ]);
      setExecutions(execRes.data);
      setAgents(agentRes.data);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.agent_id) return toast.error("Select an agent");
    try {
      const res = await axios.post(`${API}/executions/request`, {
        agent_id: form.agent_id,
        action: form.action,
        target_address: form.target_address || "0x" + Array(40).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join(''),
        value: parseFloat(form.value),
        chain_id: form.chain_id
      });
      toast.success(`Execution ${res.data.status}`);
      setOpen(false);
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Execution request failed");
    }
  };

  const statusColor = (s) => {
    if (s === 'completed') return '#39FF14';
    if (s.includes('rejected') || s.includes('invalid')) return '#FF003C';
    return '#FFD300';
  };

  return (
    <div data-testid="execution-flow-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">Execution Flow</h1>
          <p className="font-mono text-xs text-avaira-muted mt-1">{executions.length} EXECUTIONS RECORDED</p>
        </div>
        <div className="flex items-center gap-2">
          <button data-testid="refresh-executions-btn" onClick={fetchData} className="p-2 border border-avaira-border text-avaira-muted hover:text-avaira-cyan hover:border-avaira-cyan transition-colors">
            <RefreshCw size={14} />
          </button>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <button data-testid="new-execution-btn" className="cyber-btn bg-avaira-cyan text-black px-4 py-2 font-heading text-sm flex items-center gap-2">
                <Send size={14} /> NEW EXECUTION
              </button>
            </DialogTrigger>
            <DialogContent className="bg-avaira-card border-avaira-border rounded-none max-w-md">
              <DialogHeader>
                <DialogTitle className="font-heading font-bold text-lg text-foreground uppercase tracking-tight">Submit Execution Request</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-3 mt-2" data-testid="execution-request-form">
                <div>
                  <label className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest block mb-1">Agent</label>
                  <select
                    data-testid="exec-agent-select"
                    value={form.agent_id}
                    onChange={(e) => setForm(p => ({ ...p, agent_id: e.target.value }))}
                    className="w-full bg-black border border-white/20 focus:border-avaira-cyan text-white font-mono text-sm p-2 outline-none"
                  >
                    <option value="">Select agent...</option>
                    {agents.filter(a => a.status === 'active').map(a => (
                      <option key={a.id} value={a.id}>{a.name} (Rep: {a.reputation})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest block mb-1">Action</label>
                  <select
                    data-testid="exec-action-select"
                    value={form.action}
                    onChange={(e) => setForm(p => ({ ...p, action: e.target.value }))}
                    className="w-full bg-black border border-white/20 focus:border-avaira-cyan text-white font-mono text-sm p-2 outline-none"
                  >
                    {["transfer", "swap", "stake", "unstake", "liquidate", "bridge"].map(a => (
                      <option key={a} value={a}>{a.toUpperCase()}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest block mb-1">Value (AVAX)</label>
                  <input
                    data-testid="exec-value-input"
                    type="number"
                    step="0.01"
                    value={form.value}
                    onChange={(e) => setForm(p => ({ ...p, value: e.target.value }))}
                    className="w-full bg-black border border-white/20 focus:border-avaira-cyan text-white font-mono text-sm p-2 outline-none"
                  />
                </div>
                <div>
                  <label className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest block mb-1">Target Address</label>
                  <input
                    data-testid="exec-target-input"
                    type="text"
                    value={form.target_address}
                    onChange={(e) => setForm(p => ({ ...p, target_address: e.target.value }))}
                    placeholder="0x... (auto-generated if empty)"
                    className="w-full bg-black border border-white/20 focus:border-avaira-cyan text-white font-mono text-sm p-2 outline-none"
                  />
                </div>
                <button data-testid="submit-execution-btn" type="submit" className="w-full cyber-btn bg-avaira-cyan text-black py-2 font-heading text-sm">
                  SUBMIT EXECUTION REQUEST
                </button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Execution List */}
        <div className="lg:col-span-2 cyber-card p-4">
          <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">Execution History</h2>
          {executions.length === 0 ? (
            <div className="text-center py-8">
              <Zap size={32} className="text-avaira-dim mx-auto mb-2" strokeWidth={1} />
              <p className="font-mono text-xs text-avaira-dim">NO EXECUTIONS</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Action</th>
                    <th className="text-right">Value</th>
                    <th className="text-right">Fee</th>
                    <th>Status</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map(ex => (
                    <tr key={ex.id} className="cursor-pointer" onClick={() => setSelectedExec(ex)} data-testid={`exec-row-${ex.id}`}>
                      <td className="text-foreground">{ex.agent_name}</td>
                      <td className="uppercase text-avaira-cyan">{ex.action}</td>
                      <td className="text-right text-foreground">{ex.value.toFixed(4)}</td>
                      <td className="text-right text-avaira-yellow">{ex.fee_deducted.toFixed(6)}</td>
                      <td>
                        <span className="font-mono text-[10px] px-1.5 py-0.5 border" style={{ borderColor: statusColor(ex.status) + '40', color: statusColor(ex.status) }}>
                          {ex.status.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="text-avaira-dim">{new Date(ex.created_at).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Timeline Detail */}
        <div className="cyber-card p-4">
          <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">Execution Lifecycle</h2>
          {selectedExec ? (
            <div data-testid="execution-timeline">
              <div className="mb-3 pb-3 border-b border-avaira-border">
                <p className="font-mono text-xs text-avaira-cyan">{selectedExec.agent_name}</p>
                <p className="font-mono text-[10px] text-avaira-muted mt-0.5">ID: {selectedExec.id.slice(0, 8)}...</p>
              </div>
              <div className="relative">
                {selectedExec.lifecycle.map((step, i) => (
                  <TimelineStep key={i} step={step} isLast={i === selectedExec.lifecycle.length - 1} />
                ))}
              </div>
              {selectedExec.permit && (
                <div className="mt-3 pt-3 border-t border-avaira-border">
                  <p className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest mb-1">EIP-712 Permit</p>
                  <div className="bg-black p-2 font-mono text-[10px] text-avaira-cyan break-all max-h-32 overflow-y-auto">
                    <p>SIG: {selectedExec.permit.signature}</p>
                    <p className="text-avaira-muted mt-1">HASH: {selectedExec.permit.typedDataHash}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="font-mono text-xs text-avaira-dim">SELECT AN EXECUTION</p>
              <p className="font-mono text-[10px] text-avaira-dim mt-1">Click a row to view lifecycle</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
