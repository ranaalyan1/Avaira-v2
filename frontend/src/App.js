import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useState, createContext, useContext, useCallback } from "react";
import axios from "axios";
import Layout from "@/components/Layout";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
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

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthContext = createContext({ user: null, setUser: () => {}, logout: () => {} });
export const useAuth = () => useContext(AuthContext);

function AuthCallbackHandler() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useAuth();

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    if (sessionId) {
      axios.post(`${API}/auth/session`, { session_id: sessionId }, { withCredentials: true })
        .then(res => { setUser(res.data); navigate('/dashboard', { replace: true }); })
        .catch(() => navigate('/login', { replace: true }));
    }
  }, [searchParams, navigate, setUser]);

  return null;
}

function AppRoutes() {
  return (
    <>
      <AuthCallbackHandler />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
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
    </>
  );
}

function App() {
  const [user, setUser] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(res.data);
    } catch { /* not logged in */ }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  const logout = async () => {
    try { await axios.post(`${API}/auth/logout`, {}, { withCredentials: true }); } catch {}
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      <div className="min-h-screen bg-avaira-bg">
        <div className="noise-overlay" />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: '#0A0A0A', border: '1px solid #333', color: '#E0E0E0', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8125rem', borderRadius: '0' },
          }}
        />
      </div>
    </AuthContext.Provider>
  );
}

export default App;
