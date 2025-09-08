"use client";
import { postSummaryStream } from "../lib/api";
import { useUiStore } from "../lib/store";

export default function SSEButton() {
  const { jobId, streaming, setContext, appendToken, startStream, stopStream, setError } = useUiStore();
  const run = async () => {
    if (!jobId) return;
    startStream();
    try {
      await postSummaryStream(jobId, {
        onContext: (c) => setContext(c),
        onToken: (t) => appendToken(t),
        onDone: () => stopStream(),
        onError: (e) => { setError(e.message); stopStream(); },
      });
    } catch (e: any) {
      setError(e?.message || String(e));
      stopStream();
    }
  };
  return (
    <button
      className="px-3 py-1.5 border rounded"
      onClick={run}
      disabled={streaming}
      title="Потоковый TL;DR через SSE"
    >
      {streaming ? "Стрим…" : "Стрим TL;DR"}
    </button>
  );
}
