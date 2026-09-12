import React, { useEffect, useState } from "react";
import { fetchInspectionHistory, ApiInspectionReport } from "../services/apiClient";
import {
  PackageSearch,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Building2,
  Calendar,
  Layers,
  Scale,
  RefreshCw,
  Eye
} from "lucide-react";

export const ProductsPage: React.FC = () => {
  const [inspections, setInspections] = useState<ApiInspectionReport[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");

  const loadData = async () => {
    setLoading(true);
    try {
      const history = await fetchInspectionHistory();
      setInspections(history);
    } catch (err) {
      console.error("Failed to load products", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const categories = Array.from(new Set(inspections.map((i) => i.category || "UNIVERSAL")));

  const filtered = inspections.filter((item) => {
    const pName = item.entity_info?.commodity_name || (item as any).product_name || "";
    const cName = item.entity_info?.manufacturer_name_address || (item as any).company_name || "";
    const matchesSearch =
      pName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cName.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      categoryFilter === "ALL" || (item.category && item.category.toUpperCase() === categoryFilter.toUpperCase());

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950 to-slate-900 text-white rounded-2xl p-8 border border-sky-500/20 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 text-sky-400 font-semibold tracking-wider text-xs uppercase mb-2">
              <PackageSearch className="w-4 h-4" /> Legal Metrology Product Catalog
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Scanned Pre-Packaged Commodity Repository
            </h1>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              Central database of pre-packaged commodities scanned by enforcement officers across jurisdictions, tracked by manufacturer and statutory compliance metrics.
            </p>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Products
          </button>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by commodity name or manufacturer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 dark:text-white"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-sky-500 dark:text-white"
          >
            <option value="ALL">All Categories ({inspections.length})</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-56 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-12 text-center border border-slate-200 dark:border-slate-800">
          <PackageSearch className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">No Products Recorded</h3>
          <p className="text-sm text-slate-500 mt-1">No scanned commodities match your current filter parameters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((item, idx) => {
            const pName = item.entity_info?.commodity_name || (item as any).product_name || "Pre-Packaged Goods";
            const cName = item.entity_info?.manufacturer_name_address || (item as any).company_name || "Enterprise Ltd.";
            const netQty = item.entity_info?.net_quantity && item.entity_info.net_quantity !== "Not Specified"
              ? item.entity_info.net_quantity
              : "Not Detected";
            const mrp = item.entity_info?.mrp && item.entity_info.mrp !== "Not Specified"
              ? item.entity_info.mrp
              : "Not Detected";

            const formatDate = (ts?: string) => {
              if (!ts) return "Recent";
              const d = new Date(ts);
              if (!isNaN(d.getTime())) {
                return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
              }
              const m = ts.match(/(\d{2})[-/](\d{2})[-/](\d{4})/);
              if (m) {
                return `${m[1]}/${m[2]}/${m[3]}`;
              }
              return "Recent";
            };

            return (
              <div
                key={idx}
                className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold text-xs rounded-md">
                      {item.category || "UNIVERSAL"}
                    </span>
                    {item.is_compliant ? (
                      <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-xs">
                        <CheckCircle2 className="w-4 h-4" /> Compliant ({item.compliance_score}%)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400 font-bold text-xs">
                        <XCircle className="w-4 h-4" /> Non-Compliant ({item.compliance_score}% Score)
                      </span>
                    )}
                  </div>

                  <h3 className="font-extrabold text-slate-900 dark:text-white text-base">
                    {pName}
                  </h3>

                  <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-1">
                    <Building2 className="w-3.5 h-3.5" />
                    {cName}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-slate-50 dark:bg-slate-800/60 p-2 rounded-lg">
                      <span className="text-slate-400">Net Quantity:</span>
                      <div className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 truncate" title={netQty}>
                        {netQty}
                      </div>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-800/60 p-2 rounded-lg">
                      <span className="text-slate-400">Retail Price (MRP):</span>
                      <div className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 truncate" title={mrp}>
                        {mrp}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {formatDate(item.timestamp)}
                  </span>
                  <a
                    href={item.notice?.notice_url || "http://localhost:8000/api/download_latest_notice"}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sky-600 dark:text-sky-400 font-semibold hover:underline flex items-center gap-1"
                  >
                    View Notice &rarr;
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
