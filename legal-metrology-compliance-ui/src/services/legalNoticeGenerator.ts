import type { ComplianceResult } from "../types/compliance";
import type { MultimodalInspectionRecord } from "../types/vision";

/**
 * Module 3: Legal Notice Generator Service
 * Generates court-admissible formal documents under Sections 15, 36(1), and 51 of the Legal Metrology Act, 2009.
 */

export function generateLegalDocumentContent(record: MultimodalInspectionRecord): {
  documentType: "SHOW_CAUSE_NOTICE" | "COMPLIANCE_CERTIFICATE";
  title: string;
  documentNumber: string;
  htmlContent: string;
} {
  const { complianceResult, inspectionNumber, productName, companyName, aggregatedAt } = record;
  const isViolation = complianceResult.overallStatus === "violation";
  const dateStr = new Date(aggregatedAt).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric"
  });

  const docNo = isViolation
    ? `SCN/DoCA/LM/2026/${inspectionNumber.replace("INS-", "")}`
    : `CERT/DoCA/LM/2026/${inspectionNumber.replace("INS-", "")}`;

  if (!isViolation) {
    return {
      documentType: "COMPLIANCE_CERTIFICATE",
      title: "STATUTORY COMPLIANCE INSPECTION CERTIFICATE & COMMERCIAL CLEARANCE",
      documentNumber: docNo,
      htmlContent: `
        <div style="font-family: 'Times New Roman', serif; padding: 40px; color: #1a1a1a; max-w: 800px; margin: auto; border: 3px double #1e3a8a;">
          <div style="text-align: center; border-bottom: 2px solid #1e3a8a; padding-bottom: 15px; margin-bottom: 25px;">
            <p style="font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #1e3a8a; margin: 0;">GOVERNMENT OF INDIA</p>
            <p style="font-size: 11px; font-weight: bold; margin: 3px 0; color: #334155;">MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION</p>
            <h2 style="font-size: 16px; font-weight: bold; margin: 5px 0; color: #0f172a;">DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION</h2>
            <p style="font-size: 11px; font-style: italic; color: #64748b; margin: 0;">Issued under the Legal Metrology (Packaged Commodities) Rules, 2011</p>
          </div>

          <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="font-size: 18px; font-weight: bold; color: #065f46; text-transform: uppercase; margin-bottom: 5px;">
              STATUTORY COMPLIANCE CERTIFICATE & COMMERCIAL CLEARANCE
            </h1>
            <p style="font-size: 12px; font-weight: bold; color: #475569;">Certificate Ref No: <u>${docNo}</u> | Date: ${dateStr}</p>
          </div>

          <p style="font-size: 13px; leading-height: 1.6; text-align: justify;">
            This is to certify that the pre-packaged commodity specified below has been inspected using automated Multimodal Vision AI verification under Section 15 of the Legal Metrology Act, 2009, and evaluated against the statutory requirements of Rule 6(1), Rule 7, and Rule 11 of the Legal Metrology (Packaged Commodities) Rules, 2011.
          </p>

          <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 12px;">
            <tr style="background: #f8fafc;"><td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: bold;">Inspection Ref No</td><td style="padding: 8px; border: 1px solid #cbd5e1;">${inspectionNumber}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: bold;">Commodity Name</td><td style="padding: 8px; border: 1px solid #cbd5e1;">${productName}</td></tr>
            <tr style="background: #f8fafc;"><td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: bold;">Manufacturer / Packer</td><td style="padding: 8px; border: 1px solid #cbd5e1;">${companyName}</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: bold;">Compliance Score</td><td style="padding: 8px; border: 1px solid #cbd5e1; font-weight: bold; color: #065f46;">${complianceResult.complianceScore}% (FULLY COMPLIANT)</td></tr>
          </table>

          <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 15px; border-radius: 8px; margin: 25px 0;">
            <p style="margin: 0; font-size: 12px; color: #065f46; font-weight: bold; text-align: center;">
              COMMERCIAL CLEARANCE GRANTED FOR RETAIL DISTRIBUTION ACROSS INDIA
            </p>
          </div>

          <div style="margin-top: 50px; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
              <p style="font-size: 11px; color: #64748b; margin: 0;">Verified by: Legal Metrology AI Engine v3.8</p>
              <p style="font-size: 11px; color: #64748b; margin: 0;">Digital Signature Hash: 0x8F92...B41C</p>
            </div>
            <div style="text-align: center;">
              <div style="border-bottom: 1px solid #000; width: 180px; margin-bottom: 5px;"></div>
              <p style="font-size: 12px; font-weight: bold; margin: 0;">Authorized Inspector</p>
              <p style="font-size: 10px; color: #475569; margin: 0;">Legal Metrology Department, Govt. of India</p>
            </div>
          </div>
        </div>
      `
    };
  }

  // Generate Formal SHOW-CAUSE NOTICE & SEIZURE MEMORANDUM for Violations
  const violationsListHtml = complianceResult.violations.map((v, i) => `
    <tr style="background: ${i % 2 === 0 ? '#fff' : '#fff1f2'};">
      <td style="padding: 8px; border: 1px solid #fca5a5; font-weight: bold; text-align: center;">${i + 1}</td>
      <td style="padding: 8px; border: 1px solid #fca5a5; font-weight: bold; color: #991b1b;">${v.statutorySection}</td>
      <td style="padding: 8px; border: 1px solid #fca5a5;">${v.title}<br/><small style="color: #475569;">${v.description}</small></td>
      <td style="padding: 8px; border: 1px solid #fca5a5; font-weight: bold; color: #991b1b;">${v.observedValue}</td>
    </tr>
  `).join("");

  return {
    documentType: "SHOW_CAUSE_NOTICE",
    title: "FORMAL SHOW-CAUSE NOTICE & SEIZURE MEMORANDUM UNDER SECTIONS 15, 36(1) & 51 OF LEGAL METROLOGY ACT, 2009",
    documentNumber: docNo,
    htmlContent: `
      <div style="font-family: 'Times New Roman', serif; padding: 35px; color: #111827; max-width: 820px; margin: auto; border: 3px double #991b1b;">
        <div style="text-align: center; border-bottom: 2px solid #991b1b; padding-bottom: 12px; margin-bottom: 20px;">
          <p style="font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #991b1b; margin: 0;">GOVERNMENT OF INDIA</p>
          <p style="font-size: 11px; font-weight: bold; margin: 2px 0; color: #1e293b;">MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION</p>
          <h2 style="font-size: 15px; font-weight: bold; margin: 4px 0; color: #0f172a;">DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY ENFORCEMENT DIVISION</h2>
          <p style="font-size: 10px; font-style: italic; color: #64748b; margin: 0;">Issued under Sections 15, 36(1) and 51 of the Legal Metrology Act, 2009</p>
        </div>

        <div style="text-align: center; margin-bottom: 20px;">
          <h1 style="font-size: 16px; font-weight: bold; color: #991b1b; text-transform: uppercase; margin-bottom: 4px;">
            FORMAL SHOW-CAUSE NOTICE & SEIZURE MEMORANDUM
          </h1>
          <p style="font-size: 11px; font-weight: bold; color: #374151;">Notice Ref No: <u>${docNo}</u> | Issued Date: ${dateStr}</p>
        </div>

        <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 10px 14px; margin-bottom: 18px;">
          <p style="font-size: 11px; margin: 0;"><strong>To Offender / Manufacturer:</strong> ${companyName}</p>
          <p style="font-size: 11px; margin: 2px 0 0 0;"><strong>Inspected Commodity:</strong> ${productName} (Inspection Ref: ${inspectionNumber})</p>
          <p style="font-size: 11px; margin: 2px 0 0 0; color: #991b1b;"><strong>Overall Compliance Status:</strong> NON-COMPLIANT (Score: ${complianceResult.complianceScore}%)</p>
        </div>

        <p style="font-size: 12px; leading-height: 1.5; text-align: justify;">
          WHEREAS an inspection of the pre-packaged commodity <strong>"${productName}"</strong> manufactured/packed/imported by you was conducted under Section 15 of the Legal Metrology Act, 2009. Automated optical inspection and rule verification established the following statutory violations:
        </p>

        <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 11px;">
          <thead>
            <tr style="background: #fee2e2; color: #991b1b;">
              <th style="padding: 6px; border: 1px solid #fca5a5;">#</th>
              <th style="padding: 6px; border: 1px solid #fca5a5;">Statutory Provision</th>
              <th style="padding: 6px; border: 1px solid #fca5a5;">Nature of Violation</th>
              <th style="padding: 6px; border: 1px solid #fca5a5;">Observed Defect</th>
            </tr>
          </thead>
          <tbody>
            ${violationsListHtml}
          </tbody>
        </table>

        <div style="border: 1px solid #dc2626; background: #fff5f5; padding: 12px; margin: 18px 0; font-size: 11px;">
          <h4 style="margin: 0 0 6px 0; color: #991b1b; text-transform: uppercase;">Statutory Penalty Matrix — Section 36(1) Legal Metrology Act, 2009</h4>
          <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
            <li><strong>First Offence:</strong> Fine extending up to <strong>₹25,000</strong> (Rupees Twenty-Five Thousand).</li>
            <li><strong>Second Offence:</strong> Fine extending up to <strong>₹50,000</strong> (Rupees Fifty Thousand).</li>
            <li><strong>Subsequent Offences:</strong> Fine up to <strong>₹1,00,000</strong> or <strong>Imprisonment up to 1 Year</strong>, or both.</li>
          </ul>
        </div>

        <p style="font-size: 12px; font-weight: bold; color: #991b1b; leading-height: 1.5; text-align: justify;">
          NOW THEREFORE, take notice that you are hereby directed to SHOW CAUSE in writing within <u>SEVEN (7) DAYS</u> from the date of receipt of this notice why prosecution proceedings under Section 36(1) of the Legal Metrology Act, 2009 should not be initiated against your firm. Failure to respond within 7 days shall result in immediate seizure of non-compliant stock and filing of formal court complaint.
        </p>

        <div style="margin-top: 40px; display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <p style="font-size: 10px; color: #64748b; margin: 0;">Evidence Hash: 0x9D42...F881</p>
            <p style="font-size: 10px; color: #64748b; margin: 0;">Generated by DoCA Enforcement System SIH 26034</p>
          </div>
          <div style="text-align: center;">
            <div style="border-bottom: 1px solid #000; width: 190px; margin-bottom: 4px;"></div>
            <p style="font-size: 11px; font-weight: bold; margin: 0;">Enforcement Officer / Inspector</p>
            <p style="font-size: 10px; color: #475569; margin: 0;">Legal Metrology Department, Govt. of India</p>
          </div>
        </div>
      </div>
    `
  };
}
