import { useState, useRef } from "react";
import {
  Camera,
  CheckCircle2,
  FileImage,
  ImagePlus,
  LoaderCircle,
  ShieldCheck,
  UploadCloud,
  Trash2,
  X
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { inspectPackageApi } from "../services/apiClient";
import { LiveCameraScanner } from "../components/common/LiveCameraScanner";

export function NewInspectionPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [productName, setProductName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [processing, setProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleSelectedFiles = (newFiles: File[]) => {
    const validImages = newFiles.filter((file) =>
      file.type.startsWith("image/") ||
      /\.(jpg|jpeg|png|webp|bmp|tiff)$/i.test(file.name)
    );
    if (validImages.length > 0) {
      setFiles((prev) => [...prev, ...validImages]);
    }
  };

  const onFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    handleSelectedFiles(selectedFiles);
    // Reset file input value so same file can be chosen again if needed
    if (event.target) event.target.value = "";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      handleSelectedFiles(droppedFiles);
    }
  };

  const handleCameraCapture = (capturedFile: File) => {
    setFiles((prev) => [...prev, capturedFile]);
  };

  const removeFile = (indexToRemove: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  const start = async () => {
    if (!productName.trim() || !companyName.trim() || files.length === 0) {
      return;
    }

    setProcessing(true);
    setStatusMessage("Uploading packaging scans & invoking Multimodal Vision AI...");

    try {
      await inspectPackageApi(productName, companyName, files);
      navigate("/inspections/demo/review");
    } catch (err) {
      console.error("Inspection processing error:", err);
      navigate("/inspections/demo/review");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="page-title">New Product Packaging Inspection</h1>

        <p className="page-description">
          Enter commodity details and upload packaging label images (via drag & drop, file selection, or live field camera) to execute AI compliance verification.
        </p>
      </div>

      {/* Product details section */}
      <section className="app-card p-6">
        <div className="mb-5">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            Product & Entity Details
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Provide the commodity name and manufacturer/importer details before uploading packaging label scans.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label
              htmlFor="productName"
              className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-300"
            >
              Product Name / Commodity
            </label>

            <input
              id="productName"
              name="productName"
              type="text"
              value={productName}
              onChange={(event) => setProductName(event.target.value)}
              placeholder="Example: Herbal Shampoo 180 ml"
              className="form-input"
              required
            />

            <p className="mt-1.5 text-xs text-slate-500">
              Enter the commodity name as printed on the front Principal Display Panel (PDP).
            </p>
          </div>

          <div>
            <label
              htmlFor="companyName"
              className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-300"
            >
              Company / Manufacturer Name
            </label>

            <input
              id="companyName"
              name="companyName"
              type="text"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              placeholder="Example: GreenCare Pvt. Ltd."
              className="form-input"
              required
            />

            <p className="mt-1.5 text-xs text-slate-500">
              Enter the manufacturer, packer, or importer name registered under Legal Metrology Rules.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Upload section */}
        <section className="app-card p-6 lg:col-span-3">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-blue-50 dark:bg-blue-950 p-3 text-blue-600 dark:text-blue-400">
                <ImagePlus className="h-6 w-6" />
              </div>

              <div>
                <h2 className="font-semibold text-slate-900 dark:text-white">
                  Packaging Image Upload & Capture
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Drag & drop saved image files (.jpg, .jpeg, .png, .webp) or capture live with camera.
                </p>
              </div>
            </div>
          </div>

          {/* Interactive Drag & Drop Box */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
              isDragging
                ? "border-blue-500 bg-blue-100/60 scale-[1.01]"
                : "border-blue-200 dark:border-slate-700 bg-blue-50/40 dark:bg-slate-800/40 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-slate-800"
            }`}
          >
            <div className="p-4 bg-white dark:bg-slate-800 rounded-full shadow-sm mb-3">
              <UploadCloud className="h-8 w-8 text-blue-600 dark:text-blue-400 animate-bounce" />
            </div>

            <p className="text-base font-bold text-slate-900 dark:text-white">
              Drag & Drop package image files here
            </p>

            <p className="mt-1.5 max-w-md text-xs leading-5 text-slate-500">
              Supports <span className="font-semibold text-slate-700 dark:text-slate-300">JPG, JPEG, PNG, WEBP, BMP</span> packaging photos. Ensure MRP, net quantity, mfg date, and manufacturer address are clearly visible.
            </p>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-3" onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 shadow-md active:scale-95"
              >
                <UploadCloud className="h-4 w-4" /> Select Images from Device
              </button>

              <button
                type="button"
                onClick={() => setIsCameraOpen(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 dark:bg-slate-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 dark:hover:bg-slate-600 shadow-md active:scale-95"
              >
                <Camera className="h-4 w-4 text-amber-400" /> Live Field Camera Scan
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/webp,image/bmp"
              multiple
              className="hidden"
              onChange={onFileInputChange}
            />
          </div>

          <LiveCameraScanner
            isOpen={isCameraOpen}
            onClose={() => setIsCameraOpen(false)}
            onCapture={handleCameraCapture}
          />

          {/* Selected Files List & Thumbnail Previews */}
          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-slate-500 uppercase tracking-wider">
                <span>Selected Packaging Files ({files.length})</span>
                <button
                  type="button"
                  onClick={() => setFiles([])}
                  className="text-rose-600 hover:underline text-xs flex items-center gap-1 font-semibold"
                >
                  Clear All
                </button>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {files.map((file, index) => {
                  const objectUrl = URL.createObjectURL(file);
                  return (
                    <div
                      key={`${file.name}-${index}`}
                      className="relative flex items-center gap-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2.5 shadow-sm group hover:border-blue-400"
                    >
                      <img
                        src={objectUrl}
                        alt={file.name}
                        className="h-12 w-12 rounded-lg object-cover border border-slate-200 dark:border-slate-700 bg-slate-200"
                      />

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-bold text-slate-900 dark:text-white">
                          {file.name}
                        </p>

                        <p className="mt-0.5 text-[11px] text-slate-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950 transition-colors"
                        title="Remove image"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>

        {/* Instructions section */}
        <aside className="app-card h-fit p-6 lg:col-span-2 space-y-6">
          <div className="flex gap-3">
            <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950 p-3 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-6 w-6" />
            </div>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Statutory Scan Requirements
              </h2>

              <ul className="mt-3 space-y-2.5 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  Ensure MRP, Net Quantity & Unit symbols are un-blurred.
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  Capture the Principal Display Panel (PDP) front surface.
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  Upload close-ups for consumer care address and tax disclosures.
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                  Both file drop and live field camera capture are supported.
                </li>
              </ul>
            </div>
          </div>

          <button
            onClick={start}
            disabled={
              !productName.trim() ||
              !companyName.trim() ||
              files.length === 0 ||
              processing
            }
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 transition-all shadow-md active:scale-95 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700"
          >
            {processing && (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            )}

            {processing
              ? "Running Multimodal AI Inspection..."
              : "Start AI Packaging Inspection"}
          </button>

          {(!productName.trim() ||
            !companyName.trim() ||
            files.length === 0) && (
            <p className="text-center text-xs text-slate-500">
              Enter product details and select/drag at least one packaging image (.jpg, .jpeg, .png) to continue.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
