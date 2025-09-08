export default function Footer() {
  return (
    <footer className="border-t text-sm text-slate-600">
      <div className="container py-4 flex items-center justify-between">
        <div>© {new Date().getFullYear()} Сводка встреч</div>
        <a className="hover:underline" href="/demo">Открыть демо</a>
      </div>
    </footer>
  );
}
