export interface NavItem {
  href: string;
  label: string;
  index: string;
}

export const NAV_ITEMS: readonly NavItem[] = [
  { href: "/", label: "Overview", index: "01" },
  { href: "/data", label: "Data Explorer", index: "02" },
  { href: "/analysis", label: "Drift Analysis", index: "03" },
  { href: "/report", label: "Reproduction Report", index: "04" },
  { href: "/methods", label: "Methods & Sources", index: "05" },
];
