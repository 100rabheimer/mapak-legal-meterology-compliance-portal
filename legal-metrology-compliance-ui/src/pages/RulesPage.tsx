import React, { useEffect, useState } from "react";
import { fetchMasterRules, addMasterRule } from "../services/apiClient";
import { useAuthStore } from "../stores/authStores";
import {
  BookOpen,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldCheck,
  Tag,
  ExternalLink,
  RefreshCw,
  Plus
} from "lucide-react";

interface Rule {
  rule_id: string;
  clause: string;
  title: string;
  category: string;
  is_universal?: boolean;
  mandatory?: boolean;
  status?: string;
  text: string;
  source_pdf?: string;
  source_url?: string;
}

export const RulesPage: React.FC = () => {
  const { user } = useAuthStore();
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);

  const [isAddingRule, setIsAddingRule] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newRule, setNewRule] = useState({
    rule_id: "",
    clause: "",
    title: "",
    category: "MANDATORY DECLARATION",
    text: "",
    mandatory: true,
  });

  const loadRules = async () => {
    setLoading(true);
    try {
      const data = await fetchMasterRules();
      setRules(data);
    } catch (err) {
      console.error("Failed to load rules", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRuleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      // Auto-generate ID if empty
      const payload = {
        ...newRule,
        rule_id: newRule.rule_id || `RULE-NEW-${Math.floor(Math.random() * 10000)}`,
      };
      await addMasterRule(payload);
      await loadRules();
      setIsAddingRule(false);
      setNewRule({
        rule_id: "",
        clause: "",
        title: "",
        category: "MANDATORY DECLARATION",
        text: "",
        mandatory: true,
      });
    } catch (err) {
      console.error("Failed to add rule", err);
      alert("Failed to add rule.");
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const categories = Array.from(new Set(rules.map((r) => r.category || "GENERAL"))).sort();

  const filteredRules = rules.filter((rule) => {
    const titleStr = String(rule?.title || (rule as any)?.rule_name || "").toLowerCase();
    const clauseStr = String(rule?.clause || rule?.rule_id || "").toLowerCase();
    const ruleIdStr = String(rule?.rule_id || "").toLowerCase();
    const textStr = String(rule?.text || (rule as any)?.description || "").toLowerCase();
    const query = searchTerm.toLowerCase();

    const matchesSearch =
      titleStr.includes(query) ||
      clauseStr.includes(query) ||
      ruleIdStr.includes(query) ||
      textStr.includes(query);

    const matchesCategory =
      categoryFilter === "ALL" || (rule.category && rule.category.toUpperCase() === categoryFilter.toUpperCase());

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-8 border border-indigo-500/20 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 font-semibold tracking-wider text-xs uppercase mb-2">
              <BookOpen className="w-4 h-4" /> Department of Consumer Affairs KB
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Legal Rules & Statutory Gazette Repository
            </h1>
            <p className="text-slate-300 text-sm mt-1 max-w-2xl">
              Official 49 statutory rules under Legal Metrology (Packaged Commodities) Rules, 2011 & Amendments, synthesized into Module 1 Knowledge Base.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {user?.role === "admin" && (
              <button
                onClick={() => setIsAddingRule(true)}
                className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition-all shadow-md active:scale-95"
              >
                <Plus className="w-4 h-4" />
                Add New Rule
              </button>
            )}
            <button
              onClick={loadRules}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh Rules
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3 top-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by rule title, clause (e.g. Rule 6(1)), or text..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:text-white"
          >
            <option value="ALL">All Categories ({rules.length})</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Rules Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : filteredRules.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-12 text-center border border-slate-200 dark:border-slate-800">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">No Legal Rules Found</h3>
          <p className="text-sm text-slate-500 mt-1">Try refining your search query or selecting a different category filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRules.map((rule) => (
            <div
              key={rule.rule_id}
              onClick={() => setSelectedRule(rule)}
              className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 hover:border-indigo-500 dark:hover:border-indigo-500 transition-all cursor-pointer shadow-sm hover:shadow-md group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-mono text-xs font-semibold rounded-md border border-indigo-200 dark:border-indigo-800">
                    {rule.clause || rule.rule_id}
                  </span>
                  <div className="flex items-center gap-1">
                    {rule.mandatory !== false && (
                      <span className="px-2 py-0.5 bg-rose-100 dark:bg-rose-950/50 text-rose-700 dark:text-rose-400 text-[10px] font-bold uppercase rounded">
                        Mandatory
                      </span>
                    )}
                    {rule.is_universal && (
                      <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 text-[10px] font-bold uppercase rounded">
                        Universal
                      </span>
                    )}
                  </div>
                </div>

                <h3 className="font-bold text-slate-900 dark:text-white text-base group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
                  {rule.title || (rule as any).rule_name || rule.rule_id}
                </h3>

                <p className="text-slate-600 dark:text-slate-400 text-xs mt-2 line-clamp-3 leading-relaxed">
                  {rule.text || (rule as any).description || "Statutory regulation details under Legal Metrology Act, 2009."}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Tag className="w-3.5 h-3.5" />
                  {rule.category || "GENERAL"}
                </span>
                <span className="text-indigo-600 dark:text-indigo-400 font-semibold group-hover:underline flex items-center gap-1">
                  Details &rarr;
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Rule Detail Modal */}
      {selectedRule && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <span className="px-2.5 py-1 bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-mono text-xs font-bold rounded">
                  {selectedRule.clause || selectedRule.rule_id}
                </span>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-2">
                  {selectedRule.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedRule(null)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold p-1"
              >
                &times;
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Statutory Text & Requirement</h4>
                <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-sans leading-relaxed">
                  {selectedRule.text}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                  <div className="text-xs text-slate-400 font-semibold">Category</div>
                  <div className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                    {selectedRule.category || "GENERAL"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                  <div className="text-xs text-slate-400 font-semibold">Applicability Scope</div>
                  <div className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                    {selectedRule.is_universal ? "Universal Pre-Packaged Goods" : "Commodity Specific"}
                  </div>
                </div>
              </div>

              {selectedRule.source_pdf && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Official Source Gazette</h4>
                  <a
                    href={selectedRule.source_pdf}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-indigo-600 dark:text-indigo-400 text-xs font-semibold hover:underline"
                  >
                    <FileText className="w-4 h-4" /> View Gazette PDF Reference <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedRule(null)}
                className="px-5 py-2 bg-slate-800 text-white rounded-xl text-sm font-medium hover:bg-slate-700 transition-colors"
              >
                Close Rule Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add New Rule Modal */}
      {isAddingRule && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Add New Statutory Rule</h2>
            <form onSubmit={handleAddRuleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Clause (e.g. Rule 6(1))</label>
                  <input
                    required
                    type="text"
                    value={newRule.clause}
                    onChange={(e) => setNewRule({ ...newRule, clause: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Category</label>
                  <select
                    value={newRule.category}
                    onChange={(e) => setNewRule({ ...newRule, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
                  >
                    <option value="MANDATORY DECLARATION">Mandatory Declaration</option>
                    <option value="SPECIAL PROVISION">Special Provision</option>
                    <option value="GENERAL">General</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Rule Title</label>
                <input
                  required
                  type="text"
                  value={newRule.title}
                  onChange={(e) => setNewRule({ ...newRule, title: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1">Statutory Text</label>
                <textarea
                  required
                  rows={4}
                  value={newRule.text}
                  onChange={(e) => setNewRule({ ...newRule, text: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white resize-none"
                ></textarea>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="mandatoryCheck"
                  checked={newRule.mandatory}
                  onChange={(e) => setNewRule({ ...newRule, mandatory: e.target.checked })}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <label htmlFor="mandatoryCheck" className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  This is a mandatory requirement
                </label>
              </div>
              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsAddingRule(false)}
                  className="px-5 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-500 transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : "Save Rule to KB"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
