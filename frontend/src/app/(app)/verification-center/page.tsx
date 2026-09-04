"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ConnectorStatus } from "@/lib/types";
import { formatDateTime } from "@/lib/format";

export default function VerificationCenterPage() {
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);

  useEffect(() => {
    api.get<ConnectorStatus[]>("/verification-center/connectors").then(setConnectors);
  }, []);

  return (
    <div className="p-8 max-w-[1400px]">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-ink-900">Verification Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Government/registry connector status. All connectors below are <span className="font-medium">Sandbox Verification</span> —
          prototype connectors built to a stable interface so real government APIs can be substituted later without changing the rest of the platform.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {connectors.map((c) => (
          <div key={c.code} className="panel p-5">
            <div className="flex items-center justify-between mb-1">
              <div className="text-sm font-semibold text-ink-900">{c.label}</div>
              <span className="badge badge-verified">{c.mode}</span>
            </div>
            <div className="text-xs text-slate-500 mb-3">{c.code}</div>
            <div className="flex items-center gap-2 text-xs">
              <span className="w-2 h-2 rounded-full bg-status-verified" />
              <span className="text-slate-600">Connected</span>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500 space-y-1">
              <div>Last checked: {c.last_checked ? formatDateTime(c.last_checked) : "Never"}</div>
              <div>Last status: {c.last_status || "—"}</div>
              <div>Total checks: {c.total_checks}</div>
            </div>
            {c.last_response && (
              <div className="mt-3 bg-slate-50 rounded p-2 text-[11px] font-mono text-slate-600 overflow-x-auto max-h-24 overflow-y-auto">
                {JSON.stringify(c.last_response, null, 2)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
