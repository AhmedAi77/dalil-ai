import { Sparkles, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Translations } from "@/lib/i18n";
import type { Answer } from "@/lib/types";

export function AnswerCard({ answer, t, onDelete }: { answer: Answer; t: Translations; onDelete: () => void }) {
  return <article className="rounded-2xl border hairline surface p-4 shadow-[0_10px_35px_rgba(0,0,0,.12)] sm:p-5">
    {answer.transcription && <div className="mb-5 rounded-xl surface-muted px-4 py-3"><p className="text-muted mb-1 text-[10px] font-semibold uppercase tracking-[.12em]">{t.youSaid}</p><p className="text-sm">{answer.transcription}</p></div>}
    <div className="mb-4 flex items-center justify-between"><div className="flex items-center gap-2"><span className="brand-soft brand grid h-7 w-7 place-items-center rounded-lg"><Sparkles size={14}/></span><h2 className="text-sm font-semibold">Dalil AI</h2></div><button onClick={onDelete} className="text-muted rounded-lg p-2 transition hover:bg-red-950/40 hover:text-[var(--danger)]" aria-label={t.deleteAnswer} title={t.deleteAnswer}><Trash2 size={15}/></button></div>
    <div className="markdown text-[15px] leading-7"><ReactMarkdown remarkPlugins={[remarkGfm]}>{answer.answer}</ReactMarkdown></div>
    <div className="mt-7"><p className="text-muted mb-3 text-[10px] font-semibold uppercase tracking-[.12em]">{t.sources} · {answer.sources.length}</p><div className="grid gap-2 sm:grid-cols-2">{answer.sources.map((source, index) => <div key={`${source.document_id}-${source.chunk_index}-${index}`} className="flex items-center gap-3 rounded-xl border hairline surface p-3"><span className="brand-soft brand grid h-8 w-8 shrink-0 place-items-center rounded-lg text-xs font-semibold">{index + 1}</span><span className="min-w-0"><span className="block truncate text-xs font-medium">{source.filename}</span><span className="text-muted mt-0.5 block text-[10px]">{t.chunk} {source.chunk_index} · {(source.score * 100).toFixed(0)}%</span></span></div>)}</div></div>
  </article>;
}
