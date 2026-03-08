import { NavLink, Outlet, useLocation } from "react-router-dom";
import { LayoutDashboard, UserCheck, Workflow, ShieldOff, Wallet, TrendingUp, Code, Menu, X, Users, BookOpen, Home } from "lucide-react";
import { useState } from "react";

const NAV_ITEMS = [
  { path: "/dashboard", label: "DASHBOARD", icon: LayoutDashboard },
  { path: "/agents", label: "AGENT REGISTRY", icon: UserCheck },
  { path: "/executions", label: "EXECUTION FLOW", icon: Workflow },
  { path: "/underwriters", label: "UNDERWRITERS", icon: Users },
  { path: "/freeze", label: "FREEZE / SLASH", icon: ShieldOff },
  { path: "/treasury", label: "TREASURY", icon: Wallet },
  { path: "/reputation", label: "REPUTATION", icon: TrendingUp },
  { path: "/sdk", label: "SDK DOCS", icon: BookOpen },
  { path: "/contracts", label: "CONTRACTS", icon: Code },
];

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex min-h-screen" data-testid="app-layout">
      {/* Mobile toggle */}
      <button
        data-testid="mobile-menu-toggle"
        className="fixed top-4 left-4 z-50 lg:hidden p-2 border border-avaira-border bg-avaira-card"
        onClick={() => setMobileOpen(!mobileOpen)}
      >
        {mobileOpen ? <X size={20} className="text-avaira-cyan" /> : <Menu size={20} className="text-avaira-cyan" />}
      </button>

      {/* Sidebar */}
      <aside
        data-testid="sidebar"
        className={`fixed inset-y-0 left-0 z-40 w-56 bg-avaira-card border-r border-avaira-border flex flex-col transition-transform duration-300 ${mobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      >
        {/* Logo */}
        <div className="p-5 border-b border-avaira-border">
          <h1 className="font-heading font-bold text-2xl tracking-tight text-avaira-cyan uppercase" data-testid="app-logo">
            AVAIRA
          </h1>
          <p className="font-mono text-[10px] text-avaira-muted mt-1 tracking-widest">EXECUTION CONTROL PROTOCOL</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4" data-testid="main-nav">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                data-testid={`nav-${item.path === "/" ? "dashboard" : item.path.slice(1)}`}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-5 py-2.5 text-xs font-mono tracking-wider transition-all duration-200 border-l-2 ${
                  isActive
                    ? "border-avaira-cyan text-avaira-cyan bg-avaira-cyan/5"
                    : "border-transparent text-avaira-muted hover:text-foreground hover:border-avaira-border hover:bg-white/[0.02]"
                }`}
              >
                <item.icon size={16} strokeWidth={1.5} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-avaira-border">
          <div className="flex items-center gap-2">
            <span className="status-dot active" />
            <span className="font-mono text-[10px] text-avaira-green tracking-wider">PROTOCOL ONLINE</span>
          </div>
          <p className="font-mono text-[9px] text-avaira-dim mt-1">AVALANCHE FUJI C-CHAIN</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 lg:ml-56 min-h-screen" data-testid="main-content">
        <div className="p-6 md:p-8">
          <Outlet />
        </div>
      </main>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 bg-black/60 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}
    </div>
  );
}
