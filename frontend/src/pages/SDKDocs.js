import { useEffect, useState } from "react";
import axios from "axios";
import { Code, Terminal, Copy, Check, ChevronRight } from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CopyBtn = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Copied to clipboard");
    });
  };
  return (
    <button data-testid="copy-btn" onClick={handle} className="p-1 text-avaira-muted hover:text-avaira-cyan transition-colors">
      {copied ? <Check size={12} className="text-avaira-green" /> : <Copy size={12} />}
    </button>
  );
};

const CodeBlock = ({ code, lang = "typescript" }) => (
  <div className="relative bg-black border border-avaira-border overflow-x-auto">
    <div className="flex items-center justify-between px-3 py-1.5 border-b border-avaira-border">
      <span className="font-mono text-[9px] text-avaira-dim uppercase tracking-widest">{lang}</span>
      <CopyBtn text={code} />
    </div>
    <pre className="p-4 font-mono text-xs text-avaira-green whitespace-pre leading-relaxed overflow-x-auto">{code}</pre>
  </div>
);

export default function SDKDocs() {
  const [docs, setDocs] = useState(null);
  const [activeFunc, setActiveFunc] = useState(0);

  useEffect(() => {
    axios.get(`${API}/sdk/docs`).then(res => setDocs(res.data)).catch(console.error);
  }, []);

  if (!docs) return (
    <div className="flex items-center justify-center h-64">
      <p className="font-mono text-xs text-avaira-muted animate-glow-pulse">LOADING SDK DOCS...</p>
    </div>
  );

  return (
    <div data-testid="sdk-docs-page">
      <div className="mb-6">
        <h1 className="font-heading font-bold text-2xl sm:text-3xl text-foreground uppercase tracking-tight">SDK Documentation</h1>
        <p className="font-mono text-xs text-avaira-muted mt-1">INTEGRATE IN 4 FUNCTION CALLS</p>
      </div>

      {/* Install */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="cyber-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Terminal size={14} className="text-avaira-cyan" />
            <span className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest">TypeScript Installation</span>
          </div>
          <CodeBlock code={docs.install.typescript} lang="bash" />
        </div>
        <div className="cyber-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Terminal size={14} className="text-avaira-cyan" />
            <span className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest">Rust Installation</span>
          </div>
          <CodeBlock code={docs.install.rust} lang="bash" />
        </div>
      </div>

      {/* Quick Start */}
      <div className="cyber-card p-4 mb-6">
        <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-cyan mb-3 flex items-center gap-2">
          <Code size={14} /> Quick Start
        </h2>
        <CodeBlock code={docs.quick_start} lang="typescript" />
      </div>

      {/* Function Reference */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Function Nav */}
        <div className="space-y-1.5">
          <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">API Reference</h2>
          {docs.functions.map((fn, i) => (
            <button
              key={fn.name}
              data-testid={`sdk-func-${fn.name}`}
              onClick={() => setActiveFunc(i)}
              className={`w-full text-left p-3 border transition-colors flex items-center justify-between ${
                activeFunc === i ? 'border-avaira-cyan bg-avaira-cyan/5 text-avaira-cyan' : 'border-avaira-border text-avaira-muted hover:border-avaira-cyan/30 hover:text-foreground'
              }`}
            >
              <div>
                <p className="font-mono text-sm">.{fn.name}()</p>
                <p className="font-mono text-[10px] text-avaira-dim mt-0.5">{fn.description}</p>
              </div>
              <ChevronRight size={14} className={activeFunc === i ? 'text-avaira-cyan' : 'text-avaira-dim'} />
            </button>
          ))}
        </div>

        {/* Function Detail */}
        <div className="lg:col-span-2 cyber-card p-4">
          {docs.functions[activeFunc] && (
            <div data-testid="sdk-func-detail">
              <div className="flex items-center gap-3 mb-4">
                <span className="font-heading font-bold text-2xl text-avaira-cyan">.{docs.functions[activeFunc].name}()</span>
              </div>
              <p className="font-body text-sm text-avaira-muted mb-4">{docs.functions[activeFunc].description}</p>

              {/* Parameters */}
              <div className="mb-4">
                <h3 className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-muted mb-2">Parameters</h3>
                <div className="space-y-1">
                  {docs.functions[activeFunc].params.map((p, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 bg-black/40">
                      <code className="font-mono text-xs text-avaira-cyan">{p.name}</code>
                      <code className="font-mono text-[10px] text-avaira-purple">{p.type}</code>
                    </div>
                  ))}
                </div>
              </div>

              {/* Returns */}
              <div className="mb-4">
                <h3 className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-muted mb-2">Returns</h3>
                <div className="p-2 bg-black/40">
                  <code className="font-mono text-xs text-avaira-green">{docs.functions[activeFunc].returns}</code>
                </div>
              </div>

              {/* Example */}
              <div>
                <h3 className="font-heading font-semibold text-xs uppercase tracking-wider text-avaira-muted mb-2">Example</h3>
                <CodeBlock code={docs.functions[activeFunc].example} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Fee Structure */}
      <div className="cyber-card p-4 mt-6">
        <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">Fee Structure</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-3 border border-avaira-border">
            <p className="font-heading font-bold text-lg text-avaira-green">85%</p>
            <p className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest mt-0.5">Agent Payout</p>
            <p className="font-mono text-[10px] text-avaira-dim mt-1">The AI agent earns the majority of the mission value</p>
          </div>
          <div className="p-3 border border-avaira-border">
            <p className="font-heading font-bold text-lg text-avaira-cyan">10%</p>
            <p className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest mt-0.5">Underwriter Yield</p>
            <p className="font-mono text-[10px] text-avaira-dim mt-1">Human underwriters earn yield for backing the mission</p>
          </div>
          <div className="p-3 border border-avaira-border">
            <p className="font-heading font-bold text-lg text-avaira-purple">5%</p>
            <p className="font-mono text-[10px] text-avaira-muted uppercase tracking-widest mt-0.5">Protocol Fee</p>
            <p className="font-mono text-[10px] text-avaira-dim mt-1">AVAIRA protocol fee for settlement infrastructure</p>
          </div>
        </div>
      </div>

      {/* Scoring Reference */}
      <div className="cyber-card p-4 mt-4">
        <h2 className="font-heading font-semibold text-sm uppercase tracking-wider text-avaira-muted mb-3">Avaira Score Reference</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          {[
            { grade: 'AAA', range: '90-100', color: '#39FF14' },
            { grade: 'AA', range: '80-89', color: '#00F0FF' },
            { grade: 'A', range: '70-79', color: '#00F0FF' },
            { grade: 'BBB', range: '60-69', color: '#FFD300' },
            { grade: 'BB', range: '50-59', color: '#FFD300' },
            { grade: 'B', range: '40-49', color: '#FF8C00' },
            { grade: 'CCC', range: '30-39', color: '#FF003C' },
            { grade: 'D', range: '0-29', color: '#FF003C' },
          ].map(g => (
            <div key={g.grade} className="p-2 border border-avaira-border text-center">
              <p className="font-heading font-bold text-lg" style={{ color: g.color }}>{g.grade}</p>
              <p className="font-mono text-[9px] text-avaira-dim">{g.range}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
