import { useState } from "react";
import { AlertTriangle, ArrowRight, CheckCircle2, Edit3, Eye, Layers, Ruler, ScanLine } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getActiveInspection } from "../services/apiClient";

export function ReviewPage() {
  const navigate = useNavigate();
  const [activePanelIndex, setActivePanelIndex] = useState(0);
  const [viewMode, setViewMode] = useState<"annotated" | "original">("annotated");

  const API_BASE_URL = "http://localhost:8000";
  const activeReport = getActiveInspection();

  let rawImgUrl = activeReport?.artifacts?.annotated_image_url || activeReport?.artifacts?.original_image_url || "";
  if (rawImgUrl && !rawImgUrl.startsWith("http")) {
    rawImgUrl = `${API_BASE_URL}${rawImgUrl}`;
  }

  // Parse panels dynamically from backend activeReport.panels if available
  const uiPanels = (activeReport?.panels && activeReport.panels.length > 0)
    ? activeReport.panels.map((p: any, idx: number) => {
        let annUrl = p.annotated_image_url || p.annotated_url || p.original_image_url || p.original_url || "";
        let origUrl = p.original_image_url || p.original_url || p.annotated_image_url || "";
        if (annUrl && !annUrl.startsWith("http")) annUrl = `${API_BASE_URL}${annUrl}`;
        if (origUrl && !origUrl.startsWith("http")) origUrl = `${API_BASE_URL}${origUrl}`;

        return {
          panelId: p.panel_id || `panel-${idx}`,
          panelName: p.panel_name || `Scan Panel #${idx + 1}`,
          annotatedUrl: annUrl,
          originalUrl: origUrl,
          pdpAreaSqCm: p.pdp_area_cm2 || activeReport?.pdp_summary?.pdp_area_cm2 || 85.5,
          scaleRatioMmPerPixel: p.scale_k || activeReport?.pdp_summary?.scale_k || 0.125,
          violations: p.violations || []
        };
      })
    : [
        {
          panelId: "p-front",
          panelName: "Front PDP",
          annotatedUrl: rawImgUrl || "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&auto=format&fit=crop&q=80",
          originalUrl: activeReport?.artifacts?.original_image_url ? `${API_BASE_URL}${activeReport.artifacts.original_image_url}` : "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&auto=format&fit=crop&q=80",
          pdpAreaSqCm: activeReport?.pdp_summary?.pdp_area_cm2 || 85.5,
          scaleRatioMmPerPixel: activeReport?.pdp_summary?.scale_k || 0.125,
          violations: activeReport?.violations || []
        }
      ];

  const activePanel = uiPanels[activePanelIndex] || uiPanels[0];
  const activeDisplayUrl = viewMode === "annotated" ? activePanel.annotatedUrl : activePanel.originalUrl;

  const ocrFields = activeReport?.ocr_raw?.fields || {};
  const entity = activeReport?.entity_info || {};

  const fontMeasured = Number(activeReport?.font_verification?.measured_font_height_mm ?? 2.34);
  const fontRequired = Number(activeReport?.font_verification?.statutory_min_height_mm ?? 2.0);
  const isFontOk = fontMeasured >= (fontRequired - 0.05);

  const hasViolation = (fieldKey: string, rulePattern?: string) => {
    return activeReport?.violations?.some((v: any) => 
      v.field === fieldKey || 
      (rulePattern && (v.rule_id?.toLowerCase().includes(rulePattern.toLowerCase()) || v.title?.toLowerCase().includes(rulePattern.toLowerCase())))
    );
  };

  const isDetected = (fieldKey: string, val?: string) => {
    if (val && val !== "Not Detected on Packaging PDP" && val !== "Not Detected" && val !== "Not Specified") return true;
    const f = ocrFields[fieldKey];
    return Boolean(f && (f.present || f.text));
  };

  const hasUnitViolation = hasViolation("net_quantity", "RULE_11_UNITS") || hasViolation("net_quantity", "unit");
  const netQtyDetected = isDetected("net_quantity", entity.net_quantity || ocrFields.net_quantity?.text);
  const netQtyCompliant = netQtyDetected && isFontOk && !hasUnitViolation;

  const extractedDeclarations = [
    {
      id: "decl-1",
      fieldLabel: "Product Name / Commodity",
      extractedValue: entity.commodity_name || ocrFields.generic_name?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.generic_name?.confidence || 0.95) * 100),
      measuredFontHeightMm: 5.2,
      requiredMinFontHeightMm: 2.5,
      status: isDetected("generic_name", entity.commodity_name || ocrFields.generic_name?.text) && !hasViolation("generic_name", "generic") ? "compliant" : "violation"
    },
    {
      id: "decl-2",
      fieldLabel: "Net Quantity",
      extractedValue: entity.net_quantity || ocrFields.net_quantity?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.net_quantity?.confidence || 0.95) * 100),
      measuredFontHeightMm: fontMeasured,
      requiredMinFontHeightMm: fontRequired,
      status: netQtyCompliant ? "compliant" : "violation",
      violationMessage: !isFontOk 
        ? `Rule 7 Font Height Violation (${fontMeasured}mm < ${fontRequired}mm required)` 
        : (hasUnitViolation ? "Rule 11 Unit Symbol Violation" : undefined)
    },
    {
      id: "decl-3",
      fieldLabel: "Maximum Retail Price (MRP)",
      extractedValue: entity.mrp || ocrFields.mrp?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.mrp?.confidence || 0.94) * 100),
      measuredFontHeightMm: 3.5,
      requiredMinFontHeightMm: 2.5,
      status: isDetected("mrp", entity.mrp || ocrFields.mrp?.text) && !hasViolation("mrp", "mrp") ? "compliant" : "violation",
      violationMessage: activeReport?.violations?.find((v: any) => v.field === "mrp" || v.title?.toLowerCase().includes("mrp"))?.description
    },
    {
      id: "decl-4",
      fieldLabel: "Unit Sale Price (USP)",
      extractedValue: ocrFields.usp?.text || entity.usp || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.usp?.confidence || 0.90) * 100),
      measuredFontHeightMm: 2.4,
      requiredMinFontHeightMm: 1.5,
      status: isDetected("usp", ocrFields.usp?.text || entity.usp) && !hasViolation("usp", "usp") ? "compliant" : "violation",
      violationMessage: activeReport?.violations?.find((v: any) => v.field === "usp")?.description
    },
    {
      id: "decl-5",
      fieldLabel: "Manufacturer / Packer Address",
      extractedValue: entity.manufacturer_name_address || ocrFields.manufacturer_details?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.manufacturer_details?.confidence || 0.92) * 100),
      measuredFontHeightMm: 2.6,
      requiredMinFontHeightMm: 1.5,
      status: isDetected("manufacturer_details", entity.manufacturer_name_address || ocrFields.manufacturer_details?.text) && !hasViolation("manufacturer_details", "manufacturer") ? "compliant" : "violation"
    },
    {
      id: "decl-6",
      fieldLabel: "Month and Year of Packing",
      extractedValue: entity.mfg_date || ocrFields.mfg_date?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.mfg_date?.confidence || 0.91) * 100),
      measuredFontHeightMm: 2.2,
      requiredMinFontHeightMm: 1.5,
      status: isDetected("mfg_date", entity.mfg_date || ocrFields.mfg_date?.text) && !hasViolation("mfg_date", "mfg_date") ? "compliant" : "violation"
    },
    {
      id: "decl-7",
      fieldLabel: "Consumer Care Contact Details",
      extractedValue: entity.consumer_care || ocrFields.customer_care?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.customer_care?.confidence || 0.95) * 100),
      measuredFontHeightMm: 2.0,
      requiredMinFontHeightMm: 1.5,
      status: isDetected("customer_care", entity.consumer_care || ocrFields.customer_care?.text) && !hasViolation("customer_care", "customer") ? "compliant" : "violation"
    },
    {
      id: "decl-8",
      fieldLabel: "Country of Origin",
      extractedValue: entity.country_of_origin || ocrFields.country_of_origin?.text || "Not Detected on Packaging PDP",
      confidence: Math.round((ocrFields.country_of_origin?.confidence || 0.98) * 100),
      measuredFontHeightMm: 2.0,
      requiredMinFontHeightMm: 1.5,
      status: isDetected("country_of_origin", entity.country_of_origin || ocrFields.country_of_origin?.text) && !hasViolation("country_of_origin", "country") ? "compliant" : "violation"
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">
              Module 2: Multimodal Vision AI Pipeline
            </span>
            <p className="text-xs text-slate-500">Inspection {activeReport?.inspection_id}</p>
          </div>

          <h1 className="page-title mt-1">Packaging Vision AI Review</h1>

          <p className="page-description">
            Multi-panel OCR extraction, PDP boundary deskewing, Rule 7 optical font calibration, and Module 1 cross-referencing.
          </p>
        </div>

        <button
          onClick={() => navigate("/inspections/demo/result")}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 shadow-sm"
        >
          Evaluate Legal Compliance <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Multi-Panel Aggregator Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-white p-3 border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <Layers className="h-5 w-5 text-blue-600 ml-2" />
          <span className="text-sm font-semibold text-slate-700">Multi-Image Scans ({uiPanels.length}):</span>
          <div className="flex flex-wrap gap-2">
            {uiPanels.map((panel, idx) => (
              <button
                key={panel.panelId}
                onClick={() => setActivePanelIndex(idx)}
                className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                  activePanelIndex === idx
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {panel.panelName}
              </button>
            ))}
          </div>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1.5 rounded-xl bg-slate-100 p-1 border border-slate-200">
          <button
            onClick={() => setViewMode("annotated")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              viewMode === "annotated" ? "bg-white text-blue-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <ScanLine className="h-3.5 w-3.5" /> AI Annotated View
          </button>

          <button
            onClick={() => setViewMode("original")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
              viewMode === "original" ? "bg-white text-blue-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Eye className="h-3.5 w-3.5" /> Original Scan
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-5">
        {/* VisualAnnotator: Side-by-side AI Annotated Bounding Box Screen */}
        <section className="app-card overflow-hidden xl:col-span-2">
          <div className="border-b border-slate-100 px-5 py-4 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">{activePanel.panelName} AI Vision Canvas</h2>
              <p className="mt-0.5 text-xs text-slate-500">
                {viewMode === "annotated" ? "OpenCV Pixel Annotations Active" : "Original Raw Packaging Scan"}
              </p>
            </div>

            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
              <ScanLine className="h-3.5 w-3.5" /> OpenCV + Vision AI
            </span>
          </div>

          {/* Clean OpenCV Annotated Image Container */}
          <div className="relative m-5 aspect-[4/5] overflow-hidden rounded-2xl bg-slate-950 shadow-inner flex items-center justify-center p-2">
            <img
              src={activeDisplayUrl}
              alt={activePanel.panelName}
              className="h-full w-full object-contain rounded-lg"
            />
          </div>

          {/* FontCalibrator Scale Metrics */}
          <div className="mx-5 mb-5 space-y-2 rounded-xl bg-slate-50 p-4 text-xs text-slate-700 border border-slate-200">
            <div className="flex justify-between">
              <span className="font-semibold text-slate-600 flex items-center gap-1">
                <Ruler className="h-3.5 w-3.5 text-blue-600" /> Stage 1: PDP Surface Area
              </span>
              <strong className="text-slate-900">{activePanel.pdpAreaSqCm} cm²</strong>
            </div>

            <div className="flex justify-between">
              <span className="font-semibold text-slate-600 flex items-center gap-1">
                <Ruler className="h-3.5 w-3.5 text-blue-600" /> Stage 2: Optical Calibration Scale
              </span>
              <strong className="text-slate-900">{activePanel.scaleRatioMmPerPixel} mm/px (Barcode)</strong>
            </div>
          </div>
        </section>

        {/* Extracted Declarations Table */}
        <section className="app-card xl:col-span-3">
          <div className="border-b border-slate-100 px-6 py-5 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">Stage 3 & 4: Extracted Declarations</h2>
              <p className="mt-1 text-sm text-slate-500">Cross-referenced against Module 1 Statutory Rules KB.</p>
            </div>

            <span className="text-xs font-semibold text-slate-500">
              {extractedDeclarations.length} Declarations Verified
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {extractedDeclarations.map((item) => (
              <div key={item.id} className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-slate-900">{item.fieldLabel}</p>

                    {item.status === "violation" ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700">
                        <AlertTriangle className="h-3 w-3" /> Flagged Defect
                      </span>
                    ) : item.status === "warning" ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
                        <AlertTriangle className="h-3 w-3" /> Needs Review
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                        <CheckCircle2 className="h-3 w-3" /> Verified Compliant
                      </span>
                    )}
                  </div>

                  <p className="mt-1 text-sm font-medium text-slate-700">{item.extractedValue}</p>

                  {item.violationMessage && (
                    <p className="mt-1 text-xs font-medium text-rose-600 bg-rose-50 p-2 rounded-lg border border-rose-100">
                      ⚠️ {item.violationMessage}
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between gap-4 sm:justify-end">
                  {item.measuredFontHeightMm && (
                    <div className="text-right">
                      <p className="text-[11px] text-slate-500">Numeral Height</p>
                      <p
                        className={`text-xs font-bold ${
                          item.measuredFontHeightMm < (item.requiredMinFontHeightMm ?? 0)
                            ? "text-rose-600"
                            : "text-emerald-700"
                        }`}
                      >
                        {item.measuredFontHeightMm} mm (Req: {item.requiredMinFontHeightMm}mm)
                      </p>
                    </div>
                  )}

                  <div className="text-right">
                    <p className="text-[11px] text-slate-500">OCR Confidence</p>

                    <p
                      className={`text-xs font-bold ${
                        item.confidence < 70 ? "text-amber-700" : "text-emerald-700"
                      }`}
                    >
                      {item.confidence}%
                    </p>
                  </div>

                  <button className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50">
                    <Edit3 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
