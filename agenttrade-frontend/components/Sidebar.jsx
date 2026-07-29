"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, LineChart, Bot, History, Settings } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/markets", label: "Markets", icon: LineChart },
  { href: "/dashboard/agent", label: "Agent", icon: Bot },
  { href: "/dashboard/history", label: "History", icon: History },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-52 border-r border-line min-h-screen py-6 px-3 shrink-0">
      <div className="font-mono tracking-widest text-sm px-2 mb-8">AGENTTRADE</div>
      <nav className="flex flex-col gap-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 px-2 py-2 rounded text-sm font-mono transition-colors duration-150 ease ${
                active ? "bg-surface2 text-signal" : "text-dim hover-fine:text-white"
              }`}
            >
              <Icon size={15} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
