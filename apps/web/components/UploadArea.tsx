"use client";
import { useCallback, useRef, useState } from "react";
import { allowedExtension, maxSizeOk } from "../lib/file";
import { postTranscribe } from "../lib/api";
import { useUiStore } from "../lib/store";

const exts = [".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus", ".webm"];

export default function UploadArea() {
  const inputRef = useRef<HTMLInputElement>(null);
  const { setJob, setUploading, setError, language, fastMode, resetResult } = useUiStore();
  const [file, setFile] = useState<File | null>(null);

  const onFile = useCallback((f: File) => {
    setFile(f);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  }, [onFile]);

  const onSend = useCallback(async () => {
    if (!file) return;
    if (!allowedExtension(file.name)) {
      setError("Unsupported format");
      return;
    }
    if (!maxSizeOk(file.size)) {
      setError("File too large");
      return;
    }
    try {
      setUploading(true);
      resetResult();
      const res = await postTranscribe(file, { fast_mode: fastMode, language });
      setJob(res.job_id);
      sessionStorage.setItem("jobId", res.job_id);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setUploading(false);
    }
  }, [file, setJob, setUploading, setError, language, fastMode, resetResult]);

  return (
    <div>
      <div
        className="border-2 border-dashed rounded-xl p-6 text-center text-slate-600"
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
      >
        <div className="mb-2">Перетащите файл сюда</div>
        <div className="text-xs">Поддерживается: {exts.join(", ")}</div>
        <div className="mt-3">
          <button className="px-3 py-1.5 border rounded" onClick={() => inputRef.current?.click()}>Выбрать файл</button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={exts.join(",")}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFile(f);
          }}
        />
      </div>
      {file && (
        <div className="mt-3 flex items-center justify-between text-sm">
          <div className="truncate">{file.name}</div>
          <button className="px-3 py-1.5 bg-blue-600 text-white rounded" onClick={onSend}>Отправить</button>
        </div>
      )}
    </div>
  );
}
