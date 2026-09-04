"use client";
import { useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { docTypeLabel } from "@/lib/format";

const DOCUMENT_TYPES = [
  "UDYAM_CERTIFICATE", "GST_CERTIFICATE", "PAN_CARD", "INCOME_TAX_RETURN", "MII_DECLARATION",
  "EPFO_CERTIFICATE", "ESIC_CERTIFICATE", "STARTUP_INDIA_CERTIFICATE", "NSIC_CERTIFICATE",
  "OEM_AUTHORIZATION", "AFFIDAVIT", "FINANCIAL_STATEMENT", "TURNOVER_DECLARATION", "TENDER_SPECIFIC", "OTHER",
];

export function UploadPanel({ bidId, onUploaded }: { bidId: string; onUploaded: () => void }) {
  const [documentType, setDocumentType] = useState("GST_CERTIFICATE");
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function upload(file: File) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("document_type", documentType);
      form.append("file", file);
      await api.postForm(`/bids/${bidId}/documents`, form);
      onUploaded();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel p-5 sticky top-6">
      <h2 className="text-sm font-semibold text-ink-900 mb-3">Upload Bidder Document</h2>
      <label className="label-sm block mb-1">Document Type</label>
      <select className="input mb-3" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
        {DOCUMENT_TYPES.map((t) => <option key={t} value={t}>{docTypeLabel(t)}</option>)}
      </select>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) upload(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={`rounded-md border-2 border-dashed p-8 text-center cursor-pointer transition-colors ${
          dragging ? "border-ink-600 bg-slate-50" : "border-slate-300 hover:border-slate-400"
        }`}
      >
        <div className="text-sm text-slate-600">{busy ? "Uploading…" : "Drag & drop a PDF, or click to browse"}</div>
        <div className="text-xs text-slate-400 mt-1">PDF, PNG, JPEG · up to 15MB</div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,image/png,image/jpeg"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload(file);
            e.target.value = "";
          }}
        />
      </div>
      {error && <div className="mt-3 text-xs text-status-failed bg-status-failedBg rounded px-3 py-2">{error}</div>}
      <p className="mt-3 text-[11px] text-slate-400 leading-relaxed">
        After upload, click <span className="font-medium">Process</span> on the document to run OCR, AI field
        extraction and validation.
      </p>
    </div>
  );
}
