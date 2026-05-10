"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Home", href: "/chat" },
  { label: "Search", href: "/playlist" },
  { label: "Your Library", href: "/taste" },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <nav className="mt-14 flex flex-col gap-5 px-8">
      {navItems.map(({ label, href }) => {
        const active =
          pathname === href || (href === "/chat" && pathname === "/");
        return (
          <Link
            key={href}
            href={href}
            className={`transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70 ${
              active ? "text-cream" : "text-cream-muted hover:text-cream"
            }`}
          >
            <span
              className={`font-display text-3xl italic leading-none ${
                active
                  ? "underline decoration-copper decoration-1 underline-offset-[9px]"
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
