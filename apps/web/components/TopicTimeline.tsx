import { useUiStore } from "../lib/store";

export default function TopicTimeline() {
  const { result } = useUiStore();
  const topics = result?.topics || [];
  if (!topics.length) return <div className="text-sm text-slate-500">Нет тем</div>;
  const dur = Math.max(1, result?.duration_sec || 1);
  return (
    <div className="flex h-6 w-full rounded overflow-hidden">
      {topics.map((t, idx) => {
        const left = (t.start / dur) * 100;
        const width = ((t.end - t.start) / dur) * 100;
        return (
          <div key={idx} className="bg-blue-200 hover:bg-blue-300" style={{ width: `${width}%` }} title={`${t.title} (${t.start.toFixed(1)}–${t.end.toFixed(1)})`} />
        );
      })}
    </div>
  );
}
