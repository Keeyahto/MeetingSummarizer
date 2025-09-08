"use client";
import { useEffect, useMemo, useState } from "react";
import UploadArea from "../../components/UploadArea";
import JobProgress from "../../components/JobProgress";
import ResultTabs from "../../components/ResultTabs";
import { useUiStore } from "../../lib/store";
import { useSearchParams, useRouter } from "next/navigation";
import { getResult, getStatus } from "../../lib/api";

export default function DemoPage() {
  const params = useSearchParams();
  const router = useRouter();
  const jobFromUrl = params.get("job") || undefined;
  const {
    jobId, status, result, polling, setJob, setResult, setPolling, setError,
  } = useUiStore();

  useEffect(() => {
    if (jobFromUrl && !jobId) setJob(jobFromUrl);
  }, [jobFromUrl, jobId, setJob]);

  // Poll status if we have a job without result
  useEffect(() => {
    if (!jobId || result) return;
    const POLL_MS = Number(process.env.NEXT_PUBLIC_POLL_MS || 1200);
    setPolling(true);
    const t = setInterval(async () => {
      try {
        const s = await getStatus(jobId);
        if (s.status === "done") {
          clearInterval(t);
          const r = await getResult(jobId);
          setResult(r);
          setPolling(false);
          const sp = new URLSearchParams(Array.from(params.entries()));
          sp.set("job", jobId);
          router.replace(`/demo?${sp.toString()}`);
        } else if (s.status === "error") {
          clearInterval(t);
          setPolling(false);
          setError(s.error || "Job failed");
        }
      } catch (e: any) {
        clearInterval(t);
        setPolling(false);
        setError(e?.message || String(e));
      }
    }, POLL_MS);
    return () => clearInterval(t);
  }, [jobId, result, setPolling, setResult, setError, params, router]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl shadow-sm p-4 bg-white">
        <UploadArea />
      </div>
      {jobId && (
        <div className="rounded-2xl shadow-sm p-4 bg-white">
          <JobProgress />
        </div>
      )}
      {result && (
        <div className="rounded-2xl shadow-sm p-4 bg-white">
          <ResultTabs />
        </div>
      )}
    </div>
  );
}

