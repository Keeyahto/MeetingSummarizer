import { ActionItem } from "../lib/types";
import { formatDue } from "../lib/time";

export default function ActionList({ items }: { items: ActionItem[] }) {
  if (!items?.length) return <div className="text-slate-500 text-sm">Нет</div>;
  return (
    <ul className="space-y-1 text-sm">
      {items.map((a, i) => (
        <li key={i} className="flex items-center gap-2">
          <input type="checkbox" className="accent-blue-600" />
          <span>{a.text}</span>
          <span className="text-slate-500">(ответственный: {a.owner || "нет"}, срок: {formatDue(a.due)})</span>
        </li>
      ))}
    </ul>
  );
}
