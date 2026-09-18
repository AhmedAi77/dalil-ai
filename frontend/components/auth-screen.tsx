"use client";

import { CircleAlert, Globe2, LoaderCircle, ShieldCheck } from "lucide-react";
import { FormEvent, useState } from "react";

import { BrandLogo } from "@/components/brand-logo";
import { api } from "@/lib/api";
import type { Locale, Translations } from "@/lib/i18n";
import type { User } from "@/lib/types";

type Props = {
  t: Translations;
  locale: Locale;
  onLocale: () => void;
  onAuthenticated: (user: User) => void;
};

export function AuthScreen({ t, locale, onLocale, onAuthenticated }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const body = mode === "register"
        ? { name: name.trim(), email: email.trim(), password }
        : { email: email.trim(), password };
      const user = await api<User>(`/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      onAuthenticated(user);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  function selectMode(nextMode: "login" | "register") {
    setMode(nextMode);
    setError("");
  }

  return (
    <main className="ambient relative min-h-screen overflow-hidden p-4 sm:p-6" dir={locale === "ar" ? "rtl" : "ltr"}>
      <div className="absolute start-4 top-4 sm:start-7 sm:top-7"><BrandLogo /></div>
      <button onClick={onLocale} className="surface text-muted absolute end-4 top-4 z-10 flex items-center gap-2 rounded-xl border hairline px-3 py-2 text-xs sm:end-7 sm:top-7"><Globe2 size={15}/>{locale === "en" ? "العربية" : "English"}</button>
      <div className="mx-auto grid min-h-[calc(100vh-32px)] max-w-6xl items-center pt-20 sm:min-h-[calc(100vh-48px)] sm:pt-12 lg:grid-cols-[1fr_460px] lg:gap-20">
        <section className="hidden lg:block"><span className="brand-soft brand inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"><ShieldCheck size={14}/>{t.private}</span><h1 className="mt-6 max-w-xl text-6xl font-semibold leading-[1.02] tracking-[-.055em]">{t.authTitle}</h1><p className="text-muted mt-6 max-w-lg text-lg leading-8">{t.authSub}</p></section>
        <section className="surface app-shadow w-full rounded-[24px] border hairline p-5 sm:p-8">
          <div className="lg:hidden"><span className="brand-soft brand inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[11px] font-semibold"><ShieldCheck size={13}/>{t.private}</span><h1 className="mt-4 text-3xl font-semibold leading-tight tracking-[-.04em]">{t.authTitle}</h1><p className="text-muted mt-2 text-sm leading-6">{t.authSub}</p></div>
          <div className="mt-7 grid grid-cols-2 rounded-xl surface-muted p-1 lg:mt-0"><button type="button" onClick={() => selectMode("login")} className={`rounded-lg px-3 py-2.5 text-xs font-semibold ${mode === "login" ? "surface brand shadow-sm" : "text-muted"}`}>{t.signIn}</button><button type="button" onClick={() => selectMode("register")} className={`rounded-lg px-3 py-2.5 text-xs font-semibold ${mode === "register" ? "surface brand shadow-sm" : "text-muted"}`}>{t.createAccount}</button></div>
          <form onSubmit={submit} className="mt-6 space-y-4">
            {mode === "register" && <label className="block"><span className="mb-2 block text-xs font-medium">{t.name}</span><input required minLength={2} maxLength={100} autoComplete="name" value={name} onChange={event => setName(event.target.value)} className="surface-muted w-full rounded-xl border hairline px-3.5 py-3 text-base outline-none focus:border-[var(--brand)] sm:text-sm"/></label>}
            <label className="block"><span className="mb-2 block text-xs font-medium">{t.email}</span><input required type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} className="surface-muted w-full rounded-xl border hairline px-3.5 py-3 text-base outline-none focus:border-[var(--brand)] sm:text-sm"/></label>
            <label className="block"><span className="mb-2 flex justify-between gap-2 text-xs font-medium"><span>{t.password}</span>{mode === "register" && <span className="text-muted font-normal">{t.passwordHint}</span>}</span><input required minLength={mode === "register" ? 8 : 1} maxLength={128} type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} value={password} onChange={event => setPassword(event.target.value)} className="surface-muted w-full rounded-xl border hairline px-3.5 py-3 text-base outline-none focus:border-[var(--brand)] sm:text-sm"/></label>
            {error && <p className="flex items-start gap-2 rounded-xl border border-red-900/70 bg-red-950/40 px-3 py-2.5 text-xs text-red-200"><CircleAlert size={15} className="mt-px shrink-0"/>{error}</p>}
            <button disabled={busy} className="brand-bg flex min-h-12 w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50">{busy && <LoaderCircle size={16} className="animate-spin"/>}{mode === "login" ? t.signIn : t.createAccount}</button>
          </form>
          <p className="text-muted mt-5 text-center text-xs">{mode === "login" ? t.noAccount : t.haveAccount} <button type="button" onClick={() => selectMode(mode === "login" ? "register" : "login")} className="brand font-semibold">{mode === "login" ? t.createAccount : t.signIn}</button></p>
        </section>
      </div>
    </main>
  );
}

