document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const dropzoneText = document.getElementById("dropzoneText");
  const categorySelect = document.getElementById("categorySelect");
  const inspectBtn = document.getElementById("inspectBtn");
  const sampleItems = document.querySelectorAll(".sample-item");

  const spinnerOverlay = document.getElementById("spinnerOverlay");
  const spinnerText = document.getElementById("spinnerText");
  const spinnerSubtext = document.getElementById("spinnerSubtext");

  const scorecardBanner = document.getElementById("scorecardBanner");
  const statusPill = document.getElementById("statusPill");
  const scoreNumber = document.getElementById("scoreNumber");
  const statChecked = document.getElementById("statChecked");
  const statCompliant = document.getElementById("statCompliant");
  const statViolations = document.getElementById("statViolations");

  const infoManufacturer = document.getElementById("infoManufacturer");
  const infoCommodity = document.getElementById("infoCommodity");
  const infoQtyMrp = document.getElementById("infoQtyMrp");
  const infoPdpArea = document.getElementById("infoPdpArea");

  const originalImg = document.getElementById("originalImg");
  const annotatedImg = document.getElementById("annotatedImg");

  const violationsTableBody = document.getElementById("violationsTableBody");
  const generateNoticeBtn = document.getElementById("generateNoticeBtn");
  const exportJsonBtn = document.getElementById("exportJsonBtn");

  const noticeModal = document.getElementById("noticeModal");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const modalCloseAction = document.getElementById("modalCloseAction");
  const pdfFrame = document.getElementById("pdfFrame");
  const downloadPdfLink = document.getElementById("downloadPdfLink");

  // State
  let selectedFile = null;
  let selectedSampleId = null; // No auto-selected sample
  let currentInspectionReport = null;

  // Dropzone Interaction
  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  function handleFileSelection(file) {
    selectedFile = file;
    selectedSampleId = null;
    dropzoneText.textContent = `Selected: ${file.name}`;
    // Highlight none of the samples
    sampleItems.forEach(item => item.style.borderColor = "var(--border-color)");

    // Show image preview in original scan viewer
    const reader = new FileReader();
    reader.onload = (e) => {
      originalImg.src = e.target.result;
      originalImg.style.display = "block";
      const origEmpty = document.getElementById("originalEmptyState");
      if (origEmpty) origEmpty.style.display = "none";
    };
    reader.readAsDataURL(file);

    // Reset annotated view to awaiting state
    annotatedImg.style.display = "none";
    const annEmpty = document.getElementById("annotatedEmptyState");
    if (annEmpty) annEmpty.style.display = "flex";

    // Update status
    statusPill.className = "status-pill";
    statusPill.textContent = "READY FOR INSPECTION";
    infoManufacturer.textContent = `Uploaded scan: ${file.name}`;
  }

  // Sample items selection - ONLY SELECTS, DOES NOT AUTO-RUN INSPECTION
  sampleItems.forEach((item) => {
    item.addEventListener("click", () => {
      selectedSampleId = item.getAttribute("data-id");
      selectedFile = null;
      fileInput.value = "";
      const sampleName = item.querySelector("h4").textContent;
      dropzoneText.textContent = `Selected: ${sampleName}`;

      sampleItems.forEach(i => i.style.borderColor = "var(--border-color)");
      item.style.borderColor = "var(--accent-blue)";

      // Auto-set category if sample has specific category
      if (selectedSampleId === "sample_garment") {
        categorySelect.value = "GARMENTS";
      } else if (selectedSampleId.includes("food") || selectedSampleId.includes("compliant")) {
        categorySelect.value = "FOOD_SNACKS";
      } else {
        categorySelect.value = "UNIVERSAL";
      }

      // Show sample preview in original viewer WITHOUT running inspection
      const thumb = item.querySelector("img");
      if (thumb) {
        originalImg.src = thumb.src;
        originalImg.style.display = "block";
        const origEmpty = document.getElementById("originalEmptyState");
        if (origEmpty) origEmpty.style.display = "none";
      }

      // Reset annotated viewer to awaiting state
      annotatedImg.style.display = "none";
      const annEmpty = document.getElementById("annotatedEmptyState");
      if (annEmpty) annEmpty.style.display = "flex";

      statusPill.className = "status-pill";
      statusPill.textContent = "READY FOR INSPECTION";
      infoManufacturer.textContent = `Selected Sample: ${sampleName} (Click "Run Statutory Inspection")`;
    });
  });

  // Run Inspection Action - ONLY TRIGGERED ON BUTTON CLICK
  inspectBtn.addEventListener("click", () => {
    if (!selectedFile && !selectedSampleId) {
      alert("Please upload a packaging photo or select a preloaded sample first.");
      return;
    }
    runInspection();
  });

  async function runInspection() {
    showSpinner(true, "Executing Statutory Packaging Audit...", "Detecting PDP Area • Calibrating Scale • Running Multimodal OCR • Cross-Examining Legal KB");

    const formData = new FormData();
    formData.append("category", categorySelect.value);

    if (selectedFile) {
      formData.append("file", selectedFile);
    } else if (selectedSampleId) {
      formData.append("sample_id", selectedSampleId);
    } else {
      showSpinner(false);
      alert("Please upload a packaging photo or select a preloaded sample.");
      return;
    }

    try {
      const response = await fetch("/api/inspect", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Inspection failed with HTTP ${response.status}`);
      }

      const report = await response.json();
      currentInspectionReport = report;
      renderReport(report);
    } catch (err) {
      console.error(err);
      alert(`Inspection Error: ${err.message}`);
    } finally {
      showSpinner(false);
    }
  }

  function renderReport(report) {
    const isCompliant = report.is_compliant;
    const score = Math.round(report.compliance_score);
    const violations = report.violations || [];
    const summary = report.summary || {};

    // 1. Scorecard Banner
    scorecardBanner.className = `scorecard-banner ${isCompliant ? 'pass' : 'fail'}`;
    statusPill.className = `status-pill ${isCompliant ? 'pass' : 'fail'}`;
    statusPill.textContent = isCompliant ? "100% STATUTORY PASS" : "NON-COMPLIANT / SEIZURE DIRECTIVE";

    scoreNumber.textContent = score;
    statChecked.textContent = summary.total_mandatory_fields_checked || (report.compliant_fields.length + violations.length);
    statCompliant.textContent = summary.compliant_fields_count || report.compliant_fields.length;
    statViolations.textContent = violations.length;

    // 2. Offender Details Strip
    const entity = report.entity_info || {};
    infoManufacturer.textContent = entity.manufacturer_name_address || "Undisclosed on packaging";
    infoCommodity.textContent = entity.commodity_name || "Pre-Packaged Commodity";
    infoQtyMrp.textContent = `${entity.net_quantity || 'N/A'} | ${entity.mrp || 'N/A'}`;

    const pdp = report.pdp_summary || {};
    const font = report.font_verification || {};
    const pdpAreaStr = pdp.pdp_area_cm2 ? `${pdp.pdp_area_cm2} cm²` : "N/A";
    const fontStr = font.measured_font_height_mm ? `${font.measured_font_height_mm}mm (Min: ${font.statutory_min_height_mm}mm)` : "Calibrated";
    infoPdpArea.textContent = `${pdpAreaStr} | Font: ${fontStr}`;

    // 3. Side-by-Side Viewer Images
    const artifacts = report.artifacts || {};
    if (artifacts.original_image_url) {
      originalImg.src = `${artifacts.original_image_url}?t=${Date.now()}`;
      originalImg.style.display = "block";
      const origEmpty = document.getElementById("originalEmptyState");
      if (origEmpty) origEmpty.style.display = "none";
    }
    if (artifacts.annotated_image_url) {
      annotatedImg.src = `${artifacts.annotated_image_url}?t=${Date.now()}`;
      annotatedImg.style.display = "block";
      const annEmpty = document.getElementById("annotatedEmptyState");
      if (annEmpty) annEmpty.style.display = "none";
    }

    // 4. Violations Table
    violationsTableBody.innerHTML = "";
    if (violations.length === 0) {
      violationsTableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: #047857; background-color: #ecfdf5; padding: 2rem;">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">✓</div>
            <b>100% COMPLIANT PRE-PACKAGED COMMODITY</b><br/>
            <span style="font-size: 0.85rem; color: #065f46;">All mandatory statutory declarations, legal SI unit symbols, MRP tax phrases, and numeral font height thresholds are verified under the Legal Metrology (Packaged Commodities) Rules, 2011.</span>
          </td>
        </tr>
      `;
      generateNoticeBtn.textContent = "📄 Generate Compliance Certificate (PDF)";
    } else {
      generateNoticeBtn.textContent = "📄 Generate Official Legal Notice (PDF)";
      violations.forEach((v, index) => {
        const tr = document.createElement("tr");
        const sevClass = (v.severity || "MAJOR").toLowerCase();

        tr.innerHTML = `
          <td><b>${index + 1}</b></td>
          <td><b>${v.field || 'General'}</b><br/><span style="color: #64748b; font-size: 0.75rem;">${v.title || ''}</span></td>
          <td><b>${v.clause || 'PCR 2011'}</b><br/><span style="color: #475569; font-size: 0.75rem;">${v.legal_citation || ''}</span></td>
          <td>
            <div style="color: #0f172a; margin-bottom: 0.25rem;">${v.description || v.issue || ''}</div>
            <div style="color: #15803D; font-size: 0.75rem;"><b>Prescribed Remedy:</b> ${v.remedy || v.statutory_ref || 'Rectify packaging declaration to conform to statutory standards.'}</div>
          </td>
          <td><span class="severity-pill ${sevClass}">${v.severity || 'MAJOR'}</span></td>
        `;
        violationsTableBody.appendChild(tr);
      });
    }

    generateNoticeBtn.disabled = false;
    exportJsonBtn.disabled = false;
  }

  // Generate Official Legal Notice Action
  generateNoticeBtn.addEventListener("click", async () => {
    if (!currentInspectionReport) {
      alert("Please run an inspection first before generating the official document.");
      return;
    }

    const openTabLink = document.getElementById("openNewTabLink");

    // 1. If notice was already pre-generated in inspect response, open instantly
    if (currentInspectionReport.notice && currentInspectionReport.notice.notice_url) {
      const noticeUrl = currentInspectionReport.notice.notice_url;
      const filename = currentInspectionReport.notice.notice_filename || "Official_Notice.pdf";
      pdfFrame.src = `${noticeUrl}?t=${Date.now()}`;
      downloadPdfLink.href = noticeUrl;
      downloadPdfLink.setAttribute("download", filename);
      if (openTabLink) openTabLink.href = noticeUrl;
      openModal();
      return;
    }

    // 2. Otherwise request generation via API
    showSpinner(true, "Generating Official Court-Ready Notice PDF...", "Formatting Statutory Sections • Embedding Visual Evidence Scan • Signing Document");

    try {
      const response = await fetch("/api/generate_notice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          inspection_report: currentInspectionReport
        })
      });

      if (!response.ok) {
        throw new Error("Failed to generate legal notice PDF");
      }

      const noticeData = await response.json();
      currentInspectionReport.notice = noticeData;
      
      // Load PDF into modal frame
      pdfFrame.src = `${noticeData.notice_url}?t=${Date.now()}`;
      downloadPdfLink.href = noticeData.notice_url;
      downloadPdfLink.setAttribute("download", noticeData.notice_filename);
      if (openTabLink) openTabLink.href = noticeData.notice_url;

      openModal();
    } catch (err) {
      console.warn("Direct POST failed, opening latest generated notice directly:", err);
      // Fail-safe fallback: open direct download URL
      const fallbackUrl = "/api/download_latest_notice";
      downloadPdfLink.href = fallbackUrl;
      if (openTabLink) openTabLink.href = fallbackUrl;
      pdfFrame.src = `${fallbackUrl}?t=${Date.now()}`;
      openModal();
    } finally {
      showSpinner(false);
    }
  });

  // Export JSON Report
  exportJsonBtn.addEventListener("click", () => {
    if (!currentInspectionReport) return;
    const blob = new Blob([JSON.stringify(currentInspectionReport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Inspection_Audit_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // Modal handlers
  function openModal() {
    noticeModal.classList.add("active");
  }

  function closeModal() {
    noticeModal.classList.remove("active");
    pdfFrame.src = "about:blank";
  }

  closeModalBtn.addEventListener("click", closeModal);
  modalCloseAction.addEventListener("click", closeModal);
  noticeModal.addEventListener("click", (e) => {
    if (e.target === noticeModal) closeModal();
  });

  function showSpinner(show, text = "Loading...", subtext = "") {
    if (show) {
      spinnerText.textContent = text;
      spinnerSubtext.textContent = subtext;
      spinnerOverlay.classList.add("active");
    } else {
      spinnerOverlay.classList.remove("active");
    }
  }
});
