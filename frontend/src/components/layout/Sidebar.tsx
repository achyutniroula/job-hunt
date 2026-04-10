import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Sparkles, Mail, Search } from "lucide-react";
import clsx from "clsx";
import { useAppStore } from "@/store/appStore";

const navItems = [
  { label: "Search",       href: "/",             icon: Search },
  { label: "Dashboard",    href: "/dashboard",    icon: LayoutDashboard },
  { label: "Optimize",     href: "/optimize",     icon: Sparkles },
  { label: "Cover Letter", href: "/cover-letter", icon: Mail },
];

export default function Sidebar() {
  const location = useLocation();
  const { activeSession } = useAppStore();

  const isActive = (href: string) => {
    if (href === "/") return location.pathname === "/";
    if (href === "/dashboard") return location.pathname.startsWith("/dashboard");
    return location.pathname.startsWith(href);
  };

  const dashboardHref = activeSession?.id ? `/dashboard/${activeSession.id}` : null;

  return (
    <aside
      className="hidden md:flex fixed left-0 top-[57px] w-72 flex-col py-8 z-40"
      style={{ height: "calc(100vh - 57px)", background: "#111317", borderRight: "1px solid rgba(255,255,255,0.04)" }}
    >
      {/* Nav */}
      <nav className="flex-1 space-y-1">
        {navItems.map(({ label, href, icon: Icon }) => {
          const active = isActive(href);
          if (href === "/dashboard" && !activeSession) return null;
          const resolvedHref = href === "/dashboard" ? (dashboardHref ?? "/") : href;

          return (
            <Link
              key={href}
              to={resolvedHref}
              className={clsx(
                "flex items-center px-8 py-3.5 transition-all text-sm group",
                active
                  ? "text-[#e2e2e8] bg-white/[0.04]"
                  : "text-[#c6c6c7]/40 hover:text-[#c6c6c7] hover:bg-[#1e2024]"
              )}
              style={active ? {
                borderLeft: "2px solid rgba(198,198,199,0.6)",
              } : { borderLeft: "2px solid transparent" }}
            >
              <span className="mr-4">
                <Icon className={clsx("w-4 h-4 transition-colors", active ? "text-[#c6c6c7]" : "group-hover:text-[#c6c6c7]/70")} />
              </span>
              <span className="font-manrope font-normal">{label}</span>
            </Link>
          );
        })}
      </nav>

    </aside>
  );
}
