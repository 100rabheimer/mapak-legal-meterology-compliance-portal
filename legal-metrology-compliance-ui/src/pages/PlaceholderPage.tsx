import { Construction } from "lucide-react";

export function PlaceholderPage({ title, description }: { title: string; description: string }) {
 return <div className="mx-auto max-w-3xl py-12 text-center"><div className="app-card p-10"><div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><Construction className="h-7 w-7" /></div><h1 className="mt-5 text-2xl font-bold text-slate-900">{title}</h1><p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-500">{description}</p><p className="mt-6 text-xs font-medium uppercase tracking-wide text-slate-400">Module scaffold ready for FastAPI integration</p></div></div>;
}
