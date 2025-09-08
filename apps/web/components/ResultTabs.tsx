"use client";
import { useState } from "react";
import OverviewCard from "./OverviewCard";
import TranscriptView from "./TranscriptView";
import TopicTimeline from "./TopicTimeline";

export default function ResultTabs() {
  const [tab, setTab] = useState<"overview"|"transcript"|"subtitles"|"topics">("overview");
  return (
    <div>
      <div className="flex gap-2 mb-4">
        {([
          ["overview","Обзор"],
          ["transcript","Транскрипт"],
          ["subtitles","Субтитры"],
          ["topics","Темы"],
        ] as const).map(([k, label]) => (
          <button key={k} className={`px-3 py-1.5 border rounded ${tab===k?"bg-slate-900 text-white":""}`} onClick={() => setTab(k)}>{label}</button>
        ))}
      </div>
      {tab === "overview" && <OverviewCard />}
      {tab === "transcript" && <TranscriptView />}
      {tab === "subtitles" && (
        <div className="text-sm text-slate-600">Используйте кнопки загрузки в «Обзор», чтобы получить файлы .srt и .vtt.</div>
      )}
      {tab === "topics" && <TopicTimeline />}
    </div>
  );
}
