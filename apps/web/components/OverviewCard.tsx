"use client";
import { useUiStore } from "../lib/store";
import SSEButton from "./SSEButton";
import ActionList from "./ActionList";
import DecisionList from "./DecisionList";
import RiskList from "./RiskList";
import DownloadButtons from "./DownloadButtons";
import MetricsStrip from "./MetricsStrip";

export default function OverviewCard() {
  const { result, tldrStream, lastContext } = useUiStore();
  if (!result) return null;
  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">TL;DR</h3>
          <SSEButton />
        </div>
        <p className="whitespace-pre-wrap">
          {tldrStream ? (
            <span>
              {tldrStream}
              <span className="animate-pulse">|</span>
            </span>
          ) : (
            result.summary.tldr
          )}
        </p>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="font-semibold mb-2">Действия</div>
          <ActionList items={lastContext?.action_items || result.summary.action_items} />
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="font-semibold mb-2">Решения</div>
          <DecisionList items={lastContext?.decisions || result.summary.decisions} />
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="font-semibold mb-2">Риски</div>
          <RiskList items={lastContext?.risks || result.summary.risks} />
        </div>
      </div>
      <DownloadButtons />
      <MetricsStrip />
    </div>
  );
}
