import { useEffect, useState } from "react";
import axios from "axios";
import { Code, Shield, FileKey, Snowflake, Wallet, TrendingUp, Heart, ChevronDown, ChevronRight, AlertTriangle, Zap } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CONTRACT_ICONS = {
  AgentRegistry: Shield,
  ExecutionWallet: FileKey,
  FreezeSlash: Snowflake,
  Treasury: Wallet,
  ReputationEngine: TrendingUp,
  InsurancePool: Heart,
};

const ContractCard = ({ contract }) => {
  const [expanded, setExpanded] = useState(false);
  const Icon = CONTRACT_ICONS[contract.name] || Code;

  return (
    <div className="cyber-card" data-testid={`contract-${contract.name}`}>
      <button
        data-testid={`toggle-contract-${contract.name}`}
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 border border-avaira-cyan/30 bg-avaira-cyan/5">
            <Icon size={16} className="text-avaira-cyan" strokeWidth={1.5} />
          </div>
          <div>
            <h3 className="font-heading font-bold text-base text-foreground uppercase tracking-tight">{contract.name}</h3>
            <p className="font-mono text-[10px] text-avaira-muted mt-0.5 truncate max-w-[300px]">{contract.address}</p>
          </div>
        </div>
        {expanded ? <ChevronDown size={16} className="text-avaira-cyan" /> : <ChevronRight size={16} className="text-avaira-muted" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-avaira-border pt-4 animate-slide-in">
          <p className="font-mono text-xs text-avaira-muted">{contract.description}</p>

          {/* State Variables */}
          <div>
            <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-cyan mb-2">State Variables</h4>
            <div className="space-y-1">
              {contract.state_variables.map((sv, i) => (
                <div key={i} className="flex items-start gap-2 p-1.5 bg-black/40">
                  <code className="font-mono text-[11px] text-avaira-green whitespace-nowrap">{sv.type}</code>
                  <code className="font-mono text-[11px] text-foreground">{sv.name}</code>
                  <span className="font-mono text-[10px] text-avaira-dim ml-auto">{sv.description}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Functions */}
          <div>
            <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-cyan mb-2">Functions</h4>
            <div className="space-y-1.5">
              {contract.functions.map((fn, i) => (
                <div key={i} className="p-2 bg-black/40 border-l-2 border-avaira-cyan/30">
                  <div className="flex items-center gap-2 flex-wrap">
                    <code className="font-mono text-[11px] text-avaira-cyan font-bold">{fn.name}</code>
                    <code className="font-mono text-[10px] text-avaira-muted">{fn.params}</code>
                    {fn.modifier && (
                      <span className="font-mono text-[9px] px-1 py-0.5 border border-avaira-purple/30 text-avaira-purple">{fn.modifier}</span>
                    )}
                  </div>
                  {fn.returns && <p className="font-mono text-[10px] text-avaira-green mt-0.5">returns {fn.returns}</p>}
                  <p className="font-mono text-[10px] text-avaira-dim mt-0.5">{fn.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Events */}
          <div>
            <h4 className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-cyan mb-2">Events</h4>
            <div className="space-y-1">
              {contract.events.map((ev, i) => (
                <div key={i} className="p-1.5 bg-black/40">
                  <code className="font-mono text-[10px] text-avaira-yellow break-all">{ev}</code>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function SmartContracts() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/contracts`)
      .then(res => { setData(res.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <p className="font-mono text-xs text-avaira-muted animate-glow-pulse">LOADING CONTRACT DATA...</p>
    </div>
  );

  return (
    <div data-testid="smart-contracts-page">
      <div className="mb-6">
        <h1 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">Smart Contracts</h1>
        <p className="font-mono text-xs text-avaira-muted mt-1">AVALANCHE FUJI C-CHAIN ARCHITECTURE</p>
      </div>

      {/* Contracts */}
      {data && (
        <div className="space-y-3 mb-6">
          {data.contracts.map(contract => <ContractCard key={contract.name} contract={contract} />)}
        </div>
      )}

      {/* Security & Gas */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-green mb-3 flex items-center gap-2">
              <Shield size={14} /> Security Assumptions
            </h2>
            <div className="space-y-2">
              {data.security_assumptions.map((sa, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <span className="font-mono text-[10px] text-avaira-green mt-0.5">{'>'}</span>
                  <p className="font-mono text-[11px] text-foreground">{sa}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-red mb-3 flex items-center gap-2">
              <AlertTriangle size={14} /> Attack Surfaces
            </h2>
            <div className="space-y-2">
              {data.attack_surfaces.map((as2, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <span className="font-mono text-[10px] text-avaira-red mt-0.5">!</span>
                  <p className="font-mono text-[11px] text-foreground">{as2}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="cyber-card p-4">
            <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-yellow mb-3 flex items-center gap-2">
              <Zap size={14} /> Gas Considerations
            </h2>
            <div className="space-y-2">
              {data.gas_considerations.map((gc, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <span className="font-mono text-[10px] text-avaira-yellow mt-0.5">~</span>
                  <p className="font-mono text-[11px] text-foreground">{gc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
