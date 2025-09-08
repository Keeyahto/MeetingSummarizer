import { useUiStore } from "../lib/store";

export default function MetricsStrip() {
  const { result } = useUiStore();
  if (!result) return null;
  const rate = result.metrics.speech_rate_wpm;
  const tt = result.metrics.talk_time || {};
  const ttText = Object.entries(tt).map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`).join(" / ");
  return (
    <div className="text-sm text-slate-600">
      <span className="mr-4">Длительность: {Math.round(result.duration_sec)}с</span>
      <span className="mr-4">Скорость речи: {rate} слов/мин</span>
      <span>Доля речи: {ttText}</span>
    </div>
  );
}
