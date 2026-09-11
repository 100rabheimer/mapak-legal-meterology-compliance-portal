export type ComplianceStatus = "pass" | "warning" | "violation";
export type DeclarationState = "detected" | "missing" | "needs_review" | "verified";
export type ViolationSeverity = "low" | "medium" | "high" | "critical";

export interface LegalRule {
  id: string;
  ruleNumber: string;
  title: string;
  description: string;
  version: string;
}

export interface ExtractedDeclaration {
  id: string;
  label: string;
  value: string;
  confidence: number;
  status: DeclarationState;
  required: boolean;
}

export interface Violation {
  id: string;
  title: string;
  description: string;
  severity: ViolationSeverity;
  expectedRequirement: string;
  observedValue?: string;
  rule: LegalRule;
}

export interface ComplianceResult {
  inspectionId: string;
  productName: string;
  overallStatus: ComplianceStatus;
  complianceScore: number;
  declarations: ExtractedDeclaration[];
  violations: Violation[];
  warnings: Violation[];
}
