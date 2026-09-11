import { AlertTriangle, CheckCircle2, ClipboardList, ScanLine } from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../components/common/StatusBadge";
import { recentInspections } from "../data/mockData";

const metrics = [
  ["Total inspections", "1,248", "Across all active officers", ClipboardList, "bg-blue-50 text-blue-600"],
  ["Compliant products", "876", "70.2% compliance rate", CheckCircle2, "bg-emerald-50 text-emerald-600"],
  ["Needs review", "218", "Awaiting officer verification", ScanLine, "bg-amber-50 text-amber-600"],
  ["Violations found", "154", "12.3% of inspections", AlertTriangle, "bg-rose-50 text-rose-600"],
] as const;

export function DashboardPage() {
 return <div className="space-y-7">
  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h1 className="page-title">Compliance dashboard</h1><p className="page-description">Monitor inspection activity, review pending cases, and track packaged commodity compliance.</p></div><Link to="/inspections/new" className="rounded-xl bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white transition hover:bg-blue-700">Start new inspection</Link></div>
  <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{metrics.map(([title, value, description, Icon, color]) => <article key={title} className="app-card p-5"><div className="flex items-start justify-between"><div><p className="text-sm font-medium text-slate-500">{title}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</p></div><div className={`rounded-xl p-3 ${color}`}><Icon className="h-5 w-5" /></div></div><p className="mt-4 text-xs text-slate-500">{description}</p></article>)}</section>
  <section className="grid gap-6 xl:grid-cols-3"><div className="app-card overflow-hidden xl:col-span-2"><div className="flex items-center justify-between border-b border-slate-100 px-6 py-5"><div><h2 className="font-semibold text-slate-900">Recent inspections</h2><p className="mt-1 text-sm text-slate-500">Latest uploaded products and compliance outcomes.</p></div><Link to="/reports" className="text-sm font-semibold text-blue-600 hover:text-blue-700">View reports</Link></div><div className="overflow-x-auto"><table className="min-w-full text-left"><thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-4">Inspection</th><th className="px-6 py-4">Product</th><th className="px-6 py-4">Date</th><th className="px-6 py-4">Status</th></tr></thead><tbody className="divide-y divide-slate-100">{recentInspections.map(item => <tr key={item.id} className="hover:bg-slate-50"><td className="px-6 py-4 text-sm font-semibold text-blue-600">{item.inspectionNumber}</td><td className="px-6 py-4"><p className="text-sm font-medium text-slate-800">{item.productName}</p><p className="mt-1 text-xs text-slate-500">{item.category}</p></td><td className="px-6 py-4 text-sm text-slate-600">{item.createdAt}</td><td className="px-6 py-4"><StatusBadge status={item.complianceResult!.overallStatus} /></td></tr>)}</tbody></table></div></div>
  <aside className="app-card p-6"><h2 className="font-semibold text-slate-900">Inspection guidance</h2><p className="mt-2 text-sm leading-6 text-slate-500">High-quality images help OCR identify declarations and preserve usable evidence.</p><div className="mt-5 space-y-4">{["Capture every declaration panel.", "Avoid glare, folds, shadows, and blur.", "Review fields with low OCR confidence.", "Approve only after officer verification."].map((text, i) => <div className="flex gap-3" key={text}><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-bold text-blue-700">{i+1}</span><p className="text-sm text-slate-700">{text}</p></div>)}</div></aside></section>
 </div>;
}
