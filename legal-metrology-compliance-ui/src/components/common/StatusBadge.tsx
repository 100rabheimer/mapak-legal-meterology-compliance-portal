import type { ComplianceStatus } from "../../types/compliance";

const styles: Record<ComplianceStatus, { label: string; classes: string }> = {
  pass: { label: "Compliant", classes: "bg-emerald-50 text-emerald-700 ring-emerald-600/20" },
  warning: { label: "Needs Review", classes: "bg-amber-50 text-amber-700 ring-amber-600/20" },
  violation: { label: "Violation Found", classes: "bg-rose-50 text-rose-700 ring-rose-600/20" },
};

export function StatusBadge({ status }: { status: ComplianceStatus }) {
  const item = styles[status];
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${item.classes}`}>{item.label}</span>;
}
