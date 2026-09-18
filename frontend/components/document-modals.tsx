"use client";

import { CircleAlert, FileText, LoaderCircle, Trash2, Upload, X } from "lucide-react";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import type { Translations } from "@/lib/i18n";
import type { KnowledgeDocument } from "@/lib/types";

export function AddDocumentModal({ t, onClose, onAdded }: { t: Translations; onClose: () => void; onAdded: (doc: KnowledgeDocument) => void }) {
  const [tab, setTab] = useState<"file" | "text">("file");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!title.trim()) { setError(t.titleRequired); return; }
    if (tab === "file" && !file) { setError(t.fileRequired); return; }
    if (tab === "text" && !content.trim()) { setError(t.textRequired); return; }
    setBusy(true);
    try {
      let document: KnowledgeDocument;
      if (tab === "file") {
        const form = new FormData();
        form.append("file", file!);
        form.append("title", title.trim());
        document = await api<KnowledgeDocument>("/documents/upload", { method: "POST", body: form });
      } else {
        document = await api<KnowledgeDocument>("/documents/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: title.trim(), text: content.trim() }),
        });
      }
      onAdded(document);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-black/45 p-3 backdrop-blur-[2px] sm:p-4" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><div className="surface app-shadow my-auto max-h-[calc(100dvh-24px)] w-full max-w-[560px] overflow-y-auto rounded-[20px] border hairline p-4 sm:rounded-[22px] sm:p-6">
    <div className="flex items-start justify-between"><div><h2 className="text-xl font-semibold tracking-[-.03em]">{t.addTitle}</h2><p className="text-muted mt-1 text-sm">{t.addSub}</p></div><button onClick={onClose} className="text-muted rounded-lg p-2 hover:surface-muted"><X size={18}/></button></div>
    <div className="surface-muted mt-6 grid grid-cols-2 rounded-xl p-1"><button type="button" onClick={() => setTab("file")} className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-medium ${tab === "file" ? "surface shadow-sm" : "text-muted"}`}><Upload size={15}/>{t.upload}</button><button type="button" onClick={() => setTab("text")} className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-medium ${tab === "text" ? "surface shadow-sm" : "text-muted"}`}><FileText size={15}/>{t.paste}</button></div>
    <form onSubmit={submit} className="mt-5">
      <label className="mb-4 block"><span className="mb-2 block text-xs font-medium">{t.title} <span className="brand">· {t.required}</span></span><input required maxLength={200} value={title} onChange={event => setTitle(event.target.value)} className="w-full rounded-xl border hairline surface-muted px-3.5 py-3 text-base outline-none focus:border-[var(--brand)] sm:text-sm"/></label>
      {tab === "file" ? <label className="surface-muted flex min-h-[150px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed hairline px-4 text-center hover:border-[var(--brand)] sm:min-h-[170px] sm:px-5"><input type="file" accept=".txt,.md,.pdf,.docx,.xlsx,.xlsm,text/markdown,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" className="hidden" onChange={event => setFile(event.target.files?.[0] ?? null)}/><span className="surface brand grid h-10 w-10 place-items-center rounded-xl border hairline"><Upload size={18}/></span><span className="mt-3 max-w-full truncate text-sm font-medium">{file?.name ?? t.choose}</span><span className="text-muted mt-1 text-xs">{file ? `${(file.size / 1024).toFixed(1)} KB` : t.drop}</span></label> : <label className="block"><span className="mb-2 flex items-center justify-between gap-2 text-xs font-medium"><span>{t.content}</span><span className="text-muted font-normal">{t.markdownHint}</span></span><textarea required rows={6} value={content} onChange={event => setContent(event.target.value)} placeholder={t.contentPlaceholder} className="w-full resize-none rounded-xl border hairline surface-muted px-3.5 py-3 text-base leading-6 outline-none focus:border-[var(--brand)] sm:text-sm"/></label>}
      {error && <p className="mt-3 flex items-center gap-2 text-xs text-red-600"><CircleAlert size={14}/>{error}</p>}
      <div className="mt-6 flex justify-end gap-2"><button type="button" onClick={onClose} className="text-muted rounded-xl px-4 py-2.5 text-xs font-semibold hover:surface-muted">{t.cancel}</button><button disabled={busy} className="flex items-center gap-2 rounded-xl brand-bg px-4 py-2.5 text-xs font-semibold text-white disabled:opacity-50">{busy && <LoaderCircle size={15} className="animate-spin"/>}{t.index}</button></div>
    </form>
  </div></div>;
}

export function ConfirmDeleteModal({ t, document, deleting, onClose, onConfirm }: { t: Translations; document: KnowledgeDocument; deleting: boolean; onClose: () => void; onConfirm: () => void }) {
  return <div className="fixed inset-0 z-[60] grid place-items-center bg-black/45 p-3 backdrop-blur-[2px] sm:p-4"><div className="surface app-shadow w-full max-w-sm rounded-[20px] border hairline p-5 sm:p-6"><div className="grid h-10 w-10 place-items-center rounded-xl bg-red-50 text-red-600 dark:bg-red-950/40"><Trash2 size={18}/></div><h2 className="mt-4 text-lg font-semibold">{t.deleteConfirm}</h2><p className="mt-1 break-words text-sm font-medium">{document.filename}</p><p className="text-muted mt-1 text-xs leading-5">{t.deleteSub}</p><div className="mt-6 grid grid-cols-2 gap-2 sm:flex sm:justify-end"><button onClick={onClose} className="text-muted rounded-xl px-4 py-3 text-xs font-semibold hover:surface-muted sm:py-2.5">{t.cancel}</button><button onClick={onConfirm} disabled={deleting} className="flex items-center justify-center gap-2 rounded-xl bg-red-600 px-4 py-3 text-xs font-semibold text-white disabled:opacity-50 sm:py-2.5">{deleting && <LoaderCircle size={14} className="animate-spin"/>}{deleting ? t.deleting : t.delete}</button></div></div></div>;
}

