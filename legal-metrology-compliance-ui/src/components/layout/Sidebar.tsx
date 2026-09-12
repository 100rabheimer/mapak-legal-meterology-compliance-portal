import { BarChart3, ClipboardPlus, FileText, Gavel, LayoutDashboard, LogOut, PackageSearch, Settings, UserCog } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import type { UserRole } from "../../types/auth";
import { useAuthStore } from "../../stores/authStores";

interface SidebarItem {
  name: string;
  to: string;
  icon: LucideIcon;
  roles: UserRole[];
}

const items: SidebarItem[] = [
  { name: "Dashboard", to: "/", icon: LayoutDashboard, roles: ["officer", "admin"] },
  { name: "New Inspection", to: "/inspections/new", icon: ClipboardPlus, roles: ["officer"] },
  { name: "Product Repository", to: "/products", icon: PackageSearch, roles: ["officer"] },
  { name: "Reports", to: "/reports", icon: FileText, roles: ["officer"] },
  { name: "Legal Rules", to: "/rules", icon: Gavel, roles: ["admin"] },
  { name: "Analytics", to: "/analytics", icon: BarChart3, roles: ["officer"] },
  { name: "Manage Officers", to: "/admin/officers", icon: UserCog, roles: ["admin"] },
  { name: "Settings", to: "/settings", icon: Settings, roles: ["officer", "admin"] },
];
interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export function Sidebar({ isOpen, setIsOpen }: SidebarProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const visibleItems = items.filter((item) => user && item.roles.includes(user.role));

  return (
    <aside className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-slate-200 bg-white transition-all duration-300 lg:flex dark:border-slate-800 dark:bg-slate-900 ${isOpen ? "w-72" : "w-20"}`}>
      <div className={`relative flex shrink-0 items-center border-b border-slate-100 dark:border-slate-800 ${isOpen ? "h-20 px-6 gap-4" : "h-20 justify-center"}`}>
        <img src="/src/assets/mapak-logo.png" alt="MAPAK Logo" className={`object-contain ${isOpen ? "h-12 w-12" : "h-10 w-10"}`} />
        {isOpen && (
          <div className="overflow-hidden whitespace-nowrap">
            <p className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">MAPAK</p>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Legal Metrology Portal</p>
          </div>
        )}
        
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`absolute -right-3 top-1/2 -translate-y-1/2 flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm transition-transform hover:bg-slate-50 hover:text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-slate-200 ${isOpen ? "" : "rotate-180"}`}
          aria-label="Toggle sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
      </div>
      <nav className={`flex-1 overflow-y-auto py-6 ${isOpen ? "px-4 space-y-1" : "px-2 space-y-2"}`}>
        {visibleItems.map(({ name, to, icon: Icon }) => { 
          const href = name === "Dashboard" && user?.role === "admin" ? "/admin/dashboard" : to; 
          return (
            <NavLink 
              key={name} 
              to={href} 
              className={({isActive}) => `flex items-center rounded-xl transition-colors ${isOpen ? "gap-3 px-4 py-3 text-sm font-medium" : "justify-center p-3"} ${isActive ? "bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"}`}
              title={!isOpen ? name : undefined}
            >
              <Icon className={`shrink-0 ${isOpen ? "h-5 w-5" : "h-6 w-6"}`} />
              {isOpen && <span className="truncate">{name}</span>}
            </NavLink>
          ); 
        })}
      </nav>
      <div className={`m-4 ${isOpen ? "space-y-3" : "flex justify-center"}`}>
        <button
          type="button"
          onClick={handleLogout}
          className={`flex items-center rounded-xl text-rose-700 transition hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40 ${isOpen ? "w-full gap-3 px-4 py-3 text-sm font-medium" : "p-3"}`}
          title={!isOpen ? "Log out" : undefined}
        >
          <LogOut className={`shrink-0 ${isOpen ? "h-5 w-5" : "h-6 w-6"}`} />
          {isOpen && <span>Log out</span>}
        </button>
      </div>
    </aside>
  );
}
