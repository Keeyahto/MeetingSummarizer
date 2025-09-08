import { useUiStore } from "../lib/store";
import Pill from "./ui/Pill";

export default function ResultHeader() {
  const { result, lastContext, language, fastMode } = useUiStore();
  if (!result) return null;
  return (
    <div className="flex items-center gap-2 mb-2">
      <Pill>{lastContext?.language || result.language}</Pill>
      {fastMode && <Pill color="amber">fast</Pill>}
    </div>
  );
}

