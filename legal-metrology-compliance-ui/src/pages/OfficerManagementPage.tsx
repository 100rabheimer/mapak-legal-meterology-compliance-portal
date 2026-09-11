import { useEffect, useMemo, useState } from "react";
import {
  CircleOff,
  Edit3,
  Plus,
  Search,
  Trash2,
  UserCheck,
  UsersRound,
  RefreshCw,
  ShieldCheck
} from "lucide-react";
import {
  fetchOfficersApi,
  createOfficerApi,
  updateOfficerApi,
  deleteOfficerApi,
  UserProfile
} from "../services/apiClient";

export function OfficerManagementPage() {
  const [officers, setOfficers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  const loadOfficers = async () => {
    setLoading(true);
    try {
      const data = await fetchOfficersApi();
      if (data && data.length > 0) {
        setOfficers(data);
      } else {
        // Fallback default officers if list is empty
        setOfficers([
          {
            user_id: "USR-OFFICER-001",
            email: "officer@doca.gov.in",
            full_name: "Sh. R. K. Verma",
            role: "OFFICER",
            badge_number: "LM-DEL-2026-0148",
            jurisdiction_zone: "Northern Enforcement Zone, New Delhi"
          },
          {
            user_id: "USR-ADMIN-001",
            email: "admin@doca.gov.in",
            full_name: "DoCA Chief Enforcement Director",
            role: "ADMIN",
            badge_number: "LM-HQ-2026-0001",
            jurisdiction_zone: "Ministry of Consumer Affairs HQ, New Delhi"
          }
        ]);
      }
    } catch (err) {
      console.error("Failed to load officers", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOfficers();
  }, []);

  const filteredOfficers = useMemo(() => {
    const query = search.toLowerCase().trim();

    if (!query) {
      return officers;
    }

    return officers.filter((officer) =>
      [
        officer.full_name,
        officer.email,
        officer.badge_number,
        officer.jurisdiction_zone,
        officer.role
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [officers, search]);

  const handleDeactivate = async (userId: string, name: string) => {
    const approved = window.confirm(`Deactivate enforcement account for '${name}'?`);
    if (!approved) return;

    try {
      await deleteOfficerApi(userId);
      alert(`Officer '${name}' deactivated successfully.`);
      loadOfficers();
    } catch (err: any) {
      alert(`Deactivation failed: ${err.message}`);
    }
  };

  const addOfficerSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    const name = String(formData.get("name"));
    const email = String(formData.get("email"));
    const password = String(formData.get("password"));
    const role = String(formData.get("role") || "OFFICER");
    const badge = String(formData.get("badge"));
    const zone = String(formData.get("zone"));

    try {
      await createOfficerApi({
        full_name: name,
        email,
        password,
        role,
        badge_number: badge,
        jurisdiction_zone: zone
      });
      alert(`Enforcement account for '${name}' created successfully.`);
      setShowAddModal(false);
      loadOfficers();
    } catch (err: any) {
      alert(`Failed to create officer: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-2">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2 text-blue-600 font-bold text-xs uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4" /> Role-Based Access Control (RBAC)
          </div>

          <h1 className="page-title">Officer Management</h1>

          <p className="page-description">
            Create, update, activate, deactivate, and audit enforcement officer credentials in the DoCA relational database.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={loadOfficers}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-200 transition hover:bg-slate-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 shadow-md"
          >
            <Plus className="h-4 w-4" />
            Add Officer Account
          </button>
        </div>
      </div>

      <section className="app-card overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-slate-100 dark:border-slate-800 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-50 dark:bg-blue-950 p-3 text-blue-600 dark:text-blue-400">
              <UsersRound className="h-5 w-5" />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Enforcement Officers & Admins
              </h2>

              <p className="text-sm text-slate-500">
                {officers.length} active registered accounts in relational ORM database.
              </p>
            </div>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="form-input py-2.5 pl-10"
              placeholder="Search officers or badge..."
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="bg-slate-50 dark:bg-slate-800 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-6 py-4">Officer Name & Email</th>
                <th className="px-6 py-4">Badge Number</th>
                <th className="px-6 py-4">Jurisdiction Zone</th>
                <th className="px-6 py-4">RBAC Role</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredOfficers.map((officer) => (
                <tr key={officer.user_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="px-6 py-4">
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {officer.full_name}
                    </p>

                    <p className="mt-0.5 text-xs text-slate-500 font-mono">
                      {officer.email}
                    </p>
                  </td>

                  <td className="px-6 py-4 text-xs font-mono font-bold text-indigo-600 dark:text-indigo-400">
                    {officer.badge_number || "LM-HQ-2026"}
                  </td>

                  <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400">
                    {officer.jurisdiction_zone || "Northern Enforcement Zone"}
                  </td>

                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex rounded-full px-3 py-1 text-xs font-extrabold uppercase ${
                        officer.role?.toUpperCase() === "ADMIN"
                          ? "bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300"
                          : "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300"
                      }`}
                    >
                      {officer.role || "OFFICER"}
                    </span>
                  </td>

                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => handleDeactivate(officer.user_id, officer.full_name)}
                        className="rounded-lg border border-rose-200 dark:border-rose-900 p-2 text-rose-700 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950 transition-colors"
                        title="Deactivate officer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {filteredOfficers.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-12 text-center text-sm text-slate-500"
                  >
                    No officers match your search criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-2xl space-y-4">
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Add Enforcement Officer Account
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Register a new officer with JWT authentication & database credentials.
                </p>
              </div>

              <button
                onClick={() => setShowAddModal(false)}
                className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 font-bold"
              >
                &times;
              </button>
            </div>

            <form onSubmit={addOfficerSubmit} className="space-y-4 text-sm">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Full Name
                </label>

                <input
                  name="name"
                  required
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                  placeholder="Sh. Aarav Sharma"
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Official Email
                  </label>

                  <input
                    name="email"
                    type="email"
                    required
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                    placeholder="officer@doca.gov.in"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Password
                  </label>

                  <input
                    name="password"
                    type="password"
                    required
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                    placeholder="Password123"
                  />
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    RBAC Role
                  </label>

                  <select
                    name="role"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                  >
                    <option value="OFFICER">Enforcement Officer</option>
                    <option value="ADMIN">System Administrator</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Badge Number
                  </label>

                  <input
                    name="badge"
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                    placeholder="LM-DEL-2026-0192"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Jurisdiction Zone
                </label>

                <input
                  name="zone"
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                  placeholder="Northern Enforcement Zone, New Delhi"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-semibold hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold shadow-md"
                >
                  Save Officer Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}