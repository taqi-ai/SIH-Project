"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/tenders", label: "Tenders" },
  { href: "/verification-center", label: "Verification Center" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-[var(--background)]">
      <aside className="w-60 shrink-0 bg-ink-950 text-slate-200 flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="text-[11px] uppercase tracking-widest text-brand-400 font-semibold">SIH26100 · Prototype</div>
          <div className="mt-1 text-sm font-semibold text-white leading-tight">GeM Bid Compliance Platform</div>
          <div className="mt-1 text-[11px] text-slate-400">CPCL · Ministry of Petroleum &amp; Natural Gas</div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="px-3 py-4 border-t border-white/10">
          <div className="px-2 text-xs text-slate-400">Signed in as</div>
          <div className="px-2 text-sm font-medium text-white truncate">{user?.full_name}</div>
          <div className="px-2 text-[11px] text-slate-400 truncate">{user?.designation}</div>
          <button onClick={logout} className="mt-2 w-full text-left px-2 py-1.5 text-xs text-slate-300 hover:text-white hover:bg-white/5 rounded">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
