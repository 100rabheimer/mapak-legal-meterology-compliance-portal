import type { ComplianceResult } from "../types/compliance";
import type { Inspection } from "../types/inspection";

export const recentInspections: Inspection[] = [
  { id: "1", inspectionNumber: "INS-2026-00148", productName: "Premium Tea 500 g", category: "Food & Beverages", location: "Kolkata Market", inspectorName: "A. Sharma", createdAt: "06 Sep 2026", state: "completed", complianceResult: { inspectionId: "1", productName: "Premium Tea 500 g", overallStatus: "pass", complianceScore: 92, declarations: [], violations: [], warnings: [] } },
  { id: "2", inspectionNumber: "INS-2026-00147", productName: "Herbal Shampoo 180 ml", category: "Personal Care", location: "Kolkata Market", inspectorName: "A. Sharma", createdAt: "06 Sep 2026", state: "review_required", complianceResult: { inspectionId: "2", productName: "Herbal Shampoo 180 ml", overallStatus: "warning", complianceScore: 74, declarations: [], violations: [], warnings: [] } },
  { id: "3", inspectionNumber: "INS-2026-00146", productName: "Imported Kitchen Container", category: "Household Goods", location: "Howrah Market", inspectorName: "R. Das", createdAt: "05 Sep 2026", state: "completed", complianceResult: { inspectionId: "3", productName: "Imported Kitchen Container", overallStatus: "violation", complianceScore: 48, declarations: [], violations: [], warnings: [] } },
];

export const demoComplianceResult: ComplianceResult = {
  inspectionId: "INS-2026-00147",
  productName: "Herbal Shampoo 180 ml",
  overallStatus: "warning",
  complianceScore: 74,
  declarations: [
    { id: "d1", label: "Product name", value: "Herbal Shampoo", confidence: 99, status: "verified", required: true },
    { id: "d2", label: "Net quantity", value: "180 ml", confidence: 97, status: "verified", required: true },
    { id: "d3", label: "Maximum Retail Price", value: "₹199.00 (incl. of all taxes)", confidence: 94, status: "verified", required: true },
    { id: "d4", label: "Manufacturer / Packer address", value: "GreenCare Pvt. Ltd., Mumbai", confidence: 88, status: "detected", required: true },
    { id: "d5", label: "Month and year of packing", value: "Aug 2026", confidence: 92, status: "verified", required: true },
    { id: "d6", label: "Consumer-care phone", value: "1800-XXX-1122", confidence: 53, status: "needs_review", required: true },
  ],
  warnings: [
    { id: "w1", title: "Low OCR confidence in consumer-care number", description: "The consumer-care contact number was identified, but the scan quality does not support reliable automated verification.", severity: "medium", expectedRequirement: "A clear and verifiable consumer-care contact declaration.", observedValue: "1800-XXX-1122", rule: { id: "LMPC-R6-CC", ruleNumber: "Rule 6", title: "Consumer-care declaration", description: "Consumer-care details should be declared as applicable.", version: "2011" } }
  ],
  violations: []
};
