import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Clock3,
  MapPin,
  ScanLine,
} from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../components/common/StatusBadge";
import { useAuthStore } from "../stores/authStores";
import { fetchAnalyticsStats, fetchInspectionHistory } from "../services/apiClient";

export function OfficerDashboardPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<any>(null);
  const [recentInspections, setRecentInspections] = useState<any[]>([]);

  useEffect(() => {
    fetchAnalyticsStats().then(setStats).catch(() => {});
    fetchInspectionHistory().then(setRecentInspections).catch(() => {});
  }, []);

  const metrics = [
    {
      label: "Total Package Scans",
      value: stats?.total_inspections ? String(stats.total_inspections) : "18",
      description: "Current audit workload",
      icon: ClipboardList,
      color: "bg-blue-50 text-blue-600",
    },
    {
      label: "Compliant Clearances",
      value: stats?.compliant_count !== undefined ? String(stats.compliant_count) : "12",
      description: "Statutory 100% pass",
      icon: CheckCircle2,
      color: "bg-emerald-50 text-emerald-600",
    },
    {
      label: "Compliance Pass Rate",
      value: stats?.pass_rate !== undefined ? `${stats.pass_rate}%` : "79%",
      description: "Overall audit score",
      icon: ScanLine,
      color: "bg-amber-50 text-amber-600",
    },
    {
      label: "Non-Compliant Defective",
      value: stats?.non_compliant_count !== undefined ? String(stats.non_compliant_count) : "6",
      description: "Show-Cause Notices issued",
      icon: AlertTriangle,
      color: "bg-rose-50 text-rose-600",
    },
  ];

  return (
    <div className="space-y-7">
      <section className="rounded-2xl bg-linear-to-r from-blue-700 to-indigo-700 p-6 text-white sm:p-8">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div>
            <p className="text-sm font-medium text-blue-100">
              Enforcement Officer Dashboard
            </p>

            <h1 className="mt-2 text-3xl font-bold">
              Welcome, {user?.name ?? "Officer"}
            </h1>

            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-blue-100">
              <span>Officer ID: {user?.officerId ?? "LM-WB-2026-0148"}</span>

              <span className="inline-flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {user?.jurisdiction ?? "Kolkata North Division"}
              </span>
            </div>
          </div>

          <Link
            to="/inspections/new"
            className="rounded-xl bg-white px-4 py-3 text-center text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
          >
            Start new inspection
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <article key={metric.label} className="app-card p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">
                    {metric.label}
                  </p>

                  <p className="mt-2 text-3xl font-bold text-slate-900">
                    {metric.value}
                  </p>
                </div>

                <div className={`rounded-xl p-3 ${metric.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>

              <p className="mt-4 text-xs text-slate-500">
                {metric.description}
              </p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-3">
        <div className="app-card overflow-hidden xl:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <div>
              <h2 className="font-semibold text-slate-900">
                My recent inspections
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Inspections assigned to your account.
              </p>
            </div>

            <Link
              to="/my-inspections"
              className="text-sm font-semibold text-blue-600 hover:text-blue-700"
            >
              View all
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left">
              <thead className="bg-slate-50 dark:bg-slate-800 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="px-6 py-4">Inspection</th>
                  <th className="px-6 py-4">Product</th>
                  <th className="px-6 py-4">Location</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {(recentInspections && recentInspections.length > 0 ? recentInspections : [
                  {
                    inspection_id: "INS-2026-8801",
                    product_name: "Herbal Shampoo 180 ml",
                    company_name: "GreenCare Pvt. Ltd.",
                    timestamp: "2026-09-11",
                    is_compliant: false
                  },
                  {
                    inspection_id: "INS-2026-8802",
                    product_name: "NutriBite Whole Wheat Biscuits",
                    company_name: "NutriBite Foods",
                    timestamp: "2026-09-10",
                    is_compliant: true
                  }
                ]).map((inspection, idx) => (
                  <tr key={inspection.inspection_id || idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-6 py-4 text-sm font-semibold text-blue-600 dark:text-blue-400 font-mono">
                      {inspection.inspection_id || `INS-2026-880${idx + 1}`}
                    </td>

                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                        {inspection.entity_info?.commodity_name || inspection.product_name || "Pre-Packaged Goods"}
                      </p>

                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        {inspection.timestamp ? new Date(inspection.timestamp).toLocaleDateString() : "Recent"}
                      </p>
                    </td>

                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                      {inspection.entity_info?.manufacturer_name_address || inspection.company_name || "Northern Zone"}
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-bold ${
                          inspection.is_compliant
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {inspection.is_compliant ? "Compliant" : "Non-Compliant"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="app-card p-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-amber-50 p-3 text-amber-700">
              <Clock3 className="h-5 w-5" />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900">
                Pending actions
              </h2>

              <p className="text-sm text-slate-500">
                Complete these reviews.
              </p>
            </div>
          </div>

          <div className="mt-5 space-y-4">
            <div className="rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-950/40 p-4">
              <p className="text-sm font-bold text-amber-900 dark:text-amber-300">
                Pending Inspection Review
              </p>

              <p className="mt-1 text-xs leading-5 text-amber-800 dark:text-amber-400">
                Verify mandatory consumer care contact number & tax disclosure.
              </p>

              <Link
                to="/inspections/demo/review"
                className="mt-3 inline-flex items-center gap-1 text-xs font-extrabold text-amber-800 hover:text-amber-950 dark:text-amber-300 dark:hover:text-white"
              >
                Review Inspection &rarr;
              </Link>
            </div>

            <div className="rounded-xl border border-blue-200 bg-blue-50 dark:bg-blue-950/40 p-4">
              <p className="text-sm font-bold text-blue-900 dark:text-blue-300">
                New Inspection Assignment
              </p>

              <p className="mt-1 text-xs leading-5 text-blue-800 dark:text-blue-400">
                Start new pre-packaged commodity AI scan in your jurisdiction.
              </p>

              <Link
                to="/inspections/new"
                className="mt-3 inline-flex items-center gap-1 text-xs font-extrabold text-blue-800 hover:text-blue-950 dark:text-blue-300 dark:hover:text-white"
              >
                Start New Scan &rarr;
              </Link>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}