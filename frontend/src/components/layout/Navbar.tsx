import { Link, useLocation } from "react-router-dom";
import { useAppStore } from "@/store/appStore";

const navItems = [
  { label: "Search",       href: "/" },
  { label: "Dashboard",    href: "/dashboard" },
  { label: "Optimize",     href: "/optimize" },
  { label: "Cover Letter", href: "/cover-letter" },
];

export default function Navbar() {
  const location = useLocation();
  const { resumeFilename, activeSession } = useAppStore();

  const isActive = (href: string) => {
    if (href === "/") return location.pathname === "/";
    if (href === "/dashboard") return location.pathname.startsWith("/dashboard");
    return location.pathname.startsWith(href);
  };

  const dashboardHref = activeSession?.id ? `/dashboard/${activeSession.id}` : null;

  return (
    <nav
      className="fixed top-0 w-full z-50 flex justify-between items-center px-10 py-4"
      style={{
        background: "rgba(30,32,36,0.8)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
    >
      {/* Logo */}
      <Link to="/" className="font-manrope font-light tracking-[0.2em] text-[#c6c6c7] uppercase text-base select-none">
        JobHunt <span className="silver-gradient font-medium">AI</span>
      </Link>

      {/* Nav links */}
      <div className="hidden md:flex items-center space-x-8">
        {navItems.map(({ label, href }) => {
          const active = isActive(href);
          const resolvedHref = href === "/dashboard" ? (dashboardHref ?? "/") : href;
          if (href === "/dashboard" && !activeSession) return null;
          return (
            <Link
              key={href}
              to={resolvedHref}
              className={
                active
                  ? "font-manrope text-sm tracking-wide font-medium transition-all"
                  : "text-[#c6c6c7]/50 hover:text-[#c6c6c7] transition-colors font-manrope text-sm tracking-wide font-light"
              }
              style={active ? {
                color: "#c6c6c7",
                borderBottom: "1px solid rgba(198,198,199,0.35)",
                paddingBottom: "2px",
              } : {}}
            >
              {label}
            </Link>
          );
        })}
      </div>

      {/* Resume status */}
      <div className="flex items-center gap-3">
        {resumeFilename ? (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)" }}>
            <div className="w-1.5 h-1.5 rounded-full bg-success" />
            <span className="text-xs text-success hidden sm:block">Resume loaded</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(68,71,72,0.4)" }}>
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#5c5e63" }} />
            <span className="text-xs text-text-muted hidden sm:block">No resume</span>
          </div>
        )}
      </div>

      {/* RGB gradient bottom border */}
      <div className="absolute bottom-0 left-0 right-0 h-px"
        style={{ background: "linear-gradient(to right, transparent, rgba(124,208,255,0.2), rgba(214,186,255,0.2), rgba(255,200,124,0.15), transparent)" }}
      />
    </nav>
  );
}
