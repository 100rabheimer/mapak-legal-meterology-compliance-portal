import type { ComplianceResult } from "./compliance";

export type InspectionState = "draft" | "uploaded" | "processing" | "review_required" | "completed" | "approved";

export interface Inspection {
  id: string;
  inspectionNumber: string;
  productName: string;
  category: string;
  location: string;
  inspectorName: string;
  createdAt: string;
  state: InspectionState;
  complianceResult?: ComplianceResult;
}
