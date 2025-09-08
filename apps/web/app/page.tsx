import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="text-center space-y-3">
        <h1 className="text-3xl md:text-5xl font-bold">Сводка встреч</h1>
        <p className="text-slate-600">WhisperX, диаризация, таймкоды слов, локальная LLM</p>
        <div className="flex justify-center gap-3">
          <Link className="px-4 py-2 bg-blue-600 text-white rounded-lg" href="/demo">Открыть демо</Link>
          <Link className="px-4 py-2 border rounded-lg" href="/health">Состояние</Link>
        </div>
      </section>
      <section className="grid sm:grid-cols-2 gap-4">
        {[
          ["TL;DR", "Короткое резюме встречи"],
          ["Action Items", "Ответственные и сроки"],
          ["Decisions & Risks", "Фиксация решений и рисков"],
          ["SRT/VTT", "Субтитры с точными таймкодами"],
          ["Темы", "Опциональная временная шкала"],
          ["Локально", "Без облачных загрузок"],
        ].map(([title, desc]) => (
          <div key={title} className="rounded-2xl shadow-sm p-4 bg-white">
            <div className="font-semibold">{title}</div>
            <div className="text-slate-600 text-sm">{desc}</div>
          </div>
        ))}
      </section>
      <section className="rounded-2xl shadow-sm p-4 bg-white">
        <h2 className="font-semibold mb-2">Как это работает</h2>
        <ol className="list-decimal list-inside text-slate-700 space-y-1">
          <li>Загрузите аудио</li>
          <li>Распознавание WhisperX (+ выравнивание/диаризация)</li>
          <li>LLM генерирует TL;DR, действия, решения и риски</li>
          <li>Скачайте протокол и субтитры</li>
        </ol>
      </section>
    </div>
  );
}
