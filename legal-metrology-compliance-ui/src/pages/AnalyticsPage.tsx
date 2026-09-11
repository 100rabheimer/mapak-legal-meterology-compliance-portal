import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  MapPin,
  UserRound,
  RefreshCw,
  TrendingUp,
  ShieldAlert,
  Building,
  Package,
  FileCheck,
  Activity,
  Layers
} from "lucide-react";
import { fetchAnalyticsStats, fetchInspectionHistory, fetchOfficersApi, UserProfile } from "../services/apiClient";

export function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [inspections, setInspections] = useState<any[]>([]);
  const [officers, setOfficers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadAnalytics = async () => {
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
      console.error("Failed to load real-time analytics", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const totalInspections = stats?.total_inspections ?? inspections.length;
  const compliantCount = stats?.compliant_count ?? inspections.filter((i) => i.is_compliant).length;
  const nonCompliantCount = stats?.non_compliant_count ?? (totalInspections - compliantCount);
  const passRate = totalInspections > 0 ? ((compliantCount / totalInspections) * 100).toFixed(1) : "100.0";
  const issueRate = totalInspections > 0 ? ((nonCompliantCount / totalInspections) * 100).toFixed(1) : "0.0";

  // Compute commodity issue aggregation dynamically
  const productIssueMap: Record<string, { product: string; issues: number; company: string; category: string }> = {};
  inspections.forEach((item) => {
    const pName = item.entity_info?.commodity_name || item.product_name || "Pre-Packaged Goods";
    const cName = item.entity_info?.manufacturer_name_address || item.company_name || "Enterprise Ltd.";
    const cat = item.category || "UNIVERSAL";
    if (!productIssueMap[pName]) {
      productIssueMap[pName] = { product: pName, issues: 0, company: cName, category: cat };
    }
    if (!item.is_compliant) {
      productIssueMap[pName].issues += 1;
    }
  });

  const issueProductsList = Object.values(productIssueMap)
    .sort((a, b) => b.issues - a.issues)
    .slice(0, 5);

  const topViolations = stats?.top_violations || [];

  return (
    <div className="p-2 max-w-7xl mx-auto space-y-6">
      {/* Premium Dark Hero Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-8 border border-indigo-500/20 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 font-bold tracking-wider text-xs uppercase mb-2">
              <Activity className="w-4 h-4 animate-pulse" /> Department of Consumer Affairs Telemetry Engine
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Real-Time Inspection & Violation Analytics
            </h1>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              Live enforcement telemetry, statutory rule defect frequencies, and regional officer workloads powered by the DoCA relational ORM engine.
            </p>
          </div>
          <button
            onClick={loadAnalytics}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Modern High-Contrast Metric Cards */}
      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Scans Executed</span>
            <div className="p-3 bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 rounded-xl">
              <BarChart3 className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900 dark:text-white mt-4">
            {loading ? "..." : totalInspections}
          </p>
          <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-semibold mt-2">
            <TrendingUp className="w-3.5 h-3.5" /> Synchronized with ORM DB
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Compliant Packages</span>
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 rounded-xl">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-4">
            {loading ? "..." : compliantCount}
          </p>
          <div className="flex items-center justify-between text-xs mt-2">
            <span className="text-slate-500 font-medium">Compliance Rate:</span>
            <span className="font-extrabold text-emerald-600 dark:text-emerald-400">{passRate}%</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Statutory Defective</span>
            <div className="p-3 bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 rounded-xl">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-rose-600 dark:text-rose-400 mt-4">
            {loading ? "..." : nonCompliantCount}
          </p>
          <div className="flex items-center justify-between text-xs mt-2">
            <span className="text-slate-500 font-medium">Defect Rate:</span>
            <span className="font-extrabold text-rose-600 dark:text-rose-400">{issueRate}%</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Jurisdiction Zone</span>
            <div className="p-3 bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 rounded-xl">
              <MapPin className="w-5 h-5" />
            </div>
          </div>
          <p className="text-sm font-bold text-slate-900 dark:text-white mt-4 truncate">
            {stats?.zone || "Northern Enforcement Zone"}
          </p>
          <p className="text-xs text-slate-500 mt-1">Inspector: {stats?.active_officer || "Sh. R. K. Verma"}</p>
        </div>
      </section>

      {/* Detailed Analytics Grid */}
      <section className="grid gap-6 xl:grid-cols-2">
        {/* Top Statutory Violations Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-500" />
                Statutory Defect Frequency
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">Top Rule 6(1), Rule 7, & Rule 11 non-compliance provisions.</p>
            </div>
          </div>

          <div className="space-y-4">
            {topViolations.length > 0 ? (
              topViolations.map((v: any, idx: number) => {
                const pct = totalInspections > 0 ? Math.min(100, Math.round((v.count / totalInspections) * 100)) : 0;
                return (
                  <div key={idx} className="space-y-1.5 bg-slate-50 dark:bg-slate-800/50 p-3.5 rounded-xl border border-slate-100 dark:border-slate-800">
                    <div className="flex justify-between text-xs font-bold text-slate-800 dark:text-slate-200">
                      <span>{v.title}</span>
                      <span className="text-rose-600 dark:text-rose-400 font-mono">{v.count} Cases ({pct}%)</span>
                    </div>
                    <div className="h-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-2 bg-gradient-to-r from-rose-500 to-amber-500 rounded-full transition-all duration-500"
                        style={{ width: `${Math.max(8, pct)}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No statutory defects recorded in database yet. Execute scans from the top menu to populate live telemetry.
              </div>
            )}
          </div>
        </div>

        {/* Commodity Issue Aggregator */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Package className="w-5 h-5 text-indigo-500" />
                Scanned Commodity Defects
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">Pre-packaged items triggering statutory non-compliance.</p>
            </div>
          </div>

          <div className="space-y-3">
            {issueProductsList.length > 0 ? (
              issueProductsList.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold text-[10px] rounded">
                        {item.category}
                      </span>
                      <p className="text-sm font-bold text-slate-900 dark:text-white">{item.product}</p>
                    </div>
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                      <Building className="w-3 h-3" /> {item.company}
                    </p>
                  </div>
                  <span className={`text-xs font-extrabold px-3 py-1 rounded-full ${
                    item.issues > 0 ? "bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300" : "bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300"
                  }`}>
                    {item.issues > 0 ? `${item.issues} Defect Cases` : "100% Compliant"}
                  </span>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No commodity defect flags recorded in database.
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Enforcement Officer RBAC Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="border-b border-slate-100 dark:border-slate-800 px-6 py-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <UserRound className="w-5 h-5 text-purple-500" />
              Registered Enforcement Officer Roster
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Live active accounts registered in relational ORM database.</p>
          </div>
          <span className="text-xs font-bold text-slate-400">{officers.length} Registered Accounts</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <th className="p-4">Officer Name & Email</th>
                <th className="p-4">Badge Number</th>
                <th className="p-4">Jurisdiction Zone</th>
                <th className="p-4 text-right">RBAC Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-sm">
              {officers.map((officer) => (
                <tr key={officer.user_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <td className="p-4">
                    <p className="font-bold text-slate-900 dark:text-white">{officer.full_name}</p>
                    <p className="text-xs text-slate-500 font-mono mt-0.5">{officer.email}</p>
                  </td>

                  <td className="p-4 font-mono font-bold text-xs text-indigo-600 dark:text-indigo-400">
                    {officer.badge_number || "LM-DEL-2026"}
                  </td>

                  <td className="p-4 text-xs text-slate-600 dark:text-slate-400">
                    {officer.jurisdiction_zone || "Northern Enforcement Zone"}
                  </td>

                  <td className="p-4 text-right">
                    <span className="px-2.5 py-1 bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 font-extrabold text-xs rounded-full uppercase">
                      {officer.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
