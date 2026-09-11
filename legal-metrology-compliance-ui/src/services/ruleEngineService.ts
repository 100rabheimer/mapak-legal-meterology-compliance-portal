import rulesKb from "../data/rules_knowledge_base.json";
import type { DeclarationField, ComplianceResult, RuleViolation, RuleWarning } from "../types/compliance";

export interface MandatoryDeclarationRule {
  id: string;
  ruleNumber: string;
  title: string;
  description: string;
  required: boolean;
  mandatoryTaxPhrase?: string[];
  penaltySection: string;
}

export interface Rule7Threshold {
  pdpAreaRangeSqCm: string;
  minPdpAreaSqCm: number;
  maxPdpAreaSqCm: number;
  minGeneralFontHeightMm: number;
  minNetQtyNumeralHeightMm: number;
}

/**
 * Module 1: Master Legal Rule Engine & Knowledge Base Service
 * Evaluates extracted package declarations against statutory rules codified in rules_knowledge_base.json.
 */

export function getMasterRulesCount(): number {
  return rulesKb.totalMasterRules;
}

export function getMandatoryDeclarationRules(): MandatoryDeclarationRule[] {
  return rulesKb.mandatoryDeclarations;
}

/**
 * Look up Rule 7 Minimum Font Heights (mm) based on Principal Display Panel (PDP) Surface Area (cm²)
 */
export function getRule7FontThreshold(pdpAreaSqCm: number): Rule7Threshold {
  const table = rulesKb.rule7FontHeightTable as Rule7Threshold[];
  
  const matched = table.find(
    (row) => pdpAreaSqCm >= row.minPdpAreaSqCm && pdpAreaSqCm <= row.maxPdpAreaSqCm
  );

  return matched ?? table[table.length - 1]; // Fallback to largest threshold if area > 500 cm²
}

/**
 * Check Rule 11 SI Unit standard compliance and identify illegal unit symbols
 */
export function checkRule11UnitSymbols(text: string): { isValid: boolean; illegalSymbolFound?: string } {
  const blacklisted = rulesKb.rule11MetricUnits.blacklistedSymbols;
  const normalizedText = text.toLowerCase();

  for (const symbol of blacklisted) {
    // Regex matching word boundary or trailing punctuation for exact illegal unit symbol match
    const regex = new RegExp(`\\b${symbol.replace(".", "\\.")}\\b`, "i");
    if (regex.test(normalizedText)) {
      return { isValid: false, illegalSymbolFound: symbol };
    }
  }

  return { isValid: true };
}

/**
 * Evaluate all mandatory declarations against Module 1 Rules Knowledge Base
 */
export function evaluatePackageCompliance(
  declarations: Array<{
    id: string;
    label: string;
    value: string;
    confidence: number;
    fontHeightMm?: number;
  }>,
  pdpAreaSqCm: number = 85
): ComplianceResult {
  const violations: RuleViolation[] = [];
  const warnings: RuleWarning[] = [];
  const fontThreshold = getRule7FontThreshold(pdpAreaSqCm);

  let passedCount = 0;
  const totalMandatory = rulesKb.mandatoryDeclarations.length;

  // Track present declaration rules
  const presentRuleIds = new Set<string>();

  const processedDeclarations: DeclarationField[] = declarations.map((dec) => {
    let status: "verified" | "detected" | "needs_review" | "missing" = "verified";

    // Low confidence check (< 70%)
    if (dec.confidence < 70) {
      status = "needs_review";
      warnings.push({
        id: `warn-low-conf-${dec.id}`,
        title: `Low OCR Confidence in ${dec.label}`,
        description: `The extracted value "${dec.value}" has an OCR confidence score of ${dec.confidence}%. Manual verification with physical package recommended.`,
        severity: "medium",
        expectedRequirement: `Clear, high-confidence declaration of ${dec.label}`,
        observedValue: dec.value,
        rule: {
          id: `RULE-CONF-${dec.id}`,
          ruleNumber: "Rule 6",
          title: `${dec.label} Declaration Verification`,
          description: "Declarations must be legible and verifiable.",
          version: "2011"
        }
      });
    }

    // Check Rule 11 Metric Units (if Net Quantity declaration)
    if (dec.label.toLowerCase().includes("quantity") || dec.label.toLowerCase().includes("net")) {
      presentRuleIds.add("RULE-6-1-C");
      const unitCheck = checkRule11UnitSymbols(dec.value);

      if (!unitCheck.isValid) {
        status = "needs_review";
        violations.push({
          id: `viol-rule11-${dec.id}`,
          title: `Rule 11 Violation: Illegal Unit Symbol "${unitCheck.illegalSymbolFound}"`,
          description: `The Net Quantity declaration uses non-standard symbol "${unitCheck.illegalSymbolFound}". Rule 11 mandates legal metric SI symbols (g, kg, ml, l, L). Non-metric or corrupt symbols like "${unitCheck.illegalSymbolFound}" are prohibited under Section 36(1).`,
          severity: "high",
          statutorySection: "Section 36(1) read with Rule 11",
          expectedRequirement: "Standard SI metric symbol (g, kg, ml, l)",
          observedValue: dec.value,
          remedy: `Replace non-standard unit "${unitCheck.illegalSymbolFound}" with standard SI metric symbol (e.g. ml or g).`
        });
      }

      // Check Rule 7 Font Height for Net Qty numerals if height is measured
      if (dec.fontHeightMm && dec.fontHeightMm < fontThreshold.minNetQtyNumeralHeightMm) {
        violations.push({
          id: `viol-rule7-font-${dec.id}`,
          title: `Rule 7 Violation: Net Qty Font Height (${dec.fontHeightMm} mm < Required ${fontThreshold.minNetQtyNumeralHeightMm} mm)`,
          description: `For a package with PDP area of ${pdpAreaSqCm.toFixed(1)} cm², Rule 7 mandates a minimum Net Quantity numeral font height of ${fontThreshold.minNetQtyNumeralHeightMm} mm. Observed numeral height is ${dec.fontHeightMm} mm.`,
          severity: "high",
          statutorySection: "Rule 7 Table 1 read with Section 36(1)",
          expectedRequirement: `>= ${fontThreshold.minNetQtyNumeralHeightMm} mm height`,
          observedValue: `${dec.fontHeightMm} mm`,
          remedy: `Increase Net Quantity numeral height to at least ${fontThreshold.minNetQtyNumeralHeightMm} mm.`
        });
      }
    }

    // Check Rule 6(1)(e) MRP Tax Inclusion Phrase
    if (dec.label.toLowerCase().includes("mrp") || dec.label.toLowerCase().includes("price")) {
      presentRuleIds.add("RULE-6-1-E");
      const hasTaxPhrase = rulesKb.mandatoryDeclarations[4].mandatoryTaxPhrase?.some(phrase =>
        dec.value.toLowerCase().includes(phrase)
      );

      if (!hasTaxPhrase) {
        violations.push({
          id: `viol-tax-phrase-${dec.id}`,
          title: "Rule 6(1)(e) Violation: Missing Mandatory Tax Phrase 'incl. of all taxes'",
          description: "Maximum Retail Price (MRP) declaration must explicitly include the tax phrase 'incl. of all taxes' or 'inclusive of all taxes'.",
          severity: "high",
          statutorySection: "Rule 6(1)(e) read with Section 36(1)",
          expectedRequirement: "MRP ₹XX.XX (incl. of all taxes)",
          observedValue: dec.value,
          remedy: "Append mandatory phrase '(incl. of all taxes)' to the MRP declaration."
        });
      }
    }

    if (dec.label.toLowerCase().includes("manufacturer") || dec.label.toLowerCase().includes("packer")) {
      presentRuleIds.add("RULE-6-1-A");
    }
    if (dec.label.toLowerCase().includes("product") || dec.label.toLowerCase().includes("name")) {
      presentRuleIds.add("RULE-6-1-B");
    }
    if (dec.label.toLowerCase().includes("date") || dec.label.toLowerCase().includes("month") || dec.label.toLowerCase().includes("pack")) {
      presentRuleIds.add("RULE-6-1-D");
    }
    if (dec.label.toLowerCase().includes("consumer") || dec.label.toLowerCase().includes("care") || dec.label.toLowerCase().includes("contact")) {
      presentRuleIds.add("RULE-6-1-G");
    }
    if (dec.label.toLowerCase().includes("origin") || dec.label.toLowerCase().includes("country")) {
      presentRuleIds.add("RULE-6-1-H");
    }

    if (status === "verified" || status === "detected") {
      passedCount++;
    }

    return {
      id: dec.id,
      label: dec.label,
      value: dec.value,
      confidence: dec.confidence,
      status: status,
      required: true
    };
  });

  // Check for missing mandatory declarations
  for (const masterRule of rulesKb.mandatoryDeclarations) {
    if (!presentRuleIds.has(masterRule.id) && masterRule.id !== "RULE-6-1-F" && masterRule.id !== "RULE-6-1-H") {
      violations.push({
        id: `viol-missing-${masterRule.id}`,
        title: `Rule 6(1) Violation: Missing Declaration — ${masterRule.title}`,
        description: masterRule.description,
        severity: "high",
        statutorySection: masterRule.penaltySection,
        expectedRequirement: `Mandatory declaration of ${masterRule.title}`,
        observedValue: "NOT DETECTED ON PACKAGE",
        remedy: `Print clear and visible ${masterRule.title} declaration on the Principal Display Panel.`
      });
    }
  }

  // Calculate 0-100% compliance score
  const scoreDeductions = violations.length * 18 + warnings.length * 5;
  const complianceScore = Math.max(0, Math.min(100, 100 - scoreDeductions));

  let overallStatus: "pass" | "warning" | "violation" = "pass";
  if (violations.length > 0) {
    overallStatus = "violation";
  } else if (warnings.length > 0) {
    overallStatus = "warning";
  }

  return {
    inspectionId: "INS-2026-00147",
    productName: "Herbal Shampoo 180 ml",
    overallStatus,
    complianceScore,
    declarations: processedDeclarations,
    violations,
    warnings
  };
}
