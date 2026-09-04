"use client";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

type Target = { kind: "finding"; id: string } | { kind: "evaluation"; id: string };

const ACTIONS_FINDING = [
  { value: "ACCEPT_FINDING", label: "Accept Finding" },
  { value: "REJECT_FINDING", label: "Reject Finding" },
  { value: "REQUEST_CLARIFICATION", label: "Request Clarification" },
  { value: "OVERRIDE", label: "Override AI Recommendation" },
];

const ACTIONS_EVAL = [
  { value: "MARK_VERIFIED", label: "Mark Requirement Verified" },
  { value: "MARK_FAILED", label: "Mark Requirement Failed" },
  { value: "OVERRIDE", label: "Override Requirement Status" },
];

export function ReviewModal({ target, title, onClose, onDone }: { target: Target; title: string; onClose: () => void; onDone: () => void }) {
  const options = target.kind === "finding" ? ACTIONS_FINDING : ACTIONS_EVAL;
  const [action, setAction] = useState(options[0].value);
  const [comment, setComment] = useState("");
  const [justification, setJustification] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const requiresJustification = action === "OVERRIDE";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const path = target.kind === "finding" ? `/findings/${target.id}/review` : `/evaluations/${target.id}/review`;
      await api.post(path, { action, comment: comment || null, justification: justification || null });
      onDone();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Review failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[60] p-4">
      <form onSubmit={submit} className="bg-white rounded-lg shadow-panel w-full max-w-md p-6">
        <h2 className="text-base font-semibold text-ink-900 mb-1">Officer Review</h2>
        <p className="text-xs text-slate-500 mb-4">{title}</p>
        {error && <div className="mb-3 text-sm text-status-failed bg-status-failedBg rounded px-3 py-2">{error}</div>}
        <div className="space-y-3">
          <div>
            <label className="label-sm block mb-1">Action</label>
            <select className="input" value={action} onChange={(e) => setAction(e.target.value)}>
              {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label-sm block mb-1">Comment (optional)</label>
            <textarea className="input" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} />
          </div>
          {requiresJustification && (
            <div>
              <label className="label-sm block mb-1 text-status-warning">Justification (mandatory for override)</label>
              <textarea required className="input" rows={3} value={justification}
                placeholder="e.g. Supporting document received separately and verified manually."
                onChange={(e) => setJustification(e.target.value)} />
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={busy} className="btn-primary">{busy ? "Submitting…" : "Submit Review"}</button>
        </div>
      </form>
    </div>
  );
}
