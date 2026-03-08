import { useNavigate } from "react-router-dom";
import { Shield, FileKey, Heart, Zap, TrendingUp, Lock, Database, Globe, ChevronRight, Code, Users, Wallet, ArrowRight } from "lucide-react";

const PILLARS = [
  { icon: TrendingUp, title: "RATE", subtitle: "The Moody's Function", color: "#00F0FF", desc: "Every AI agent gets an Avaira Score (AAA to D). No enterprise will trust an unrated agent. The rating becomes the standard.", stat: "$50B+ market" },
  { icon: FileKey, title: "CLEAR", subtitle: "The DTCC Function", color: "#39FF14", desc: "Every agent transaction passes through our settlement layer. We see every execution. Unmatched data. Unmatched risk models.", stat: "$2.5Q processed/yr" },
  { icon: Heart, title: "INSURE", subtitle: "The Lloyd's Function", color: "#7000FF", desc: "Human underwriters stake capital against agent missions. Agent fails \u2192 collateral covers losses. Agent succeeds \u2192 underwriters earn yield.", stat: "$100B+ in premiums" },
];

const MOATS = [
  { icon: Database, title: "DATA FLYWHEEL", desc: "More agents \u2192 better risk models \u2192 more accurate scores \u2192 more enterprises \u2192 more agents. Gap widens over time." },
  { icon: Lock, title: "REGULATORY CAPTURE", desc: "Define the standard before regulators do. Regulation doesn't kill you. Regulation IS you." },
  { icon: Users, title: "THREE-SIDED NETWORK", desc: "Agents + Underwriters + Enterprises. Three-sided network effects are nearly impossible to replicate." },
  { icon: Shield, title: "SWITCHING COSTS", desc: "Behavioral history, Avaira Score, insurance coverage, enterprise contracts. Switching cost: 6+ months. Nobody switches." },
  { icon: Globe, title: "AVALANCHE L1", desc: "Sub-200ms finality. Sovereign rules. Custom gas economics. The speed required to be a real-time circuit breaker." },
];

const REVENUE = [
  { name: "Agent Registration", year1: "$1.2M", year5: "$240M", desc: "SaaS tiers: Free / Growth ($200/mo) / Enterprise ($2,000/mo)" },
  { name: "Underwriting Spread", year1: "$2M", year5: "$400M", desc: "5% protocol fee on every settled mission" },
  { name: "Slashing Revenue", year1: "$500K", year5: "$50M", desc: "20% of all slashed collateral \u2014 pure insurance profit" },
  { name: "Data & Analytics", year1: "$300K", year5: "$80M", desc: "Bloomberg Terminal for AI agents. $0.01/query API access" },
];

const SDK_CODE = `import { AvairaSDK } from '@avaira/sdk';

const avaira = new AvairaSDK({
  apiKey: 'your-api-key',
  network: 'fuji',
  chainId: 43113
});

// 1. Register agent
const agent = await avaira.register(wallet, config);

// 2. Declare intent
const mission = await avaira.declareIntent(plan);

// 3. Execute (AVAIRA monitors automatically)
const result = await avaira.execute(action);

// 4. Settle
const settlement = await avaira.settle(mission.id);`;

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-avaira-bg text-foreground overflow-x-hidden" data-testid="landing-page">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-avaira-bg/80 backdrop-blur-lg border-b border-avaira-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield size={20} className="text-avaira-cyan" strokeWidth={1.5} />
            <span className="font-heading font-bold text-xl text-avaira-cyan tracking-tight uppercase">AVAIRA</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="#pillars" className="font-mono text-xs text-avaira-muted hover:text-avaira-cyan transition-colors hidden sm:block">PROTOCOL</a>
            <a href="#moats" className="font-mono text-xs text-avaira-muted hover:text-avaira-cyan transition-colors hidden sm:block">MOATS</a>
            <a href="#revenue" className="font-mono text-xs text-avaira-muted hover:text-avaira-cyan transition-colors hidden sm:block">REVENUE</a>
            <a href="#sdk" className="font-mono text-xs text-avaira-muted hover:text-avaira-cyan transition-colors hidden sm:block">SDK</a>
            <button
              data-testid="launch-protocol-btn"
              onClick={() => navigate('/dashboard')}
              className="cyber-btn bg-avaira-cyan text-black px-4 py-2 font-heading text-xs flex items-center gap-1.5"
            >
              LAUNCH PROTOCOL <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 relative" data-testid="hero-section">
        <div className="max-w-5xl mx-auto">
          <div className="mb-4">
            <span className="font-mono text-[10px] text-avaira-cyan tracking-[0.3em] border border-avaira-cyan/30 px-3 py-1 bg-avaira-cyan/5">
              AVALANCHE L1 // EXECUTION CONTROL PROTOCOL
            </span>
          </div>
          <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl text-foreground uppercase tracking-tight leading-[1.1] max-w-4xl">
            The Trust Infrastructure for the{" "}
            <span className="text-avaira-cyan" style={{ textShadow: '0 0 30px rgba(0,240,255,0.3)' }}>Autonomous Economy</span>
          </h1>
          <p className="font-body text-base sm:text-lg text-avaira-muted mt-6 max-w-2xl leading-relaxed">
            We rate, clear, and insure every AI agent transaction on-chain &mdash; so machines can manage billions and humans can sleep at night.
          </p>
          <div className="flex items-center gap-4 mt-8">
            <button
              data-testid="hero-launch-btn"
              onClick={() => navigate('/dashboard')}
              className="cyber-btn bg-avaira-cyan text-black px-6 py-3 font-heading text-sm flex items-center gap-2"
            >
              LAUNCH PROTOCOL <ArrowRight size={16} />
            </button>
            <a href="#sdk" className="font-mono text-xs text-avaira-muted border border-avaira-border px-6 py-3 hover:border-avaira-cyan hover:text-avaira-cyan transition-colors">
              VIEW SDK
            </a>
          </div>
          <div className="grid grid-cols-3 gap-6 mt-16 max-w-lg">
            <div>
              <p className="font-heading font-bold text-2xl text-avaira-cyan">{'<'}200ms</p>
              <p className="font-mono text-[10px] text-avaira-dim uppercase tracking-wider mt-1">Finality</p>
            </div>
            <div>
              <p className="font-heading font-bold text-2xl text-avaira-green">0.5%</p>
              <p className="font-mono text-[10px] text-avaira-dim uppercase tracking-wider mt-1">Protocol Fee</p>
            </div>
            <div>
              <p className="font-heading font-bold text-2xl text-avaira-purple">AAA-D</p>
              <p className="font-mono text-[10px] text-avaira-dim uppercase tracking-wider mt-1">Agent Scoring</p>
            </div>
          </div>
        </div>
        {/* Grid bg effect */}
        <div className="absolute inset-0 -z-10" style={{ backgroundImage: 'linear-gradient(rgba(0,240,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,240,255,0.03) 1px, transparent 1px)', backgroundSize: '60px 60px' }} />
      </section>

      {/* Three Pillars */}
      <section id="pillars" className="py-20 px-6 border-t border-avaira-border" data-testid="pillars-section">
        <div className="max-w-6xl mx-auto">
          <p className="font-mono text-[10px] text-avaira-cyan tracking-[0.3em] mb-3">THE PROTOCOL</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight mb-12">
            Three Functions. One Protocol.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PILLARS.map((p) => (
              <div key={p.title} className="cyber-card corner-cut p-6 group" data-testid={`pillar-${p.title.toLowerCase()}`}>
                <div className="p-3 border w-fit mb-4" style={{ borderColor: `${p.color}40`, background: `${p.color}10` }}>
                  <p.icon size={20} style={{ color: p.color }} strokeWidth={1.5} />
                </div>
                <h3 className="font-heading font-bold text-xl uppercase tracking-tight" style={{ color: p.color }}>{p.title}</h3>
                <p className="font-mono text-[10px] text-avaira-dim uppercase tracking-widest mt-0.5">{p.subtitle}</p>
                <p className="font-body text-sm text-avaira-muted mt-3 leading-relaxed">{p.desc}</p>
                <div className="mt-4 pt-3 border-t border-avaira-border">
                  <span className="font-mono text-[10px] text-avaira-dim">COMPARABLE: </span>
                  <span className="font-mono text-xs" style={{ color: p.color }}>{p.stat}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 px-6 border-t border-avaira-border bg-avaira-card" data-testid="how-it-works-section">
        <div className="max-w-5xl mx-auto">
          <p className="font-mono text-[10px] text-avaira-cyan tracking-[0.3em] mb-3">EXECUTION FLOW</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight mb-10">
            How Every Transaction is Secured
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { step: "01", label: "REGISTER", desc: "Agent stakes collateral" },
              { step: "02", label: "DECLARE", desc: "Submit mission intent" },
              { step: "03", label: "VALIDATE", desc: "Risk envelope check" },
              { step: "04", label: "PERMIT", desc: "EIP-712 signed" },
              { step: "05", label: "EXECUTE", desc: "On-chain settlement" },
              { step: "06", label: "SETTLE", desc: "Fees split 85/10/5" },
            ].map((s) => (
              <div key={s.step} className="p-3 border border-avaira-border bg-avaira-bg relative group hover:border-avaira-cyan/50 transition-colors" data-testid={`step-${s.step}`}>
                <span className="font-heading font-bold text-3xl text-avaira-cyan/20 group-hover:text-avaira-cyan/40 transition-colors">{s.step}</span>
                <p className="font-heading font-bold text-sm text-foreground uppercase tracking-tight mt-1">{s.label}</p>
                <p className="font-mono text-[10px] text-avaira-dim mt-0.5">{s.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 p-4 border border-avaira-red/30 bg-avaira-red/5">
            <p className="font-heading font-bold text-sm text-avaira-red uppercase tracking-tight flex items-center gap-2">
              <Zap size={14} /> Deviation Detected?
            </p>
            <p className="font-mono text-xs text-avaira-muted mt-1">
              Agent instantly frozen. Collateral slashed. Insurance pool compensates backers. All within {'<'}200ms.
            </p>
          </div>
        </div>
      </section>

      {/* Five Moats */}
      <section id="moats" className="py-20 px-6 border-t border-avaira-border" data-testid="moats-section">
        <div className="max-w-6xl mx-auto">
          <p className="font-mono text-[10px] text-avaira-cyan tracking-[0.3em] mb-3">DEFENSIBILITY</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight mb-10">
            Five Moats. Unkillable.
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {MOATS.map((m, i) => (
              <div key={m.title} className="p-4 border border-avaira-border bg-avaira-card hover:border-avaira-cyan/30 transition-colors" data-testid={`moat-${i}`}>
                <m.icon size={18} className="text-avaira-cyan mb-3" strokeWidth={1.5} />
                <h3 className="font-heading font-bold text-sm text-foreground uppercase tracking-tight">{m.title}</h3>
                <p className="font-mono text-[10px] text-avaira-muted mt-2 leading-relaxed">{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Revenue */}
      <section id="revenue" className="py-20 px-6 border-t border-avaira-border bg-avaira-card" data-testid="revenue-section">
        <div className="max-w-5xl mx-auto">
          <p className="font-mono text-[10px] text-avaira-cyan tracking-[0.3em] mb-3">REVENUE ARCHITECTURE</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight mb-10">
            Four Revenue Streams From Day 1
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr>
                  <th>Stream</th>
                  <th>Description</th>
                  <th className="text-right">Year 1</th>
                  <th className="text-right">Year 5</th>
                </tr>
              </thead>
              <tbody>
                {REVENUE.map(r => (
                  <tr key={r.name}>
                    <td className="text-foreground font-semibold">{r.name}</td>
                    <td className="text-avaira-muted">{r.desc}</td>
                    <td className="text-right text-avaira-yellow">{r.year1}</td>
                    <td className="text-right text-avaira-green">{r.year5}</td>
                  </tr>
                ))}
                <tr className="border-t-2 border-avaira-cyan/30">
                  <td className="text-avaira-cyan font-bold">TOTAL</td>
                  <td></td>
                  <td className="text-right text-avaira-cyan font-bold">$4M</td>
                  <td className="text-right text-avaira-cyan font-bold">$770M</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="mt-6 p-4 border border-avaira-cyan/20 bg-avaira-cyan/5">
            <p className="font-mono text-xs text-avaira-muted">
              At 10x revenue multiple (standard for high-growth SaaS with network effects): <span className="text-avaira-cyan font-bold">$7.7B valuation by Year 5</span>
            </p>
          </div>
        </div>
      </section>

      {/* SDK */}
      <section id="sdk" className="py-20 px-6 border-t border-avaira-border" data-testid="sdk-section">
        <div className="max-w-5xl mx-auto">
          <p className="font-mono text-[10px] text-avaira-cyan tracking-[0.3em] mb-3">DEVELOPER EXPERIENCE</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight mb-3">
            4 Function Calls. That's It.
          </h2>
          <p className="font-body text-base text-avaira-muted mb-8 max-w-xl">
            If integration takes more than 10 minutes, the product has failed.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-black border border-avaira-border p-5 overflow-x-auto">
              <div className="flex items-center gap-2 mb-3">
                <Code size={14} className="text-avaira-cyan" />
                <span className="font-mono text-[10px] text-avaira-dim uppercase tracking-widest">TypeScript</span>
              </div>
              <pre className="font-mono text-xs text-avaira-green whitespace-pre leading-relaxed">{SDK_CODE}</pre>
            </div>
            <div className="space-y-3">
              {["register", "declareIntent", "execute", "settle"].map((fn, i) => (
                <div key={fn} className="p-3 border border-avaira-border hover:border-avaira-cyan/30 transition-colors">
                  <div className="flex items-center gap-2">
                    <span className="font-heading font-bold text-sm text-avaira-cyan">0{i + 1}</span>
                    <span className="font-mono text-sm text-foreground">.{fn}()</span>
                  </div>
                  <p className="font-mono text-[10px] text-avaira-dim mt-1">
                    {fn === "register" && "Register agent with collateral and risk envelope"}
                    {fn === "declareIntent" && "Declare mission intent before executing"}
                    {fn === "execute" && "Execute through AVAIRA's enforcement layer"}
                    {fn === "settle" && "Settle mission with 85/10/5 fee split"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-avaira-border bg-avaira-card" data-testid="cta-section">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">
            Build It. Own the Position. <span className="text-avaira-cyan">Never Let Go.</span>
          </h2>
          <p className="font-body text-base text-avaira-muted mt-4 max-w-xl mx-auto">
            The reason this becomes a billion-dollar company is not because the technology is revolutionary.
            It's because the position is irreplaceable.
          </p>
          <button
            data-testid="cta-launch-btn"
            onClick={() => navigate('/dashboard')}
            className="cyber-btn bg-avaira-cyan text-black px-8 py-3 font-heading text-sm mt-8 inline-flex items-center gap-2"
          >
            LAUNCH AVAIRA PROTOCOL <ArrowRight size={16} />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-avaira-border">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-avaira-cyan" strokeWidth={1.5} />
            <span className="font-heading font-bold text-sm text-avaira-cyan uppercase">AVAIRA</span>
            <span className="font-mono text-[9px] text-avaira-dim ml-2">AVALANCHE L1</span>
          </div>
          <p className="font-mono text-[10px] text-avaira-dim">EXECUTION CONTROL PROTOCOL v1.0</p>
        </div>
      </footer>
    </div>
  );
}
