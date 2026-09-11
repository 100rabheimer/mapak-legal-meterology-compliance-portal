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

export function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const visibleItems = items.filter((item) => user && item.roles.includes(user.role));

  return <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col border-r border-slate-200 bg-white lg:flex">
    <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-6"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white">LM</div><div><p className="text-sm font-bold text-slate-900">Legal Metrology</p><p className="text-xs text-slate-500">Compliance Portal</p></div></div>
    <nav className="flex-1 space-y-1 px-4 py-6">{visibleItems.map(({ name, to, icon: Icon }) => { const href = name === "Dashboard" && user?.role === "admin" ? "/admin/dashboard" : to; return <NavLink key={name} to={href} className={({isActive}) => `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"}`}><Icon className="h-5 w-5" />{name}</NavLink>; })}</nav>
    <div className="m-4 space-y-3">
      <button
        type="button"
        onClick={handleLogout}
        className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-rose-700 transition hover:bg-rose-50"
      >
        <LogOut className="h-5 w-5" />
        Log out
      </button>
    </div>
  </aside>;
}
