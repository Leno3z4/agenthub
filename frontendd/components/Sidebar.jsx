"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  LineChart,
  Bot,
  History,
  Settings,
} from "lucide-react";

const links = [
  {
    href: "/dashboard",
    label: "Overview",
    icon: LayoutDashboard,
  },
  {
    href: "/dashboard/markets",
    label: "Markets",
    icon: LineChart,
  },
  {
    href: "/dashboard/agent",
    label: "Agent",
    icon: Bot,
  },
  {
    href: "/dashboard/history",
    label: "History",
    icon: History,
  },
  {
    href: "/dashboard/settings",
    label: "Settings",
    icon: Settings,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="alias-sidebar">
      <div className="alias-sidebar-top">
        <Link href="/" className="alias-sidebar-logo">
          ALIAS
        </Link>

        <p className="alias-sidebar-subtitle">
          Autonomous Trading Infrastructure
        </p>
      </div>

      <nav className="alias-sidebar-nav">
        {links.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/dashboard"
              ? pathname === href
              : pathname.startsWith(href);

          return (
            <Link
              key={href}
              href={href}
              className={`alias-nav-item ${
                active ? "alias-nav-active" : ""
              }`}
            >
              <Icon
                size={18}
                strokeWidth={1.8}
              />

              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="alias-sidebar-footer">
        <div className="alias-status-dot" />

        <span>System online</span>
      </div>
    </aside>
  );
}
