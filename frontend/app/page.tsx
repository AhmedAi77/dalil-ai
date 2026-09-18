"use client";

import {
  ArrowUp, Check, ChevronDown, CircleAlert, FileText, Globe2, LoaderCircle,
  LogOut, Menu, MessageSquare, Mic, PanelLeftClose, Plus, Search, Sparkles,
  Square, Trash2,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AnswerCard } from "@/components/answer-card";
import { AuthScreen } from "@/components/auth-screen";
import { BrandLogo } from "@/components/brand-logo";
import { AddDocumentModal, ConfirmDeleteModal } from "@/components/document-modals";
import { EmptyLibrary } from "@/components/empty-library";
import { api } from "@/lib/api";
import { copy, type Locale } from "@/lib/i18n";
import type { Answer, ChatSession, KnowledgeDocument, Notice, User } from "@/lib/types";

const makeId = () => crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [historyReady, setHistoryReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [modal, setModal] = useState(false);
  const [sidebar, setSidebar] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(true);
  const [notice, setNotice] = useState<Notice>(null);
  const [search, setSearch] = useState("");
  const [locale, setLocale] = useState<Locale>("en");
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeDocument | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const t = copy[locale];
  const activeChat = chats.find(chat => chat.id === activeChatId) ?? null;

  const showNotice = useCallback((next: Notice) => {
    setNotice(next);
    window.setTimeout(() => setNotice(null), 4200);
  }, []);

  useEffect(() => {
    const savedLocale = localStorage.getItem("dalil-locale") ?? localStorage.getItem("contexta-locale");
    // Restore the browser-only preference after hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLocale(savedLocale === "ar" ? "ar" : "en");
  }, []);

  useEffect(() => {
    fetch("/backend/auth/me", { cache: "no-store", credentials: "same-origin" })
      .then(async response => { if (response.ok) setUser(await response.json()); })
      .finally(() => setAuthLoading(false));
  }, []);

  useEffect(() => {
    if (!user) return;
    api<KnowledgeDocument[]>("/documents").then(setDocuments).catch(() => showNotice({ kind: "error", text: t.backend })).finally(() => setLoading(false));
    Promise.resolve().then(() => {
      try {
        const saved = localStorage.getItem(`dalil-chats:${user.id}`);
        const restored = saved ? JSON.parse(saved) as ChatSession[] : [];
        setChats(restored);
        if (restored[0]) { setActiveChatId(restored[0].id); setSelected(restored[0].document_id); }
      } catch { setChats([]); }
      setHistoryReady(true);
    });
  }, [user, showNotice, t.backend]);

  useEffect(() => {
    if (user && historyReady) localStorage.setItem(`dalil-chats:${user.id}`, JSON.stringify(chats));
  }, [chats, historyReady, user]);

  useEffect(() => {
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = locale;
    localStorage.setItem("dalil-locale", locale);
  }, [locale]);

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setRecordingSeconds(value => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [recording]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [activeChat?.turns.length, asking]);

  const filtered = useMemo(() => documents.filter(d => d.filename.toLowerCase().includes(search.toLowerCase())), [documents, search]);
  const selectedDoc = documents.find(d => d.id === selected);

  function newChat() {
    const now = new Date().toISOString();
    const chat: ChatSession = { id: makeId(), title: t.untitledChat, document_id: null, turns: [], created_at: now, updated_at: now };
    setChats(items => [chat, ...items]);
    setActiveChatId(chat.id); setSelected(null); setQuery(""); setSidebar(false);
  }

  function openChat(chat: ChatSession) {
    setActiveChatId(chat.id); setSelected(chat.document_id); setQuery(""); setSidebar(false);
  }

  function removeChat(id: string) {
    const remaining = chats.filter(chat => chat.id !== id);
    setChats(remaining);
    if (activeChatId === id) {
      setActiveChatId(remaining[0]?.id ?? null);
      setSelected(remaining[0]?.document_id ?? null);
      setQuery("");
    }
  }

  function selectDocument(id: string | null) {
    setSelected(id);
    if (activeChatId) setChats(items => items.map(chat => chat.id === activeChatId ? { ...chat, document_id: id, updated_at: new Date().toISOString() } : chat));
  }

  async function ask(question = query, audio?: Blob) {
    if ((!question.trim() && !audio) || asking) return;
    setAsking(true);
    const chatId = activeChatId ?? makeId();
    try {
      let result: Answer;
      if (audio) {
        const extension = audio.type.includes("ogg") ? "ogg" : audio.type.includes("mp4") ? "m4a" : "webm";
        const data = new FormData(); data.append("audio", audio, `question.${extension}`);
        result = await api<Answer>(`/speech/query${selected ? `?document_id=${encodeURIComponent(selected)}` : ""}`, { method: "POST", body: data });
      } else {
        result = await api<Answer>("/query", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: question.trim(), document_id: selected }) });
      }
      const actualQuestion = result.transcription?.trim() || question.trim();
      const now = new Date().toISOString();
      const turn = { id: makeId(), question: actualQuestion, answer: result, created_at: now };
      setChats(items => {
        const existing = items.find(chat => chat.id === chatId);
        const updated: ChatSession = existing
          ? { ...existing, title: existing.turns.length ? existing.title : actualQuestion.slice(0, 52), document_id: selected, turns: [...existing.turns, turn], updated_at: now }
          : { id: chatId, title: actualQuestion.slice(0, 52), document_id: selected, turns: [turn], created_at: now, updated_at: now };
        return [updated, ...items.filter(chat => chat.id !== chatId)];
      });
      setActiveChatId(chatId); setQuery("");
    } catch (error) { showNotice({ kind: "error", text: error instanceof Error ? error.message : t.backend }); }
    finally { setAsking(false); }
  }

  function removeTurn(turnId: string) {
    setChats(items => items.map(chat => chat.id === activeChatId ? { ...chat, turns: chat.turns.filter(turn => turn.id !== turnId), updated_at: new Date().toISOString() } : chat));
  }

  async function toggleRecording() {
    if (recording) { recorder.current?.stop(); return; }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") { showNotice({ kind: "error", text: t.micUnsupported }); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferredType = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"].find(type => MediaRecorder.isTypeSupported(type));
      const mediaRecorder = preferredType ? new MediaRecorder(stream, { mimeType: preferredType }) : new MediaRecorder(stream);
      chunks.current = []; recorder.current = mediaRecorder;
      mediaRecorder.ondataavailable = event => { if (event.data.size) chunks.current.push(event.data); };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop()); setRecording(false);
        const audio = new Blob(chunks.current, { type: mediaRecorder.mimeType || "audio/webm" });
        if (!audio.size) { showNotice({ kind: "error", text: t.emptyRecording }); return; }
        ask("", audio);
      };
      mediaRecorder.onerror = () => { stream.getTracks().forEach(track => track.stop()); setRecording(false); showNotice({ kind: "error", text: t.emptyRecording }); };
      setRecordingSeconds(0); mediaRecorder.start(); setRecording(true);
    } catch { showNotice({ kind: "error", text: t.micDenied }); }
  }

  async function removeDocument() {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api(`/documents/${deleteTarget.id}`, { method: "DELETE" });
      setDocuments(items => items.filter(item => item.id !== deleteTarget.id));
      if (selected === deleteTarget.id) selectDocument(null);
      setDeleteTarget(null); showNotice({ kind: "success", text: t.deleteSuccess });
    } catch (error) { showNotice({ kind: "error", text: error instanceof Error ? error.message : t.backend }); }
    finally { setDeleting(false); }
  }

  async function logout() {
    await api<{ logged_out: boolean }>("/auth/logout", { method: "POST" });
    setUser(null); setDocuments([]); setChats([]); setActiveChatId(null); setSelected(null); setHistoryReady(false);
  }

  function authenticated(nextUser: User) {
    setLoading(true); setUser(nextUser);
    showNotice({ kind: "success", text: t.welcomeUser.replace("{name}", nextUser.name.split(" ")[0]) });
  }

  if (authLoading) return <div className="ambient grid min-h-screen place-items-center"><LoaderCircle className="brand animate-spin" size={28}/></div>;
  if (!user) return <AuthScreen t={t} locale={locale} onLocale={() => setLocale(locale === "en" ? "ar" : "en")} onAuthenticated={authenticated}/>;

  return <main className="ambient h-[100dvh] w-full overflow-hidden" dir={locale === "ar" ? "rtl" : "ltr"}>
    <div className="flex h-full min-h-0 w-full overflow-hidden surface">
      {sidebar && <button className="fixed inset-0 z-30 bg-black/40 lg:hidden" aria-label={t.close} onClick={() => setSidebar(false)} />}
      <aside className={`fixed inset-y-0 z-40 flex h-full min-h-0 w-[min(300px,88vw)] flex-col overflow-hidden border-e hairline surface transition-transform duration-300 lg:static lg:w-[300px] lg:translate-x-0 ${sidebar ? "translate-x-0" : locale === "ar" ? "translate-x-full" : "-translate-x-full"}`}>
        <div className="flex h-[76px] items-center justify-between px-5"><BrandLogo /><button className="rounded-lg p-2 text-muted hover:surface-muted lg:hidden" onClick={() => setSidebar(false)}><PanelLeftClose size={18}/></button></div>
        <div className="px-4"><button onClick={newChat} className="flex w-full items-center justify-center gap-2 rounded-xl brand-bg px-3 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110"><Plus size={17}/>{t.newChat}</button></div>

        <div className="mt-6 flex items-center justify-between px-5"><span className="text-muted text-[11px] font-semibold uppercase tracking-[.12em]">{t.chats}</span><span className="text-muted text-[10px]">{chats.length}</span></div>
        <div className="scrollbar mt-2 min-h-0 flex-1 overflow-y-auto px-3">
          {chats.map(chat => <div key={chat.id} className={`group mb-1 flex items-center gap-1 rounded-xl p-1 transition ${activeChatId === chat.id ? "brand-soft" : "hover:surface-muted"}`}>
            <button onClick={() => openChat(chat)} className="flex min-w-0 flex-1 items-center gap-2.5 px-2 py-2 text-start"><MessageSquare size={15} className={activeChatId === chat.id ? "brand shrink-0" : "text-muted shrink-0"}/><span className="min-w-0"><span className="block truncate text-[13px] font-medium">{chat.title}</span><span className="text-muted block text-[10px]">{chat.turns.length} {t.messages}</span></span></button>
            <button onClick={() => removeChat(chat.id)} className="text-muted rounded-lg p-2 opacity-0 transition hover:text-[var(--danger)] group-hover:opacity-100 focus:opacity-100" aria-label={t.deleteChat}><Trash2 size={14}/></button>
          </div>)}
          {chats.length === 0 && <p className="text-muted px-3 py-5 text-center text-xs leading-5">{t.noChats}</p>}
        </div>

        <div className="mx-3 mt-3 border-t hairline pt-3">
          <button onClick={() => setLibraryOpen(value => !value)} className="text-muted flex w-full items-center gap-2 rounded-lg px-2 py-2 text-[11px] font-semibold uppercase tracking-[.12em] hover:surface-muted"><FileText size={14}/>{t.library}<ChevronDown size={14} className={`ms-auto transition ${libraryOpen ? "rotate-180" : ""}`}/></button>
          {libraryOpen && <div className="pb-2">
            <div className="mx-1 mt-1 flex items-center gap-2 rounded-xl border hairline surface-muted px-3 py-2"><Search size={14} className="text-muted"/><input value={search} onChange={e => setSearch(e.target.value)} placeholder={t.search} className="min-w-0 flex-1 bg-transparent text-xs outline-none"/><button onClick={() => setModal(true)} className="brand" aria-label={t.add}><Plus size={15}/></button></div>
            <div className="scrollbar mt-1 max-h-40 overflow-y-auto">
              <button onClick={() => selectDocument(null)} className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-start text-xs ${selected === null ? "brand" : "text-muted hover:surface-muted"}`}><Sparkles size={14}/><span className="truncate">{t.all}</span></button>
              {filtered.map(doc => <div key={doc.id} className={`group flex items-center rounded-lg ${selected === doc.id ? "surface-muted" : "hover:surface-muted"}`}><button onClick={() => selectDocument(doc.id)} className="flex min-w-0 flex-1 items-center gap-2 px-3 py-2 text-start text-xs"><FileText size={13} className="brand shrink-0"/><span className="truncate">{doc.filename}</span></button><button onClick={() => setDeleteTarget(doc)} className="text-muted p-2 opacity-0 hover:text-[var(--danger)] group-hover:opacity-100"><Trash2 size={12}/></button></div>)}
            </div>
          </div>}
        </div>

        <div className="border-t hairline p-4"><div className="mb-3 flex items-center gap-3 px-2"><span className="brand-soft brand grid h-9 w-9 shrink-0 place-items-center rounded-xl text-xs font-semibold">{user.name.slice(0, 1).toUpperCase()}</span><span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold">{user.name}</span><span className="text-muted block truncate text-[10px]">{user.email}</span></span><button onClick={logout} className="text-muted rounded-lg p-2 hover:text-[var(--danger)]" title={t.logout}><LogOut size={15}/></button></div><button onClick={() => setLocale(locale === "en" ? "ar" : "en")} className="text-muted surface-muted flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-medium hover:surface"><Globe2 size={15}/>{locale === "en" ? "العربية" : "English"}</button></div>
      </aside>

      <section className="relative flex h-full min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center justify-between border-b hairline px-3 sm:h-[76px] sm:px-5 md:px-7"><div className="flex min-w-0 items-center gap-3"><button onClick={() => setSidebar(true)} className="rounded-lg p-2 text-muted hover:surface-muted lg:hidden" aria-label={t.menu}><Menu size={20}/></button><div className="min-w-0"><p className="truncate text-sm font-semibold">{activeChat?.title ?? t.newChat}</p><p className="text-muted truncate text-[10px]">{selectedDoc?.filename ?? t.all}</p></div></div><button onClick={newChat} className="text-muted flex items-center gap-2 rounded-xl border hairline px-3 py-2 text-xs font-medium hover:surface-muted"><Plus size={15}/><span className="hidden sm:inline">{t.newChat}</span></button></header>

        <div className="scrollbar min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-6 sm:px-5 md:px-8">
          <div className="mx-auto max-w-[820px]">
            {!activeChat?.turns.length && <div className="fade-up flex min-h-[38vh] flex-col justify-center"><p className="brand mb-3 text-base font-semibold">{t.welcome.replace("{name}", user.name)}</p><h1 className="max-w-2xl text-[30px] font-semibold leading-[1.1] tracking-[-.04em] sm:text-4xl md:text-[46px]">{t.headline}</h1><p className="text-muted mt-4 max-w-xl text-sm leading-6 md:text-[15px]">{t.subhead}</p></div>}
            {documents.length === 0 && !loading ? <EmptyLibrary t={t} onAdd={() => setModal(true)}/> : <div className="space-y-7">
              {activeChat?.turns.map(turn => <div key={turn.id} className="fade-up">
                <div className="mb-3 flex justify-end"><div className="max-w-[85%] rounded-2xl rounded-ee-md bg-[var(--brand)] px-4 py-3 text-sm leading-6 text-slate-950 sm:max-w-[72%]">{turn.question}</div></div>
                <AnswerCard answer={turn.answer} t={t} onDelete={() => removeTurn(turn.id)}/>
              </div>)}
              {asking && <div className="text-muted flex items-center gap-3 rounded-2xl border hairline surface p-4 text-sm"><LoaderCircle size={17} className="brand animate-spin"/>{t.thinking}</div>}
            </div>}
            <div ref={bottomRef}/>
          </div>
        </div>

        {documents.length > 0 && <div className="shrink-0 border-t hairline bg-[color-mix(in_srgb,var(--surface)_94%,transparent)] px-3 py-3 backdrop-blur-xl sm:px-5 sm:py-4 md:px-8"><form onSubmit={event => { event.preventDefault(); ask(); }} className="mx-auto max-w-[820px] rounded-2xl border hairline surface p-1.5 shadow-[0_10px_35px_rgba(0,0,0,.2)] focus-within:border-[var(--brand)]"><textarea value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }} rows={2} placeholder={t.placeholder} className="w-full resize-none bg-transparent px-3.5 py-2.5 text-[15px] leading-6 outline-none placeholder:text-[var(--muted)]"/><div className="flex items-center justify-between border-t hairline px-1.5 pt-1.5"><button type="button" onClick={toggleRecording} disabled={asking} className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium ${recording ? "bg-red-950/50 text-red-300" : "text-muted hover:surface-muted"}`}>{recording ? <><span className="recording-pulse h-2 w-2 rounded-full bg-red-400"/><Square size={12} fill="currentColor"/>{t.stop}<span className="font-mono">{String(Math.floor(recordingSeconds / 60)).padStart(2, "0")}:{String(recordingSeconds % 60).padStart(2, "0")}</span></> : <><Mic size={16}/>{t.record}</>}</button><button disabled={!query.trim() || asking} className="grid h-9 w-9 place-items-center rounded-xl brand-bg text-slate-950 transition disabled:opacity-35" aria-label={t.ask}>{asking ? <LoaderCircle size={17} className="animate-spin"/> : <ArrowUp size={18}/>}</button></div></form></div>}
      </section>
    </div>

    {modal && <AddDocumentModal t={t} onClose={() => setModal(false)} onAdded={doc => { setDocuments(items => [doc, ...items]); selectDocument(doc.id); setModal(false); showNotice({ kind: "success", text: t.uploadSuccess }); }}/>} 
    {deleteTarget && <ConfirmDeleteModal t={t} document={deleteTarget} deleting={deleting} onClose={() => setDeleteTarget(null)} onConfirm={removeDocument}/>} 
    {notice && <div className={`fixed bottom-3 start-3 end-3 z-[80] flex items-center justify-center gap-2 rounded-xl border px-4 py-3 text-center text-sm shadow-xl sm:bottom-5 sm:start-1/2 sm:end-auto sm:-translate-x-1/2 ${notice.kind === "error" ? "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200" : "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"}`}>{notice.kind === "error" ? <CircleAlert size={17}/> : <Check size={17}/>}<span>{notice.text}</span></div>}
  </main>;
}
