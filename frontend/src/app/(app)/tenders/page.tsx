"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Tender } from "@/lib/types";
import { formatDate, formatINR } from "@/lib/format";
import { StatusBadge, RiskBadge } from "@/components/StatusBadge";

export default function TendersPage() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  function refresh() {
    setLoading(true);
    api.get<Tender[]>("/tenders").then(setTenders).finally(() => setLoading(false));
  }

  useEffect(refresh, []);

  return (
    <div className="p-8 max-w-[1400px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">Tenders</h1>
          <p className="text-sm text-slate-500 mt-1">GeM procurement tenders under CPCL evaluation.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + New Tender
        </button>
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wide text-slate-500 border-b border-slate-100 bg-slate-50">
              <th className="px-5 py-2.5 font-medium">Tender ID</th>
              <th className="px-5 py-2.5 font-medium">Title</th>
              <th className="px-5 py-2.5 font-medium">Organization</th>
              <th className="px-5 py-2.5 font-medium">Closing Date</th>
              <th className="px-5 py-2.5 font-medium">Bids</th>
              <th className="px-5 py-2.5 font-medium">Status</th>
              <th className="px-5 py-2.5 font-medium">Risk</th>
              <th className="px-5 py-2.5 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {tenders.map((t) => (
              <tr key={t.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50">
                <td className="px-5 py-3 font-mono text-xs text-slate-600">{t.tender_number}</td>
                <td className="px-5 py-3">
                  <div className="font-medium text-ink-900">{t.title}</div>
                  <div className="text-xs text-slate-500">{formatINR(t.estimated_value)}</div>
                </td>
                <td className="px-5 py-3 text-slate-600">{t.organization}</td>
                <td className="px-5 py-3 text-slate-600">{formatDate(t.closing_date)}</td>
                <td className="px-5 py-3 text-slate-600">{t.bid_count}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-5 py-3">{t.max_risk ? <RiskBadge level={t.max_risk} /> : <span className="text-xs text-slate-400">—</span>}</td>
                <td className="px-5 py-3">
                  <Link href={`/tenders/${t.id}`} className="text-brand-600 text-xs font-medium hover:underline">
                    Open →
                  </Link>
                </td>
              </tr>
            ))}
            {!loading && tenders.length === 0 && (
              <tr>
                <td colSpan={8} className="px-5 py-8 text-center text-sm text-slate-400">
                  No tenders yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreate && <CreateTenderModal onClose={() => setShowCreate(false)} onCreated={refresh} />}
    </div>
  );
}

function CreateTenderModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    tender_number: "", title: "", category: "Goods", estimated_value: 10000000,
    closing_date: "", description: "", min_turnover: 10000000, min_years_operation: 2,
    min_local_content_pct: 40, requires_oem_authorization: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/tenders", { ...form, closing_date: new Date(form.closing_date).toISOString() });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create tender");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <form onSubmit={submit} className="bg-white rounded-lg shadow-panel w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-base font-semibold text-ink-900 mb-4">Create Tender</h2>
        {error && <div className="mb-3 text-sm text-status-failed bg-status-failedBg rounded px-3 py-2">{error}</div>}
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="label-sm block mb-1">Tender Number</label>
            <input required className="input" value={form.tender_number} onChange={(e) => setForm({ ...form, tender_number: e.target.value })} />
          </div>
          <div className="col-span-2">
            <label className="label-sm block mb-1">Title</label>
            <input required className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <label className="label-sm block mb-1">Category</label>
            <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              <option>Goods</option>
              <option>Services</option>
              <option>Works</option>
            </select>
          </div>
          <div>
            <label className="label-sm block mb-1">Estimated Value (₹)</label>
            <input type="number" className="input" value={form.estimated_value} onChange={(e) => setForm({ ...form, estimated_value: Number(e.target.value) })} />
          </div>
          <div className="col-span-2">
            <label className="label-sm block mb-1">Closing Date</label>
            <input required type="date" className="input" value={form.closing_date} onChange={(e) => setForm({ ...form, closing_date: e.target.value })} />
          </div>
          <div>
            <label className="label-sm block mb-1">Min. Turnover (₹)</label>
            <input type="number" className="input" value={form.min_turnover} onChange={(e) => setForm({ ...form, min_turnover: Number(e.target.value) })} />
          </div>
          <div>
            <label className="label-sm block mb-1">Min. Years Operation</label>
            <input type="number" className="input" value={form.min_years_operation} onChange={(e) => setForm({ ...form, min_years_operation: Number(e.target.value) })} />
          </div>
          <div>
            <label className="label-sm block mb-1">Min. Local Content %</label>
            <input type="number" className="input" value={form.min_local_content_pct} onChange={(e) => setForm({ ...form, min_local_content_pct: Number(e.target.value) })} />
          </div>
          <div className="flex items-center gap-2 pt-5">
            <input id="oem" type="checkbox" checked={form.requires_oem_authorization} onChange={(e) => setForm({ ...form, requires_oem_authorization: e.target.checked })} />
            <label htmlFor="oem" className="text-sm text-slate-700">Requires OEM Authorization</label>
          </div>
          <div className="col-span-2">
            <label className="label-sm block mb-1">Description</label>
            <textarea className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" disabled={busy} className="btn-primary">{busy ? "Creating…" : "Create Tender"}</button>
        </div>
      </form>
    </div>
  );
}
