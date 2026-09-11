import type { ComplianceResult } from "./compliance";

export interface BoundingBox {
  ymin: number; // Percentage or pixel coordinate 0..100
  xmin: number;
  ymax: number;
  xmax: number;
}

export interface ExtractedFieldAnnotation {
  id: string;
  fieldLabel: string;
  extractedValue: string;
  confidence: number;
  boundingBox: BoundingBox;
  measuredFontHeightMm?: number;
  requiredMinFontHeightMm?: number;
  status: "compliant" | "warning" | "violation";
  violationMessage?: string;
  panelIndex: number;
  panelName: "Front PDP" | "Back Panel" | "Side Panel";
}

export interface InspectionPanel {
  panelId: string;
  panelName: "Front PDP" | "Back Panel" | "Side Panel";
  imageUrl: string;
  pdpAreaSqCm: number;
  scaleRatioMmPerPixel: number; // Optical calibration scale
  annotations: ExtractedFieldAnnotation[];
}

export interface MultimodalInspectionRecord {
  inspectionNumber: string;
  productName: string;
  companyName: string;
  panels: InspectionPanel[];
  totalDeclarationsFound: number;
  complianceResult: ComplianceResult;
  aggregatedAt: string;
}
