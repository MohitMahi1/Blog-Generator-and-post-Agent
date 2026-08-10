import { useState } from 'react';
import type { ChatMessage as ChatMessageType } from '../types/blog';
import BlogArticle from './BlogArticle';
import PlanTab from './PlanTab';
import EvidenceTab from './EvidenceTab';
import ImagesTab from './ImagesTab';
import LogsTab from './LogsTab';

export interface Chip {
  label: string;
  value: string;
  icon?: string;
}

interface Props {
  message: ChatMessageType;
  chips?: Chip[];
  onChip?: (value: string) => void;
}

const detailTabs = [
  { id: 'preview', label: '📝 Preview' },
  { id: 'plan', label: '🧩 Plan' },
  { id: 'evidence', label: '🔎 Evidence' },
  { id: 'images', label: '🖼️ Images' },
  { id: 'logs', label: '🧾 Logs' },
] as const;

type DetailTab = (typeof detailTabs)[number]['id'];

function AssistantAvatar() {
  return (
    <div className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
      ✍️
    </div>
  );
}

function BlogCard({ blog }: { blog: ChatMessageType & { kind: 'blog' } }) {
  const [tab, setTab] = useState<DetailTab>('preview');
  const title = blog.blog.blog_title || 'Untitled Blog';
  const markdown = blog.blog.final_markdown || '';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 bg-gradient-to-r from-slate-50 to-blue-50/50 border-b border-slate-200">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-semibold text-slate-900 leading-snug">{title}</h3>
          <span className="shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 whitespace-nowrap">
            ✅ Ready
          </span>
        </div>
        <div className="flex flex-wrap gap-2 mt-2 text-[11px] text-slate-500">
          <span className="px-2 py-0.5 rounded-full bg-white border border-slate-200">
            Mode: {blog.blog.mode}
          </span>
          <span className="px-2 py-0.5 rounded-full bg-white border border-slate-200">
            {blog.blog.sections_count} sections
          </span>
          {blog.blog.needs_research && (
            <span className="px-2 py-0.5 rounded-full bg-white border border-slate-200">
              🔎 researched
            </span>
          )}
        </div>
      </div>

      {/* Detail tabs */}
      <div role="tablist" aria-label="Blog details" className="flex gap-1 px-3 pt-2.5 pb-0 overflow-x-auto border-b border-slate-100 bg-slate-50/60">
        {detailTabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 text-xs font-medium rounded-t-lg whitespace-nowrap transition ${
              tab === t.id
                ? 'bg-white border border-slate-200 border-b-white text-blue-600'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-5 max-h-[520px] overflow-y-auto">
        {tab === 'preview' &&
          (markdown ? (
            <BlogArticle markdown={markdown} />
          ) : (
            <div className="text-slate-500 text-sm">No markdown available.</div>
          ))}
        {tab === 'plan' && <PlanTab plan={blog.blog.plan || null} />}
        {tab === 'evidence' && (
          <EvidenceTab evidence={blog.blog.evidence || []} queries={blog.blog.queries || []} />
        )}
        {tab === 'images' && <ImagesTab specs={blog.blog.image_specs || []} />}
        {tab === 'logs' && <LogsTab logs={blog.blog.logs || []} />}
      </div>
    </div>
  );
}

export default function ChatMessage({ message, chips, onChip }: Props) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end chat-msg-in">
        <div className="max-w-[80%] bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm leading-relaxed shadow-sm">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 chat-msg-in">
      <AssistantAvatar />
      <div className="flex-1 min-w-0 max-w-[92%]">
        {message.kind === 'blog' ? (
          <>
            {message.text && (
              <div className="bg-slate-100 border border-slate-200 text-slate-800 rounded-2xl rounded-tl-md px-4 py-2.5 text-sm leading-relaxed mb-3 inline-block whitespace-pre-wrap">
                {message.text}
              </div>
            )}
            <BlogCard blog={message} />
          </>
        ) : (
          <div className="bg-slate-100 border border-slate-200 text-slate-800 rounded-2xl rounded-tl-md px-4 py-2.5 text-sm leading-relaxed inline-block whitespace-pre-wrap">
            {message.text}
          </div>
        )}

        {/* Quick-reply chips */}
        {chips && chips.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {chips.map((chip) => (
              <button
                key={chip.value}
                onClick={() => onChip?.(chip.value)}
                className="px-3.5 py-2 text-xs font-medium rounded-full border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300 active:scale-95 transition shadow-sm"
              >
                {chip.icon && <span className="mr-1">{chip.icon}</span>}
                {chip.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
