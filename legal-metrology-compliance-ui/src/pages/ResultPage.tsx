import { useState } from "react";
import { AlertTriangle, CheckCircle2, Download, FileCheck, FileText, Gavel, Printer, ShieldAlert, X } from "lucide-react";
import { StatusBadge } from "../components/common/StatusBadge";
import { runVisionInspectionPipeline } from "../services/visionAiService";
import { generateLegalDocumentContent } from "../services/legalNoticeGenerator";
import { getActiveInspection, triggerPdfDownload } from "../services/apiClient";

export function ResultPage() {
  const [showDocModal, setShowDocModal] = useState(false);

  // Execute 3-Module Integration Pipeline
  const activeReport = getActiveInspection();
  const record = runVisionInspectionPipeline(
    activeReport?.entity_info?.commodity_name || "Herbal Shampoo 180 ml",
    activeReport?.entity_info?.manufacturer_name_address || "GreenCare Pvt. Ltd."
  );
  const { complianceResult, inspectionNumber, productName, companyName } = record;

  const legalDoc = generateLegalDocumentContent(record);

  const noticeDownloadUrl = activeReport?.notice?.notice_url || "http://localhost:8000/api/download_latest_notice";

  const handleDownloadPdf = () => {
    triggerPdfDownload(noticeDownloadUrl);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
              Module 3: Officer Enforcement Portal
            </span>
            <p className="text-xs text-slate-500">Inspection {inspectionNumber}</p>
          </div>

          <h1 className="page-title mt-1">Compliance Result & Prosecution Generator</h1>

          <p className="page-description">
            Automated statutory evaluation under Legal Metrology Act 2009 and Legal Metrology (Packaged Commodities) Rules 2011.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setShowDocModal(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-rose-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-rose-800 shadow-sm"
          >
            <Gavel className="h-4 w-4" />
            {legalDoc.documentType === "SHOW_CAUSE_NOTICE" ? "Generate Show-Cause Notice" : "Generate Compliance Certificate"}
          </button>

          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Printer className="h-4 w-4" /> Print Record
          </button>
        </div>
      </div>

      {/* Module 3 Executive Scorecard (0-100%) */}
      <section className="app-card overflow-hidden">
        <div
          className={`grid gap-6 p-6 md:grid-cols-4 ${
            complianceResult.overallStatus === "violation"
              ? "bg-linear-to-r from-rose-50 to-white"
              : complianceResult.overallStatus === "warning"
              ? "bg-linear-to-r from-amber-50 to-white"
              : "bg-linear-to-r from-emerald-50 to-white"
          }`}
        >
          <div
            className={`flex h-16 w-16 items-center justify-center rounded-2xl ${
              complianceResult.overallStatus === "violation"
                ? "bg-rose-100 text-rose-700"
                : complianceResult.overallStatus === "warning"
                ? "bg-amber-100 text-amber-700"
                : "bg-emerald-100 text-emerald-700"
            }`}
          >
            {complianceResult.overallStatus === "violation" ? (
              <AlertTriangle className="h-8 w-8" />
            ) : (
              <CheckCircle2 className="h-8 w-8" />
            )}
          </div>

          <div className="md:col-span-2">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-slate-900">
                {complianceResult.overallStatus === "violation"
                  ? "Non-Compliant Commodity — Legal Notice Required"
                  : complianceResult.overallStatus === "warning"
                  ? "Manual Officer Review Required"
                  : "Statutory Compliance Verified"}
              </h2>

              <StatusBadge status={complianceResult.overallStatus} />
            </div>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              {complianceResult.overallStatus === "violation"
                ? `Evaluation against Module 1 Rules Knowledge Base identified ${complianceResult.violations.length} statutory violations. Legal Notice under Section 36(1) pre-generated.`
                : "All mandatory declarations under Rule 6(1), Rule 7, and Rule 11 have been verified against statutory requirements."}
            </p>
          </div>

          <div className="md:text-right">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Compliance Scorecard</p>
            <p
              className={`mt-1 text-5xl font-extrabold ${
                complianceResult.complianceScore >= 80
                  ? "text-emerald-700"
                  : complianceResult.complianceScore >= 60
                  ? "text-amber-700"
                  : "text-rose-700"
              }`}
            >
              {complianceResult.complianceScore}%
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-3">
        {/* Statutory Violations & Declarations Table */}
        <section className="app-card xl:col-span-2 overflow-hidden">
          <div className="border-b border-slate-100 px-6 py-5 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">Statutory Violations & Defects Table</h2>
              <p className="mt-1 text-sm text-slate-500">Legal citation, observed defect, and statutory remedy.</p>
            </div>
            <span className="rounded-md bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700">
              {complianceResult.violations.length} Violations Flagged
            </span>
          </div>

          {/* Violations Listing */}
          {complianceResult.violations.length > 0 && (
            <div className="divide-y divide-rose-100 bg-rose-50/40">
              {complianceResult.violations.map((v) => (
                <div key={v.id} className="p-6 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-rose-600 px-2 py-0.5 text-xs font-bold text-white">
                        {v.statutorySection}
                      </span>
                      <h3 className="text-sm font-bold text-rose-900">{v.title}</h3>
                    </div>
                    <span className="text-xs font-semibold uppercase text-rose-700">{v.severity} Priority</span>
                  </div>

                  <p className="text-xs leading-5 text-slate-700">{v.description}</p>

                  <div className="grid gap-2 sm:grid-cols-2 mt-3 pt-2 border-t border-rose-200/60 text-xs">
                    <div>
                      <span className="font-semibold text-slate-500">Observed Defect:</span>
                      <p className="font-bold text-rose-700">{v.observedValue}</p>
                    </div>

                    <div>
                      <span className="font-semibold text-slate-500">Statutory Remedy:</span>
                      <p className="font-medium text-emerald-800">{v.remedy}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Declaration Checklist */}
          <div className="border-t border-slate-200 px-6 py-4 bg-slate-50">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Rule 6(1) Declaration Checklist</h3>
          </div>

          <div className="divide-y divide-slate-100">
            {complianceResult.declarations.map((declaration) => (
              <div key={declaration.id} className="flex items-center justify-between gap-4 px-6 py-4">
                <div>
                  <p className="text-sm font-semibold text-slate-800">{declaration.label}</p>
                  <p className="mt-1 text-sm text-slate-600">{declaration.value}</p>
                </div>

                {declaration.status === "needs_review" ? (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
                    <AlertTriangle className="h-3.5 w-3.5" /> Review Needed
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Verified
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Legal Prosecution Side Panel */}
        <aside className="space-y-6">
          <div className="app-card p-6 border-l-4 border-l-rose-600">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-rose-50 p-3 text-rose-700">
                <Gavel className="h-6 w-6" />
              </div>

              <div>
                <h2 className="font-semibold text-slate-900">Legal Prosecution Action</h2>
                <p className="text-xs text-slate-500">Sec 15, 36(1) & 51 Legal Metrology Act</p>
              </div>
            </div>

            <p className="mt-4 text-xs leading-6 text-slate-600">
              Pre-generated Show-Cause Notice & Seizure Memorandum includes official GoI header, offender details ({companyName}), statutory penalty matrix (up to ₹25,000 first offence), and mandatory 7-day response directive.
            </p>

            <button
              onClick={() => setShowDocModal(true)}
              className="mt-5 w-full rounded-xl bg-rose-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-rose-800 shadow-sm flex items-center justify-center gap-2"
            >
              <FileText className="h-4 w-4" /> View Legal Document PDF
            </button>
          </div>

          <div className="app-card p-6">
            <h2 className="font-semibold text-slate-900">Statutory Penalty Matrix</h2>
            <div className="mt-3 space-y-3 text-xs text-slate-600">
              <div className="rounded-xl bg-slate-50 p-3 border border-slate-200">
                <p className="font-bold text-slate-800">1st Offence — Section 36(1)</p>
                <p className="mt-1">Fine up to <strong>₹25,000</strong> per offender/director.</p>
              </div>

              <div className="rounded-xl bg-slate-50 p-3 border border-slate-200">
                <p className="font-bold text-slate-800">2nd Offence — Section 36(1)</p>
                <p className="mt-1">Fine up to <strong>₹50,000</strong>.</p>
              </div>

              <div className="rounded-xl bg-slate-50 p-3 border border-slate-200">
                <p className="font-bold text-slate-800">Subsequent Offences</p>
                <p className="mt-1">Fine up to <strong>₹1,00,000</strong> or <strong>Imprisonment up to 1 Year</strong>.</p>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Formal Court-Admissible Legal Document Modal */}
      {showDocModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs">
          <div className="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white p-8 shadow-2xl">
            <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <span className="rounded bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-800">
                  {legalDoc.documentType}
                </span>
                <p className="mt-1 text-xs text-slate-500">{legalDoc.documentNumber}</p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleDownloadPdf}
                  className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 flex items-center gap-1"
                >
                  <Download className="h-3.5 w-3.5" /> Download Official Vector PDF Notice
                </button>
                <button
                  onClick={() => setShowDocModal(false)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Document Render Canvas */}
            <div
              className="bg-white"
              dangerouslySetInnerHTML={{ __html: legalDoc.htmlContent }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
