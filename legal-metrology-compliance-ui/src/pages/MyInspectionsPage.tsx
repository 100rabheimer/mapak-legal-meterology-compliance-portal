import React, { useEffect, useState } from "react";
import { fetchInspectionHistory, ApiInspectionReport, triggerPdfDownload } from "../services/apiClient";
import {
  FileCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Download,
  Building,
  Package,
  Eye,
  AlertTriangle,
  RefreshCw
} from "lucide-react";

export const MyInspectionsPage: React.FC = () => {
  const [inspections, setInspections] = useState<ApiInspectionReport[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [selectedInspection, setSelectedInspection] = useState<ApiInspectionReport | null>(null);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await fetchInspectionHistory();
      setInspections(data);
    } catch (err) {
      console.error("Failed to load inspection history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const filteredInspections = inspections.filter((item) => {
    const productName = item.entity_info?.commodity_name || (item as any).product_name || "";
    const companyName = item.entity_info?.manufacturer_name_address || (item as any).company_name || "";
    const inspId = item.inspection_id || "";

    const matchesSearch =
      productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inspId.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "COMPLIANT" && item.is_compliant) ||
      (statusFilter === "NON_COMPLIANT" && !item.is_compliant);

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white rounded-2xl p-8 border border-slate-700/50 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 font-semibold tracking-wider text-xs uppercase mb-2">
              <FileCheck className="w-4 h-4" /> Official Enforcement Audit Log
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              My Enforcement Inspections
            </h1>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              Audit table of statutory package inspections executed by your enforcement badge, stored securely in the DoCA relational database.
            </p>
          </div>
          <button
            onClick={loadHistory}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Log
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search product, manufacturer, or inspection ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
          >
            <option value="ALL">All Inspections ({inspections.length})</option>
            <option value="COMPLIANT">Compliant Only</option>
            <option value="NON_COMPLIANT">Non-Compliant Only</option>
          </select>
        </div>
      </div>

      {/* Inspections Table */}
      {loading ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-8 space-y-4 animate-pulse border border-slate-200 dark:border-slate-800">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-12 bg-slate-100 dark:bg-slate-800 rounded-lg" />
          ))}
        </div>
      ) : filteredInspections.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-12 text-center border border-slate-200 dark:border-slate-800">
          <Package className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">No Inspections Recorded</h3>
          <p className="text-sm text-slate-500 mt-1">Execute a new packaging scan from the top navigation to populate your enforcement history.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <th className="p-4">Case ID & Timestamp</th>
                  <th className="p-4">Commodity / Manufacturer</th>
                  <th className="p-4">Category</th>
                  <th className="p-4">Compliance Status</th>
                  <th className="p-4">Score</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-sm">
                {filteredInspections.map((item, idx) => {
                  const inspId = item.inspection_id || `INS-2026-00${idx + 1}`;
                  const productName = item.entity_info?.commodity_name || (item as any).product_name || "Pre-Packaged Goods";
                  const companyName = item.entity_info?.manufacturer_name_address || (item as any).company_name || "Offending Enterprise";
                  const noticeUrl = item.notice?.notice_url || (item as any).notice_url || "http://localhost:8000/api/download_latest_notice";

                  return (
                    <tr key={inspId} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                      <td className="p-4">
                        <div className="font-mono font-bold text-indigo-600 dark:text-indigo-400 text-xs">
                          {inspId}
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {item.timestamp ? new Date(item.timestamp).toLocaleString() : "Recent"}
                        </div>
                      </td>

                      <td className="p-4">
                        <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                          <Package className="w-4 h-4 text-slate-400" />
                          {productName}
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                          <Building className="w-3 h-3" />
                          {companyName}
                        </div>
                      </td>

                      <td className="p-4 text-xs font-semibold text-slate-600 dark:text-slate-400">
                        <span className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded-md">
                          {item.category || "UNIVERSAL"}
                        </span>
                      </td>

                      <td className="p-4">
                        {item.is_compliant ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-bold text-xs rounded-full">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Compliant
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 font-bold text-xs rounded-full">
                            <XCircle className="w-3.5 h-3.5" /> Non-Compliant ({item.violations?.length || (item as any).violations_count || 1} Violations)
                          </span>
                        )}
                      </td>

                      <td className="p-4">
                        <div className="font-extrabold text-slate-900 dark:text-white text-base">
                          {item.compliance_score || 85}%
                        </div>
                      </td>

                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => setSelectedInspection(item)}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs rounded-lg transition-colors inline-flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" /> View Details
                        </button>

                        <button
                          onClick={() => triggerPdfDownload(noticeUrl)}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition-colors inline-flex items-center gap-1 shadow-sm active:scale-95 cursor-pointer"
                        >
                          <Download className="w-3.5 h-3.5" /> Legal Notice PDF
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detailed Inspection Modal */}
      {selectedInspection && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                  {selectedInspection.inspection_id}
                </span>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {selectedInspection.entity_info?.commodity_name || (selectedInspection as any).product_name || "Inspection Details"}
                </h2>
                <p className="text-xs text-slate-500">
                  {selectedInspection.entity_info?.manufacturer_name_address || (selectedInspection as any).company_name}
                </p>
              </div>
              <button
                onClick={() => setSelectedInspection(null)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold p-1"
              >
                &times;
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 bg-slate-50 dark:bg-slate-800/60 p-4 rounded-xl">
                <div>
                  <div className="text-xs text-slate-400 font-semibold">Compliance Status</div>
                  <div className="font-bold text-sm mt-0.5">
                    {selectedInspection.is_compliant ? "✅ 100% Compliant" : "❌ Non-Compliant"}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 font-semibold">Score</div>
                  <div className="font-bold text-sm mt-0.5">{selectedInspection.compliance_score}%</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 font-semibold">Category</div>
                  <div className="font-bold text-sm mt-0.5">{selectedInspection.category || "UNIVERSAL"}</div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Detected Statutory Violations</h4>
                {selectedInspection.violations && selectedInspection.violations.length > 0 ? (
                  <div className="space-y-2">
                    {selectedInspection.violations.map((v, i) => (
                      <div key={i} className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl">
                        <div className="flex justify-between font-bold text-rose-800 dark:text-rose-300 text-sm">
                          <span>{v.title}</span>
                          <span className="font-mono text-xs uppercase">{v.severity}</span>
                        </div>
                        <p className="text-xs text-rose-700 dark:text-rose-400 mt-1">{v.description}</p>
                        {v.remedy && <div className="text-xs font-semibold text-rose-900 dark:text-rose-200 mt-1">Remedy: {v.remedy}</div>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 text-sm rounded-xl font-semibold">
                    No statutory violations detected on packaging surface.
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <button
                onClick={() => triggerPdfDownload(selectedInspection.notice?.notice_url)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-md active:scale-95 cursor-pointer"
              >
                <Download className="w-4 h-4" /> Download Official Notice PDF
              </button>
              <button
                onClick={() => setSelectedInspection(null)}
                className="px-5 py-2 bg-slate-800 text-white rounded-xl text-sm font-medium hover:bg-slate-700"
              >
                Close Case
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
