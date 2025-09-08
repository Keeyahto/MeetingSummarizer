export default function Pill({ children, color = "slate" }: { children: React.ReactNode; color?: "slate"|"amber"|"green"|"blue" }) {
  const cls = color === "amber" ? "bg-amber-100 text-amber-700" : color === "green" ? "bg-green-100 text-green-700" : color === "blue" ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-700";
  return (
    <span className={`rounded-full text-xs px-2 py-0.5 ${cls}`}>{children}</span>
  );
}

