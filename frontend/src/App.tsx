import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import Optimize from "@/pages/Optimize";
import CoverLetter from "@/pages/CoverLetter";
import InterviewSessions from "@/pages/InterviewSessions";
import InterviewPrep from "@/pages/InterviewPrep";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";

function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const isLanding = location.pathname === "/";
  const hideNav =
    location.pathname.startsWith("/optimize") ||
    location.pathname.startsWith("/cover-letter") ||
    location.pathname.startsWith("/interview/");

  const hideSidebar = location.pathname.startsWith("/interview/");

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <div className="orb-blue" />
      <div className="orb-purple" />

      {!hideNav && <Navbar />}

      <div className="relative z-10 flex">
        {!isLanding && !hideSidebar && <Sidebar />}
        <div className={!isLanding && !hideSidebar ? "flex-1 md:ml-72" : "flex-1"}>
          {children}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppShell>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard/:sessionId" element={<Dashboard />} />
          <Route path="/optimize" element={<Optimize />} />
          <Route path="/cover-letter" element={<CoverLetter />} />
          <Route path="/interview" element={<InterviewSessions />} />
          <Route path="/interview/:sessionId" element={<InterviewPrep />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </AppShell>
  );
}
