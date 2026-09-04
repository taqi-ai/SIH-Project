"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("procurement@cpcl.gov.in");
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between bg-ink-950 text-white p-12">
        <div>
          <div className="text-[11px] uppercase tracking-widest text-brand-400 font-semibold">
            Smart India Hackathon 2026 · SIH26100
          </div>
          <div className="mt-2 text-2xl font-semibold leading-snug max-w-md">
            AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement
          </div>
          <div className="mt-4 text-sm text-slate-300 max-w-md leading-relaxed">
            Ministry of Petroleum &amp; Natural Gas · Chennai Petroleum Corporation Limited (CPCL)
          </div>
        </div>
        <div className="space-y-4 max-w-md">
          <div className="text-sm text-slate-300 leading-relaxed">
            A human-in-the-loop compliance workspace: AI extracts, verifies and analyzes bidder
            documents across GST, PAN, Udyam, EPFO, ESIC, MII, NSIC, Startup India, OEM authorization
            and debarment sources. The Procurement Officer always retains the final qualification decision.
          </div>
          <div className="flex gap-6 text-xs text-slate-400 pt-4 border-t border-white/10">
            <div>Deterministic rule engine</div>
            <div>Sandbox government connectors</div>
            <div>Tamper-evident audit trail</div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <form onSubmit={handleSubmit} className="w-full max-w-sm panel p-8">
          <div className="mb-6">
            <div className="text-lg font-semibold text-ink-900">Procurement Officer Login</div>
            <div className="text-sm text-slate-500 mt-1">Sign in to review bidder compliance</div>
          </div>

          {error && (
            <div className="mb-4 text-sm text-status-failed bg-status-failedBg border border-status-failed/20 rounded-md px-3 py-2">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="label-sm block mb-1.5">Email</label>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="label-sm block mb-1.5">Password</label>
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
          </div>

          <button type="submit" disabled={busy} className="btn-primary w-full mt-6">
            {busy ? "Signing in…" : "Sign in"}
          </button>

          <div className="mt-5 pt-4 border-t border-slate-100 text-xs text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-600">Prototype demo credentials:</span>
            <br />
            procurement@cpcl.gov.in / demo123
          </div>
        </form>
      </div>
    </div>
  );
}
