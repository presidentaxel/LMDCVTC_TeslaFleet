import { NavLink, Outlet } from "react-router-dom";
import "./AppShell.css";

const NAV = [
  { to: "/setup", label: "Configuration", icon: "⚙" },
  { to: "/fleet", label: "Flotte", icon: "🚗" },
  { to: "/vehicles", label: "Véhicules", icon: "📋" },
  { to: "/commands", label: "Commandes", icon: "🎛" },
  { to: "/developer", label: "Développeur", icon: "</>" },
] as const;

export default function AppShell() {
  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <div className="shell-brand">
          <span className="shell-logo">T</span>
          <span>Gestion LMDC VTC</span>
        </div>
        <nav className="shell-nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `shell-nav-item${isActive ? " active" : ""}`
              }
            >
              <span className="shell-nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="shell-footer">Fleet API · AXEL PROJECT</p>
      </aside>
      <main className="shell-main">
        <Outlet />
      </main>
    </div>
  );
}
