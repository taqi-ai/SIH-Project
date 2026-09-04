"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Tender } from "@/lib/types";
import { formatDate, formatINR, formatPct } from "@/lib/format";
import { StatusBadge, RiskBadge } from "@/components/StatusBadge";

export default function TenderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tender, setTender] = useState<Tender | null>(null);
  const [showAddBidder, setShowAddBidder] = useState(false);

  function refresh() {
    api.get<Tender>(`/tenders/${id}`).then(setTender);
  }
  useEffect(refresh, [id]);

  if (!tender) return <div className="p-8 text-sm text-slate-500">Loading tender…</div>;

  return (
    <div className="p-8 max-w-[1400px]">
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs font-mono text-slate-500">{tender.tender_number}</div>
          <h1 className="text-xl font-semibold text-ink-900 mt-1">{tender.title}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-slate-500">
            <span>{tender.organization}</span>
            <span>·</span>
            <span>Closing {formatDate(tender.closing_date)}</span>
            <span>·</span>
            <StatusBadge status={tender.status} />
          </div>
        </div>
        <button className="btn-primary" onClick={() => setShowAddBidder(true)}>+ Register Bid</button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="panel p-4">
          <div className="label-sm">Estimated Value</div>
          <div className="mt-1 text-lg font-semibold text-ink-900">{formatINR(tender.estimated_value)}</div>
        </div>
        <div className="panel p-4">
          <div className="label-sm">Min. Turnover</div>
          <div className="mt-1 text-lg font-semibold text-ink-900">{formatINR(tender.min_turnover)}</div>
        </div>
        <div className="panel p-4">
          <div className="label-sm">Min. Years / Local Content</div>
          <div className="mt-1 text-lg font-semibold text-ink-900">{tender.min_years_operation} yrs · {formatPct(tender.min_local_content_pct)}</div>
        </div>
        <div className="panel p-4">
          <div className="label-sm">OEM Authorization</div>
          <div className="mt-1 text-lg font-semibold text-ink-900">{tender.requires_oem_authorization ? "Required" : "Not Required"}</div>
        </div>
      </div>

      {tender.description && (
        <div className="panel p-5 mb-6 text-sm text-slate-700 leading-relaxed">{tender.description}</div>
      )}

      <div className="panel mb-6">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="text-sm font-semibold text-ink-900">Requirement Set ({tender.requirements?.length || 0})</h2>
          <p className="text-xs text-slate-500 mt-0.5">Data-driven compliance requirements attached to this tender.</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-px bg-slate-100">
          {tender.requirements?.map((r) => (
            <div key={r.id} className="bg-white px-4 py-3">
              <div className="text-sm font-medium text-ink-900">{r.label}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {r.mandatory ? "Mandatory" : "Conditional"} · {r.code}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="text-sm font-semibold text-ink-900">Bidders ({tender.bids?.length || 0})</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wide text-slate-500 border-b border-slate-100 bg-slate-50">
              <th className="px-5 py-2.5 font-medium">Bidder</th>
              <th className="px-5 py-2.5 font-medium">Documents</th>
              <th className="px-5 py-2.5 font-medium">Status</th>
              <th className="px-5 py-2.5 font-medium">Score</th>
              <th className="px-5 py-2.5 font-medium">Risk</th>
              <th className="px-5 py-2.5 font-medium">Final Decision</th>
              <th className="px-5 py-2.5 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {tender.bids?.map((b) => (
              <tr key={b.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50">
                <td className="px-5 py-3">
                  <div className="font-medium text-ink-900">{b.bidder.company_name}</div>
                  <div className="text-xs text-slate-500">{b.bidder.pan || "PAN pending"}</div>
                </td>
                <td className="px-5 py-3 text-slate-600">{b.document_count}</td>
                <td className="px-5 py-3"><StatusBadge status={b.status} /></td>
                <td className="px-5 py-3 text-slate-700">{b.compliance_score !== null ? `${b.compliance_score}/100` : "—"}</td>
                <td className="px-5 py-3"><RiskBadge level={b.risk_level} /></td>
                <td className="px-5 py-3">{b.final_decision ? <StatusBadge status={b.final_decision} /> : <span className="text-xs text-slate-400">Pending officer review</span>}</td>
                <td className="px-5 py-3">
                  <Link href={`/bids/${b.id}`} className="text-brand-600 text-xs font-medium hover:underline">Review →</Link>
                </td>
              </tr>
            ))}
            {tender.bids?.length === 0 && (
              <tr><td colSpan={7} className="px-5 py-8 text-center text-sm text-slate-400">No bids registered yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showAddBidder && <AddBidderModal tenderId={tender.id} onClose={() => setShowAddBidder(false)} onCreated={refresh} />}
    </div>
  );
}

function AddBidderModal({ tenderId, onClose, onCreated }: { tenderId: string; onClose: () => void; onCreated: () => void }) {
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "", pan: "", gstin: "", udyam_number: "", enterprise_type: "Small",
    incorporation_year: 2018, declared_turnover: 10000000, declared_local_content_pct: 50,
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const bid = await api.post<{ id: string }>(`/tenders/${tenderId}/bids`, {
        bidder: {
          company_name: form.company_name, pan: form.pan || null, gstin: form.gstin || null,
          udyam_number: form.udyam_number || null, enterprise_type: form.enterprise_type,
          incorporation_year: form.incorporation_year,
        },
        declared_turnover: form.declared_turnover, declared_local_content_pct: form.declared_local_content_pct,
      });
      onCreated();
      onClose();
      router.push(`/bids/${bid.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to register bid");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <form onSubmit={submit} className="bg-white rounded-lg shadow-panel w-full max-w-md p-6">
        <h2 className="text-base font-semibold text-ink-900 mb-4">Register Bidder</h2>
        {error && <div className="mb-3 text-sm text-status-failed bg-status-failedBg rounded px-3 py-2">{error}</div>}
        <div className="space-y-3">
          <div>
            <label className="label-sm block mb-1">Company Name</label>
            <input required className="input" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-sm block mb-1">PAN</label>
              <input className="input" value={form.pan} onChange={(e) => setForm({ ...form, pan: e.target.value.toUpperCase() })} />
            </div>
            <div>
              <label className="label-sm block mb-1">GSTIN</label>
              <input className="input" value={form.gstin} onChange={(e) => setForm({ ...form, gstin: e.target.value.toUpperCase() })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-sm block mb-1">Declared Turnover (₹)</label>
              <input type="number" className="input" value={form.declared_turnover} onChange={(e) => setForm({ ...form, declared_turnover: Number(e.target.value) })} />
            </div>
            <div>
              <label className="label-sm block mb-1">Declared Local Content %</label>
              <input type="number" className="input" value={form.declared_local_content_pct} onChange={(e) => setForm({ ...form, declared_local_content_pct: Number(e.target.value) })} />
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={busy} className="btn-primary">{busy ? "Registering…" : "Register & Continue"}</button>
        </div>
      </form>
    </div>
  );
}
