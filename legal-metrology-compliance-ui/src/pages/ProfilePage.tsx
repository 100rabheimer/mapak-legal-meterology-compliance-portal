import { LogOut, Mail, MapPin, ShieldCheck, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStores";

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  if (!user) {
    return null;
  }

  const roleLabel = user.role === "admin" ? "Administrator" : "Enforcement Officer";

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <p className="text-sm font-semibold text-blue-600">Account settings</p>
        <h1 className="page-title">My profile</h1>
        <p className="page-description">
          View the account details and access level associated with your sign-in.
        </p>
      </div>

      <section className="app-card overflow-hidden">
        <div className="flex items-center gap-4 border-b border-slate-100 px-6 py-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-xl font-bold text-blue-700">
            {user.name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{user.name}</h2>
            <p className="mt-1 text-sm text-slate-500">{roleLabel}</p>
          </div>
        </div>

        <dl className="grid gap-5 px-6 py-6 sm:grid-cols-2">
          <div className="flex items-start gap-3">
            <Mail className="mt-0.5 h-5 w-5 text-slate-400" />
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</dt>
              <dd className="mt-1 text-sm font-medium text-slate-800">{user.email}</dd>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 text-slate-400" />
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role</dt>
              <dd className="mt-1 text-sm font-medium text-slate-800">{roleLabel}</dd>
            </div>
          </div>

          {user.role === "officer" && (
            <>
              <div className="flex items-start gap-3">
                <UserRound className="mt-0.5 h-5 w-5 text-slate-400" />
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Officer ID</dt>
                  <dd className="mt-1 text-sm font-medium text-slate-800">{user.officerId}</dd>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="mt-0.5 h-5 w-5 text-slate-400" />
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Jurisdiction</dt>
                  <dd className="mt-1 text-sm font-medium text-slate-800">{user.jurisdiction}</dd>
                </div>
              </div>
            </>
          )}
        </dl>

        <div className="border-t border-slate-100 px-6 py-5">
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex items-center gap-2 rounded-xl border border-rose-200 px-4 py-2.5 text-sm font-semibold text-rose-700 transition hover:bg-rose-50"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </section>
    </div>
  );
}
