"use client";
import { useUiStore } from "../lib/store";

export default function Toast() {
  const { error, setError } = useUiStore();
  if (!error) return null;
  return (
    <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded shadow" onClick={() => setError(null)}>
      {error}
    </div>
  );
}

