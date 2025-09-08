"use client";
import { useMemo, useState } from "react";
import { useUiStore } from "../lib/store";
import { toHMS } from "../lib/time";

export default function TranscriptView() {
  const { result } = useUiStore();
  const [q, setQ] = useState("");
  const [speaker, setSpeaker] = useState<string | "all">("all");
  const segments = result?.segments || [];
  const speakers = result?.speakers || [];
  const filtered = useMemo(() => segments.filter((s) => {
    if (speaker !== "all" && s.speaker !== speaker) return false;
    if (q && !s.text.toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  }), [segments, q, speaker]);

  if (!result) return null;
  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <input className="border rounded px-2 py-1 text-sm" placeholder="Поиск" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="border rounded px-2 py-1 text-sm" value={speaker} onChange={(e) => setSpeaker(e.target.value)}>
          <option value="all">Все спикеры</option>
          {speakers.map((sp) => (<option key={sp} value={sp}>{sp}</option>))}
        </select>
      </div>
      <ul className="space-y-2">
        {filtered.map((s, i) => (
          <li key={i} className="flex gap-3">
            <div className="font-mono text-slate-500 shrink-0 w-24">[{toHMS(s.start)}]</div>
            <div>
              <div className="text-xs inline-block bg-slate-100 rounded-full px-2 py-0.5 mr-2">{s.speaker}</div>
              <span>{s.text}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
