import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  MapPin,
  PackageSearch,
  ShieldCheck,
  UserCog,
  UsersRound,
  RefreshCw,
  Building
} from "lucide-react";
import { Link } from "react-router-dom";
import { fetchAnalyticsStats, fetchInspectionHistory, fetchOfficersApi, UserProfile } from "../services/apiClient";

export function AdminDashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [inspections, setInspections] = useState<any[]>([]);
  const [officers, setOfficers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [statsData, historyData, officerData] = await Promise.all([
        fetchAnalyticsStats(),
        fetchInspectionHistory(),
        fetchOfficersApi()
      ]);
      setStats(statsData);
      setInspections(historyData);
      setOfficers(officerData);
    } catch (err) {
      console.error("Failed to load admin telemetry", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const totalOfficers = officers.length;
  const totalInspections = stats?.total_inspections ?? inspections.length;
  const compliantCount = stats?.compliant_count ?? inspections.filter((i) => i.is_compliant).length;
  const nonCompliantCount = stats?.non_compliant_count ?? (totalInspections - compliantCount);
  const passRate = totalInspections > 0 ? ((compliantCount / totalInspections) * 100).toFixed(1) : "100.0";

  const topViolations = stats?.top_violations || [];

  // Group inspections by product
  const productMap: Record<string, { name: string; issues: number; company: string }> = {};
  inspections.forEach((item) => {
    const pName = item.entity_info?.commodity_name || item.product_name || "Pre-Packaged Goods";
    const cName = item.entity_info?.manufacturer_name_address || item.company_name || "Enterprise";
    if (!productMap[pName]) {
      productMap[pName] = { name: pName, issues: 0, company: cName };
    }
    if (!item.is_compliant) {
      productMap[pName].issues += 1;
    }
  });

  const issueProductsList = Object.values(productMap).sort((a, b) => b.issues - a.issues).slice(0, 4);

  return (
    <div className="space-y-7 max-w-7xl mx-auto">
      <div className="relative overflow-hidden rounded-2xl bg-linear-to-r from-blue-600 to-indigo-700 p-8 text-white shadow-lg">
        <div className="relative z-10 flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div className="max-w-2xl">
            <p className="text-xs font-extrabold uppercase tracking-wider text-blue-200">
              Administrator Enforcement Control Center
            </p>

            <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">System Administration Dashboard</h1>

            <p className="mt-3 text-sm leading-relaxed text-blue-100 sm:text-base">
              Manage officer accounts, monitor field inspection workloads, and audit statutory compliance telemetry.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={loadAdminData}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-semibold text-white backdrop-blur-md transition hover:bg-white/20"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>

            <Link
              to="/admin/officers"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-blue-700 transition hover:bg-blue-50 shadow-sm"
            >
              <UserCog className="h-4 w-4" />
              Manage Officers
            </Link>
          </div>
        </div>
        
        {/* Decorative background pattern */}
        <div className="absolute -right-20 -top-20 z-0 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-32 -left-20 z-0 h-80 w-80 rounded-full bg-indigo-500/20 blur-3xl" />
      </div>

      {/* Real-Time Metric Cards */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article className="app-card p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Active Officers</p>
              <p className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-white">
                {loading ? "..." : totalOfficers}
              </p>
            </div>
            <div className="rounded-xl p-3 bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400">
              <UsersRound className="h-5 w-5" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">Registered in relational database</p>
        </article>

        <article className="app-card p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Package Scans</p>
              <p className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-white">
                {loading ? "..." : totalInspections}
              </p>
            </div>
            <div className="rounded-xl p-3 bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <ClipboardList className="h-5 w-5" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">Across all enforcement zones</p>
        </article>

        <article className="app-card p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Compliance Rate</p>
              <p className="mt-2 text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                {loading ? "..." : `${passRate}%`}
              </p>
            </div>
            <div className="rounded-xl p-3 bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">{compliantCount} products statutorily compliant</p>
        </article>

        <article className="app-card p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Open Violations</p>
              <p className="mt-2 text-3xl font-extrabold text-rose-600 dark:text-rose-400">
                {loading ? "..." : nonCompliantCount}
              </p>
            </div>
            <div className="rounded-xl p-3 bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </div>
          <p className="mt-4 text-xs text-slate-500">Show-Cause Notices issued</p>
        </article>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        {/* Products with Most Issues */}
        <article className="app-card overflow-hidden">
          <div className="border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <h2 className="font-semibold text-slate-900 dark:text-white">Commodity Flagged Telemetry</h2>
            <p className="mt-1 text-xs text-slate-500">Recurring defect findings reported by field officers.</p>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {issueProductsList.length > 0 ? (
              issueProductsList.map((product, idx) => (
                <div key={idx} className="flex items-center justify-between gap-4 px-6 py-4">
                  <div className="flex items-center gap-3">
                    <PackageSearch className="h-5 w-5 text-rose-500 shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{product.name}</p>
                      <p className="mt-0.5 text-xs text-slate-500 flex items-center gap-1">
                        <Building className="w-3 h-3" /> {product.company}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-extrabold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950 px-2.5 py-1 rounded-full">
                    {product.issues} defect{product.issues !== 1 ? "s" : ""}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No commodity defects recorded in database.
              </div>
            )}
          </div>
        </article>

        {/* Top Statutory Violations */}
        <article className="app-card overflow-hidden">
          <div className="border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <h2 className="font-semibold text-slate-900 dark:text-white">Statutory Defect Hotspots</h2>
            <p className="mt-1 text-xs text-slate-500">Most frequent non-compliance provisions.</p>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {topViolations.length > 0 ? (
              topViolations.map((v: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between gap-4 px-6 py-4">
                  <div className="flex items-center gap-3">
                    <MapPin className="h-5 w-5 text-amber-600 shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{v.title}</p>
                      <p className="mt-0.5 text-xs text-slate-500">Legal Metrology Act, 2009 & PCR 2011</p>
                    </div>
                  </div>
                  <span className="text-xs font-extrabold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 px-2.5 py-1 rounded-full">
                    {v.count} Count{v.count !== 1 ? "s" : ""}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No statutory violation hotspots recorded.
              </div>
            )}
          </div>
        </article>
      </section>

      {/* Real-time Officers Table */}
      <section className="app-card overflow-hidden">
        <div className="flex flex-col justify-between gap-3 border-b border-slate-100 dark:border-slate-800 px-6 py-5 sm:flex-row sm:items-center">
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-white">
              Enforcement Officer Roster & Jurisdictions
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Real-time active accounts registered in relational ORM database.
            </p>
          </div>

          <Link
            to="/admin/officers"
            className="text-xs font-extrabold text-blue-600 hover:text-blue-700"
          >
            Manage Accounts &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="bg-slate-50 dark:bg-slate-800 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              <tr>
                <th className="px-6 py-4">Officer Name & Email</th>
                <th className="px-6 py-4">Badge Number</th>
                <th className="px-6 py-4">Jurisdiction Zone</th>
                <th className="px-6 py-4">RBAC Role</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
              {officers.map((officer) => (
                <tr key={officer.user_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="px-6 py-4">
                    <p className="font-semibold text-slate-900 dark:text-white">
                      {officer.full_name}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500 font-mono">
                      {officer.email}
                    </p>
                  </td>

                  <td className="px-6 py-4 font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                    {officer.badge_number || "LM-DEL-2026"}
                  </td>

                  <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400">
                    {officer.jurisdiction_zone || "Northern Enforcement Zone"}
                  </td>

                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-bold text-xs rounded-full uppercase">
                      {officer.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-2xl border border-blue-100 dark:border-blue-900/40 bg-blue-50/60 dark:bg-blue-950/40 p-6">
        <div className="flex gap-4">
          <div className="rounded-xl bg-white dark:bg-slate-800 p-3 text-blue-600 shadow-xs shrink-0">
            <ShieldCheck className="h-6 w-6" />
          </div>

          <div>
            <h2 className="font-bold text-slate-900 dark:text-white text-sm">
              Statutory Administrative Responsibility & Audit Trail
            </h2>

            <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
              Administrative operations including registering officers, updating jurisdiction zones, and deactivating officer credentials are automatically audited in the relational database audit trail under Section 15 of Legal Metrology Act, 2009.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}