import { Bell, LogOut, Menu } from "lucide-react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { useAuthStore } from "../../stores/authStores";

export function AppLayout() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const initials = user?.name.slice(0, 2).toUpperCase() ?? "LM";

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <div className="min-h-screen lg:pl-72">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6">
          <button className="rounded-lg p-2 text-slate-600 lg:hidden" aria-label="Open navigation"><Menu className="h-5 w-5" /></button>
          <div className="ml-auto flex items-center gap-3">
            <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" aria-label="Notifications"><Bell className="h-5 w-5" /></button>
            <Link to="/settings" className="flex items-center gap-2 border-l border-slate-200 pl-3" aria-label="Open profile settings">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">{initials}</div>
              <div className="hidden sm:block"><p className="text-sm font-semibold text-slate-800">{user?.name}</p><p className="text-xs capitalize text-slate-500">{user?.role}</p></div>
            </Link>
            <button type="button" onClick={handleLogout} className="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-700" aria-label="Log out"><LogOut className="h-5 w-5" /></button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8"><Outlet /></main>
      </div>
    </div>
  );
}
