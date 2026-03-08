import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import AgentRegistry from "@/pages/AgentRegistry";
import ExecutionFlow from "@/pages/ExecutionFlow";
import FreezeSlash from "@/pages/FreezeSlash";
import Treasury from "@/pages/Treasury";
import Reputation from "@/pages/Reputation";
import SmartContracts from "@/pages/SmartContracts";
import Underwriters from "@/pages/Underwriters";
import SDKDocs from "@/pages/SDKDocs";
import { Toaster } from "sonner";

function App() {
  return (
    <div className="min-h-screen bg-avaira-bg">
      <div className="noise-overlay" />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agents" element={<AgentRegistry />} />
            <Route path="/executions" element={<ExecutionFlow />} />
            <Route path="/freeze" element={<FreezeSlash />} />
            <Route path="/treasury" element={<Treasury />} />
            <Route path="/reputation" element={<Reputation />} />
            <Route path="/underwriters" element={<Underwriters />} />
            <Route path="/sdk" element={<SDKDocs />} />
            <Route path="/contracts" element={<SmartContracts />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: '#0A0A0A', border: '1px solid #333', color: '#E0E0E0', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8125rem', borderRadius: '0' },
        }}
      />
    </div>
  );
}

export default App;
