import { File, Plus } from "lucide-react";

import type { Translations } from "@/lib/i18n";

export function EmptyLibrary({ t, onAdd }: { t: Translations; onAdd: () => void }) {
  return <div className="fade-up-delay grid min-h-[310px] place-items-center rounded-2xl border border-dashed hairline surface-muted px-6 text-center"><div><div className="brand-soft brand mx-auto grid h-12 w-12 place-items-center rounded-2xl"><File size={21}/></div><h2 className="mt-5 text-lg font-semibold tracking-[-.02em]">{t.noDocs}</h2><p className="text-muted mx-auto mt-2 max-w-md text-sm leading-6">{t.noDocsSub}</p><button onClick={onAdd} className="mt-6 inline-flex items-center gap-2 rounded-xl brand-bg px-4 py-2.5 text-xs font-semibold text-white"><Plus size={16}/>{t.add}</button></div></div>;
}
