"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Landmark,
  LayoutDashboard,
  Files,
  Calculator,
  History,
  Database,
  ListFilter,
  ClipboardCheck,
  Presentation,
} from "lucide-react";
const items = [
  ["/dashboard", "Workload", LayoutDashboard],
  ["/alerts", "Browse alerts", ListFilter],
  ["/cases", "Case preparation", Files],
  ["/quality", "Data quality", ClipboardCheck],
  ["/business", "Business case", Calculator],
  ["/history", "Review history", History],
  ["/pitch", "Team presentation", Presentation],
];
export default function Navigation() {
  const path = usePathname();
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside>
        <div className="brand">
          <Landmark size={37} strokeWidth={1.45} />
          <div>
            Northgate<span>B A N K</span>
          </div>
        </div>
        <div className="rail-title">Fraud operations</div>
        <nav>
          {items.map(([url, label, Icon]) => (
            <Link
              href={url}
              key={url}
              aria-current={path === url ? "page" : undefined}
              className={path === url ? "active" : ""}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="rail-foot">
          <Database size={17} />
          <div>
            Northgate warehouse<small>Local teaching environment</small>
          </div>
        </div>
      </aside>
    </>
  );
}
