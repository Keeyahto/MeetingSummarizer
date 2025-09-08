"use client";
import Link from "next/link";
import { useUiStore } from "../lib/store";

export default function Header() {
  const { language, fastMode, setSettings } = useUiStore();
  return (
    <header className="border-b bg-white">
      <div className="container flex items-center justify-between py-3">
        <div className="flex items-center gap-4">
          <Link href="/" className="font-semibold">Сводка встреч</Link>
          <nav className="text-sm text-slate-600">
            <Link className="hover:text-slate-900 mr-3" href="/demo">Демо</Link>
            <Link className="hover:text-slate-900" href="/health">Состояние</Link>
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <label className="flex items-center gap-2">
            <span className="text-slate-600">Язык</span>
            <select
              className="border rounded px-2 py-1"
              value={language}
              onChange={(e) => setSettings({ language: e.target.value })}
            >
              <option value="auto">auto</option>
              <option value="en">en</option>
              <option value="ru">ru</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <span className="text-slate-600">Быстрый режим</span>
            <input
              type="checkbox"
              checked={fastMode}
              onChange={(e) => setSettings({ fastMode: e.target.checked })}
            />
          </label>
        </div>
      </div>
    </header>
  );
}
