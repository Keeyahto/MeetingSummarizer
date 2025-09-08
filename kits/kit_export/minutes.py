from datetime import datetime
from pathlib import Path
from kits.kit_common.config import settings


def build_minutes_md(transcript: dict, summary: dict) -> str:
    dt = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append(f"# Протокол встречи — {dt}")
    lines.append("")
    lines.append("## Краткое резюме")
    lines.append(summary.get("tldr", ""))
    lines.append("")
    lines.append("## Решения")
    for d in summary.get("decisions", []) or []:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("## Пункты действий")
    for a in summary.get("action_items", []) or []:
        owner = a.get("owner") or "не указан"
        due = a.get("due") or "не указан"
        lines.append(f"- [ ] {a.get('text')} (ответственный: {owner}, срок: {due})")
    lines.append("")
    lines.append("## Риски")
    for r in summary.get("risks", []) or []:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Темы (временная шкала)")
    for t in transcript.get("topics", []) or []:
        lines.append(f"- {t.get('start')}–{t.get('end')} — {t.get('title')}")
    lines.append("")
    lines.append("## Транскрипт (участники)")
    for seg in transcript.get("segments", []) or []:
        start = seg.get("start", 0)
        hh = int(start // 3600)
        mm = int((start % 3600) // 60)
        ss = int(start % 60)
        ts = f"[{hh:02}:{mm:02}:{ss:02}]"
        lines.append(f"{ts} {seg.get('speaker', 'Участник')}: {seg.get('text','')}")
    md = "\n".join(lines)
    cap = settings.EXPORT_MD_MAX_CHARS
    return md if len(md) <= cap else md[:cap] + "\n...\n"

