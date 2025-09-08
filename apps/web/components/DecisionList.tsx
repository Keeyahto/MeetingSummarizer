export default function DecisionList({ items }: { items: string[] }) {
  if (!items?.length) return <div className="text-slate-500 text-sm">Нет</div>;
  return (
    <ul className="list-disc list-inside text-sm">
      {items.map((d, i) => <li key={i}>{d}</li>)}
    </ul>
  );
}
