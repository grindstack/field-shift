import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/assess", label: "Assessment" },
  { to: "/results", label: "Results" },
  { to: "/climate", label: "Climate" },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-field-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-field-700 text-sm font-bold text-white">
            FS
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-field-900">Field Shift</p>
            <p className="text-[11px] text-field-600">Sheikhupura, Punjab, Pakistan</p>
          </div>
        </div>
        <nav className="flex gap-1 text-sm font-medium">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 transition-colors ${
                  isActive
                    ? "bg-field-700 text-white"
                    : "text-field-800 hover:bg-field-100"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
