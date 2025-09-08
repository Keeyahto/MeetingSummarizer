"use client";
import { useUiStore } from "../lib/store";

export default function JobProgress() {
  const { jobId, polling, status, error } = useUiStore();
  return (
    <div className="space-y-2">
      <div className="font-semibold">Задача</div>
      <div className="text-sm">ID: <span className="font-mono">{jobId}</span></div>
      <div className="h-2 bg-slate-200 rounded">
        <div className="h-2 bg-blue-600 rounded" style={{ width: status === "done" ? "100%" : status === "queued" ? "15%" : status === "working" ? "65%" : "5%" }} />
      </div>
      <div className="text-sm text-slate-600">
        {status === "queued" && "в очереди"}
        {status === "working" && "обработка…"}
        {status === "done" && "готово"}
        {status === "error" && <span className="text-red-600">ошибка</span>}
        {polling && <span className="ml-2 text-slate-400">(опрос)</span>}
      </div>
      {error && <div className="text-sm text-red-600">{error}</div>}
    </div>
  );
}
