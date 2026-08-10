import { useEffect, useRef, useState } from 'react';

interface Props {
  onSend: (text: string) => void;
  asOf: string;
  setAsOf: (date: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSend,
  asOf,
  setAsOf,
  disabled = false,
  placeholder = 'Write a blog about…',
}: Props) {
  const [text, setText] = useState('');
  const [showDate, setShowDate] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow the textarea.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    setShowDate(false);
    textareaRef.current?.focus();
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-lg shadow-slate-200/50 focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-100 transition">
        {/* Optional as-of date row */}
        {showDate && (
          <div className="flex items-center gap-2 px-4 pt-3">
            <label htmlFor="as-of-date" className="text-xs font-medium text-slate-500 whitespace-nowrap">
              As-of date
            </label>
            <input
              id="as-of-date"
              type="date"
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
              className="flex-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <div className="flex items-end gap-2 p-3">
          <textarea
            ref={textareaRef}
            aria-label="Message"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            rows={1}
            placeholder={disabled ? 'Generating your blog…' : placeholder}
            disabled={disabled}
            className="flex-1 resize-none outline-none text-sm leading-relaxed placeholder:text-slate-400 disabled:opacity-60 disabled:cursor-not-allowed max-h-40 py-2 px-1"
          />

          <button
            type="button"
            onClick={() => setShowDate((v) => !v)}
            title="Toggle as-of date"
            className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition text-base ${
              showDate
                ? 'bg-blue-100 text-blue-600'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700'
            }`}
          >
            📅
          </button>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled || !text.trim()}
            title="Send"
            className="shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-blue-600 text-white hover:bg-blue-700 active:scale-95 disabled:bg-slate-300 disabled:cursor-not-allowed transition"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M3.4 20.4l17.45-7.48a1 1 0 000-1.84L3.4 3.6a.993.993 0 00-1.39.91L2 9.12c0 .5.37.93.87.99L17 12 2.87 13.88c-.5.07-.87.5-.87 1l.01 4.61c0 .71.73 1.2 1.39.91z" />
            </svg>
          </button>
        </div>
      </div>

      <p className="text-center text-[11px] text-slate-400 mt-2">
        The agent may be inaccurate — verify important details before publishing.
      </p>
    </div>
  );
}
