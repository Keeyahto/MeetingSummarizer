"use client";
import { useEffect, useState } from "react";
import { getHealth } from "../../lib/api";
import type { HealthResponse } from "../../lib/types";

export default function HealthPage() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setData).catch((e) => setErr(String(e?.message || e)));
  }, []);

  if (err) return <div className="text-red-600">Ошибка: {err}</div>;
  if (!data) return <div>Загрузка…</div>;

  const rows: Array<[string, string | number | boolean]> = [
    ["env", data.env],
    ["gpu", data.gpu],
    ["asr_model", data.asr_model],
    ["asr_language", data.asr_language],
    ["llm_model", data.llm_model],
    ["process_mode", data.process_mode],
    ["diarization", data.diarization],
    ["fast_mode", data.fast_mode],
    ["models_cache", data.models_cache],
    ["data_dir", data.data_dir],
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Состояние</h1>
      <div className="rounded-2xl shadow-sm bg-white p-4">
        <table className="w-full text-sm">
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k}>
                <td className="py-1 pr-4 text-slate-500">{k}</td>
                <td className="py-1 font-mono">
                  {String(v)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
