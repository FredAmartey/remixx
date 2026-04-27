"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, ListMusic, Sparkles } from "lucide-react";

const navItems = [
  { label: "Chat", icon: MessageSquare, href: "/chat" },
  { label: "Playlist", icon: ListMusic, href: "/playlist" },
  { label: "Taste", icon: Sparkles, href: "/taste" },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="px-6 mt-8 flex flex-col gap-4">
      {navItems.map(({ label, icon: Icon, href }) => {
        const active = pathname === href || (href === "/chat" && pathname === "/");
        return (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-3 transition-colors ${
              active ? "text-cream" : "text-cream hover:text-copper-glow"
            }`}
          >
            <Icon
              className={`h-4 w-4 ${active ? "text-copper" : "text-cream-muted"}`}
              strokeWidth={1.5}
            />
            <span
              className={`font-display italic text-base ${
                active
                  ? "underline underline-offset-[6px] decoration-copper decoration-1"
                  : ""
              }`}
            >
              {label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
