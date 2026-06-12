"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, Mic, Type, UserCircle } from "lucide-react";
import clsx from "clsx";
import { useEffect, useState } from "react";

const NAV = [
  { href: "/recorder", label: "Voice Recorder", icon: Mic },
  { href: "/tts", label: "Text to Speech", icon: Type },
  { href: "/profiles", label: "Voice Profiles", icon: UserCircle },
];

const STORAGE_KEY = "sidebar-collapsed";

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) setCollapsed(saved === "true");
  }, []);

  const toggle = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  };

  return (
    <aside
      className={clsx(
        "flex shrink-0 flex-col border-r border-surface-border bg-surface transition-[width] duration-200 ease-in-out",
        collapsed ? "w-[4.75rem]" : "w-60",
      )}
    >
      <div className="border-b border-surface-border">
        <div className="flex items-center justify-start p-3 pb-0">
          <button
            type="button"
            className="btn btn-icon shrink-0 text-ink-muted hover:text-ink"
            onClick={toggle}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>
        <div
          className={clsx(
            "flex justify-center",
            collapsed ? "px-3 pb-4 pt-2" : "px-6 pb-6 pt-2",
          )}
        >
          <Image
            src="/logo.png"
            alt="VoiceGen"
            width={160}
            height={160}
            className={clsx(
              "h-auto object-contain transition-all duration-200",
              collapsed ? "w-10" : "w-full max-w-[9.5rem]",
            )}
            priority
          />
        </div>
      </div>

      <nav className={clsx("flex flex-1 flex-col gap-2", collapsed ? "p-3" : "p-5")}>
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={clsx(
                "flex items-center rounded-lg text-sm font-medium transition",
                collapsed ? "justify-center px-0 py-3" : "gap-3 px-4 py-3",
                active
                  ? collapsed
                    ? "bg-surface-muted text-ink"
                    : "border-l-2 border-ink bg-surface-muted pl-[14px] text-ink"
                  : "text-ink-muted hover:bg-surface-muted hover:text-ink",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
