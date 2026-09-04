"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { DashboardSummary } from "@/lib/types";
import { formatDate, formatDateTime } from "@/lib/format";
import { StatusBadge } from "@/components/StatusBadge";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="panel p-4">
      <div className="label-sm">{label}</div>
      <div className="mt-1.5 text-2xl font-semibold text-ink-900">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<DashboardSummary>("/dashboard/summary").then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="p-8 text-status-failed text-sm">{error}</div>;
  if (!data) return <div className="p-8 text-sm text-slate-500">Loading dashboard…</div>;

  const riskTotal = data.risk_distribution.LOW + data.risk_distribution.MEDIUM + data.risk_distribution.HIGH || 1;

  return (
    <div className="p-8 max-w-[1400px]">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-ink-900">Compliance Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Live overview derived from tender, bid and verification records.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Active Tenders" value={data.active_tenders} />
        <StatCard label="Bids Under Review" value={data.bids_under_review} />
        <StatCard label="Compliant Bids (Qualified)" value={data.compliant_bids} sub="Officer-qualified only" />
        <StatCard label="High Risk Bids" value={data.high_risk_bids} />
        <StatCard label="Pending Verification" value={data.pending_verification} />
        <StatCard label="Documents Processed" value={data.documents_processed} />
        <StatCard label="Verification Success Rate" value={`${data.verification_success_rate}%`} sub="Sandbox connectors" />
        <StatCard
          label="Risk Distribution"
          value={`${data.risk_distribution.HIGH} High`}
          sub={`${data.risk_distribution.MEDIUM} Medium · ${data.risk_distribution.LOW} Low`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 panel">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink-900">Recent Tenders</h2>
            <Link href="/tenders" className="text-xs text-brand-600 font-medium hover:underline">
              View all
            </Link>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-slate-500 border-b border-slate-100">
                <th className="px-5 py-2.5 font-medium">Tender</th>
                <th className="px-5 py-2.5 font-medium">Closing</th>
                <th className="px-5 py-2.5 font-medium">Bids</th>
                <th className="px-5 py-2.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_tenders.map((t) => (
                <tr key={t.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50">
                  <td className="px-5 py-3">
                    <Link href={`/tenders/${t.id}`} className="font-medium text-ink-900 hover:text-brand-600">
                      {t.title}
                    </Link>
                    <div className="text-xs text-slate-500">{t.tender_number}</div>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{formatDate(t.closing_date)}</td>
                  <td className="px-5 py-3 text-slate-600">{t.bid_count}</td>
                  <td className="px-5 py-3">
                    <StatusBadge status={t.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-ink-900">Recent Compliance Activity</h2>
          </div>
          <div className="px-5 py-3 space-y-3 max-h-[420px] overflow-y-auto">
            {data.recent_activity.map((a, i) => (
              <div key={i} className="text-xs">
                <div className="text-ink-800 font-medium">{a.action.replace(/_/g, " ")}</div>
                <div className="text-slate-500">
                  {a.actor} · {formatDateTime(a.timestamp)}
                </div>
              </div>
            ))}
            {data.recent_activity.length === 0 && <div className="text-xs text-slate-400 py-4">No activity yet.</div>}
          </div>
        </div>
      </div>

      <div className="panel mt-4 p-5">
        <h2 className="text-sm font-semibold text-ink-900 mb-3">Risk Distribution</h2>
        <div className="flex h-3 rounded-full overflow-hidden bg-slate-100">
          <div className="bg-status-verified" style={{ width: `${(100 * data.risk_distribution.LOW) / riskTotal}%` }} />
          <div className="bg-status-warning" style={{ width: `${(100 * data.risk_distribution.MEDIUM) / riskTotal}%` }} />
          <div className="bg-status-failed" style={{ width: `${(100 * data.risk_distribution.HIGH) / riskTotal}%` }} />
        </div>
        <div className="flex gap-6 mt-3 text-xs text-slate-600">
          <span><span className="inline-block w-2 h-2 rounded-full bg-status-verified mr-1.5" />Low ({data.risk_distribution.LOW})</span>
          <span><span className="inline-block w-2 h-2 rounded-full bg-status-warning mr-1.5" />Medium ({data.risk_distribution.MEDIUM})</span>
          <span><span className="inline-block w-2 h-2 rounded-full bg-status-failed mr-1.5" />High ({data.risk_distribution.HIGH})</span>
        </div>
      </div>
    </div>
  );
}
