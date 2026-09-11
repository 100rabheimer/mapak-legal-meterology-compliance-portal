import React, { useRef, useState, useEffect } from "react";
import { Camera, RefreshCw, X, Check, Flashlight, ScanLine, ShieldCheck } from "lucide-react";

interface LiveCameraScannerProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (capturedFile: File) => void;
}

export function LiveCameraScanner({ isOpen, onClose, onCapture }: LiveCameraScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isOpen]);

  const startCamera = async () => {
    setErrorMsg(null);
    setCapturedBlob(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err: any) {
      console.error("Camera access error:", err);
      setErrorMsg("Camera access denied or unavailable. Please check permissions.");
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setCameraActive(false);
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
      setCapturedBlob(dataUrl);

      canvas.toBlob(
        (blob) => {
          if (blob) {
            const capturedFile = new File([blob], `camera_scan_${Date.now()}.jpg`, {
              type: "image/jpeg",
              lastModified: Date.now(),
            });
            onCapture(capturedFile);
          }
        },
        "image/jpeg",
        0.92
      );
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl bg-slate-900 shadow-2xl text-white border border-slate-800">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600/20 p-2.5 text-blue-400 border border-blue-500/30">
              <ScanLine className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Live Field Enforcement OCR Viewfinder</h3>
              <p className="text-xs text-slate-400">Position package PDP inside yellow reticle guide</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-full bg-slate-800 p-2 text-slate-400 transition hover:bg-slate-700 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Viewfinder Canvas / Video Area */}
        <div className="relative aspect-[4/3] w-full bg-black overflow-hidden flex items-center justify-center">
          {errorMsg ? (
            <div className="p-8 text-center text-rose-400">
              <p className="text-sm font-semibold">{errorMsg}</p>
              <button
                onClick={startCamera}
                className="mt-4 rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700"
              >
                Retry Camera Access
              </button>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                playsInline
                muted
                className={`h-full w-full object-cover ${capturedBlob ? "hidden" : "block"}`}
              />

              {capturedBlob && (
                <img src={capturedBlob} alt="Captured scan" className="h-full w-full object-cover" />
              )}

              <canvas ref={canvasRef} className="hidden" />

              {/* Reticle / Target Guide Bounding Box */}
              {!capturedBlob && cameraActive && (
                <div className="pointer-events-none absolute inset-12 rounded-2xl border-2 border-dashed border-amber-400/80 shadow-[0_0_0_9999px_rgba(15,23,42,0.65)] flex flex-col justify-between p-4">
                  <div className="flex justify-between text-[10px] uppercase tracking-wider text-amber-300 font-bold bg-slate-900/70 px-2.5 py-1 rounded-md max-w-fit">
                    <ShieldCheck className="h-3.5 w-3.5 mr-1" /> Legal Metrology PDP Scan Target
                  </div>
                  <div className="text-center text-xs text-amber-200/90 font-medium bg-slate-900/70 px-3 py-1.5 rounded-lg">
                    Align Net Qty, MRP, & Manufacturer Details
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center justify-between border-t border-slate-800 p-5 bg-slate-900/90">
          {capturedBlob ? (
            <div className="flex w-full items-center justify-between gap-4">
              <button
                onClick={() => setCapturedBlob(null)}
                className="flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2.5 text-sm font-semibold text-slate-200 transition hover:bg-slate-700"
              >
                <RefreshCw className="h-4 w-4" /> Retake Photo
              </button>

              <button
                onClick={onClose}
                className="flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 shadow-lg shadow-emerald-900/30"
              >
                <Check className="h-4 w-4" /> Use Captured Frame
              </button>
            </div>
          ) : (
            <div className="flex w-full items-center justify-between">
              <p className="text-xs text-slate-400">Resolution: 1080p High-Precision Target</p>

              <button
                onClick={captureFrame}
                disabled={!cameraActive}
                className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-3 text-sm font-bold text-white shadow-xl shadow-blue-900/40 transition hover:scale-105 active:scale-95 disabled:opacity-50"
              >
                <Camera className="h-5 w-5" /> Capture Frame
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
