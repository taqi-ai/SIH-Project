"use client";
import { useState } from "react";
import { DocumentViewer } from "./DocumentViewer";

export interface EvidenceChainStep {
  label: string;
  value: string;
}

export function EvidencePanel({
  open, onClose, title, chain, documentId, page, comparedDocumentId, comparedPage,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  chain: EvidenceChainStep[];
  documentId: string | null;
  page?: number | null;
  comparedDocumentId?: string | null;
  comparedPage?: number | null;
}) {
  const [showCompared, setShowCompared] = useState(false);
  if (!open) return null;

  const activeDoc = showCompared ? comparedDocumentId : documentId;
  const activePage = showCompared ? comparedPage : page;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30">
      <div className="w-full max-w-4xl bg-white h-full shadow-panel flex">
        <div className="w-[340px] shrink-0 border-r border-slate-100 flex flex-col">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink-900">Evidence</h3>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-lg leading-none">×</button>
          </div>
          <div className="px-5 py-4 overflow-y-auto flex-1">
            <div className="text-sm font-medium text-ink-900 mb-3">{title}</div>
            <ol className="space-y-3">
              {chain.map((step, i) => (
                <li key={i} className="relative pl-5">
                  <span className="absolute left-0 top-1 w-2 h-2 rounded-full bg-brand-500" />
                  {i < chain.length - 1 && <span className="absolute left-[3px] top-3 bottom-[-14px] w-px bg-slate-200" />}
                  <div className="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">{step.label}</div>
                  <div className="text-sm text-ink-800 mt-0.5 break-words">{step.value}</div>
                </li>
              ))}
            </ol>
            {comparedDocumentId && (
              <div className="mt-5 pt-4 border-t border-slate-100 flex gap-2">
                <button
                  className={`text-xs px-2.5 py-1.5 rounded border ${!showCompared ? "bg-ink-900 text-white border-ink-900" : "border-slate-300 text-slate-600"}`}
                  onClick={() => setShowCompared(false)}
                >
                  Document A
                </button>
                <button
                  className={`text-xs px-2.5 py-1.5 rounded border ${showCompared ? "bg-ink-900 text-white border-ink-900" : "border-slate-300 text-slate-600"}`}
                  onClick={() => setShowCompared(true)}
                >
                  Document B
                </button>
              </div>
            )}
          </div>
        </div>
        <div className="flex-1 bg-slate-50">
          {activeDoc ? (
            <DocumentViewer documentId={activeDoc} page={activePage} />
          ) : (
            <div className="p-6 text-sm text-slate-400">No source document available — this requirement is verified via an external sandbox connector rather than an uploaded document.</div>
          )}
        </div>
      </div>
    </div>
  );
}
