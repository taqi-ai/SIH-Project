"use client";
import { useEffect, useState } from "react";
import { fetchAuthedBlob } from "@/lib/api";

export function DocumentViewer({ documentId, page }: { documentId: string; page?: number | null }) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    setUrl(null);
    setError(null);
    fetchAuthedBlob(`/documents/${documentId}/file`)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => setError("Unable to load document file."));
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [documentId]);

  if (error) return <div className="p-6 text-sm text-status-failed">{error}</div>;
  if (!url) return <div className="p-6 text-sm text-slate-400">Loading document…</div>;

  return (
    <iframe
      src={`${url}${page ? `#page=${page}` : ""}`}
      title="Document preview"
      className="w-full h-full min-h-[500px] border-0"
    />
  );
}
