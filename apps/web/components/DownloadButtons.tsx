"use client";
import { useUiStore } from "../lib/store";

export default function DownloadButtons() {
  const { jobId } = useUiStore();
  if (!jobId) return null;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const links: Array<[string, string]> = [
    [".md", `${base}/export/${jobId}.md`],
    [".json", `${base}/export/${jobId}.json`],
    [".srt", `${base}/export/${jobId}.srt`],
    [".vtt", `${base}/export/${jobId}.vtt`],
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {links.map(([ext, href]) => (
        <a key={ext} className="px-3 py-1.5 border rounded" href={href} download>
          Скачать {ext}
        </a>
      ))}
    </div>
  );
}
