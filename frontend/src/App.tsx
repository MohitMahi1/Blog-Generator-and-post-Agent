import { useCallback, useEffect, useRef, useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatInput from './components/ChatInput';
import ChatMessage, { type Chip } from './components/ChatMessage';
import { generateBlog, startNewSession, fetchSessionBlogs, fetchBlogById } from './api/blog';
import { downloadByFormat } from './utils/download';
import type {
  ChatMessage as ChatMessageType,
  BlogListItem,
  DownloadFormat,
  FlowStage,
  GenerateResponse,
} from './types/blog';

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : 'm_' + Math.random().toString(36).slice(2, 10);

/* ------------------------- Conversation helpers ------------------------- */

const YES_RE = /^(y|yes|yeah|yep|sure|ok|okay|please)$/i;
const NO_RE = /^(n|no|nope|nah|not\s*now)$/i;

function parseDownloadAnswer(text: string): boolean | null {
  if (YES_RE.test(text.trim())) return true;
  if (NO_RE.test(text.trim())) return false;
  return null;
}

function errorMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
    if (typeof detail === 'string' && detail) return detail;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}

function parseFormat(text: string): DownloadFormat | null {
  const t = text.toLowerCase();
  if (/(^|\s)(md|markdown)(\s|$)/.test(t)) return 'md';
  if (t.includes('pdf')) return 'pdf';
  if (/(^|\s)(word|doc|docx)(\s|$)/.test(t)) return 'word';
  return null;
}

const CHIPS: Partial<Record<FlowStage, Chip[]>> = {
  ask_download: [
    { label: 'Yes, download it', value: 'yes' },
    { label: 'No', value: 'no' },
  ],
  ask_format: [
    { label: 'Markdown (.md)', value: 'md', icon: '📄' },
    { label: 'PDF', value: 'pdf', icon: '📑' },
    { label: 'Word (.doc)', value: 'word', icon: '📝' },
  ],
  ask_post: [
    { label: 'Yes, post it', value: 'yes' },
    { label: 'No', value: 'no' },
  ],
};

const SUGGESTED_TOPICS = [
  'Introduction to LangGraph with real examples',
  'The rise of AI agents in 2026',
  'How vector databases work',
];

/* --------------------------------- App ---------------------------------- */

export default function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [stage, setStage] = useState<FlowStage>('idle');
  const [loading, setLoading] = useState(false);
  const [asOf, setAsOf] = useState(new Date().toISOString().slice(0, 10));

  // Session & history states. startNewSession() wipes the previous session's
  // blogs on page load (refresh = old blogs deleted) and issues a fresh id;
  // clicking "New chat" keeps this same id so blogs stay for 15 minutes.
  const [sessionId] = useState<string>(() => startNewSession());
  const [recentBlogs, setRecentBlogs] = useState<BlogListItem[]>([]);
  const [activeBlogId, setActiveBlogId] = useState<string | null>(null);

  const lastBlogRef = useRef<GenerateResponse | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const pushMessage = useCallback((msg: ChatMessageType) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  // Load session history without calling setState synchronously inside the effect.
  useEffect(() => {
    let cancelled = false;
    fetchSessionBlogs(sessionId)
      .then((list) => {
        if (!cancelled) setRecentBlogs(list);
      })
      .catch((err) => console.error('Failed to load session blogs:', err));
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const refreshRecentBlogs = useCallback(async () => {
    try {
      const list = await fetchSessionBlogs(sessionId);
      setRecentBlogs(list);
    } catch (err) {
      console.error('Failed to load session blogs:', err);
    }
  }, [sessionId]);

  // Auto-scroll to the newest message, but only when the user is already near
  // the bottom so reading a long blog isn't interrupted.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 160;
    if (nearBottom) {
      endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, stage, loading]);

  /* ---------------------------- Generation ------------------------------ */

  const startGeneration = useCallback(
    async (topic: string) => {
      if (loading) return;
      pushMessage({ id: uid(), role: 'user', kind: 'text', text: topic });
      setLoading(true);
      setStage('generating');
      setActiveBlogId(null);
      lastBlogRef.current = null;

      try {
        const data = await generateBlog(topic, asOf, sessionId);
        lastBlogRef.current = data;
        if (data.blog_id) setActiveBlogId(data.blog_id);

        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'blog',
          text: `Here's your blog "${data.blog_title || 'Untitled'}" 🎉 (mode: ${data.mode}, ${data.sections_count} sections).`,
          blog: data,
        });
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'Would you like to download it?',
        });
        setStage('ask_download');
        refreshRecentBlogs();
      } catch (err) {
        console.error(err);
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: `❌ Sorry, something went wrong while generating the blog: ${errorMessage(err)}. Please try again.`,
        });
        setStage('done');
      } finally {
        setLoading(false);
      }
    },
    [loading, asOf, sessionId, pushMessage, refreshRecentBlogs]
  );

  /* ------------------------- Conversation flow -------------------------- */

  const handleDownloadAnswer = useCallback(
    (answer: boolean) => {
      if (answer) {
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: "Great! Which format would you like?",
        });
        setStage('ask_format');
      } else {
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'No problem! Can I post it?',
        });
        setStage('ask_post');
      }
    },
    [pushMessage]
  );

  const handleFormatChoice = useCallback(
    (format: DownloadFormat) => {
      const blog = lastBlogRef.current;
      if (blog) {
        downloadByFormat(format, blog.final_markdown || '', blog.blog_title || 'blog');
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: `Downloaded as ${
            format === 'md' ? 'Markdown' : format === 'pdf' ? 'PDF' : 'Word document'
          } ✅ Can I post it?`,
        });
      } else {
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'Hmm, I couldn’t find the blog to download. Can I post it?',
        });
      }
      setStage('ask_post');
    },
    [pushMessage]
  );

  const handlePostAnswer = useCallback(
    (answer: boolean) => {
      // Posting is intentionally a no-op for now.
      pushMessage({
        id: uid(),
        role: 'assistant',
        kind: 'text',
        text: answer
          ? "Great — I'll post it for you soon! (Posting integration is coming next.) 📌"
          : "Got it, I won't post it. Your blog is saved in Recent Blogs whenever you need it. 👍",
      });
      setStage('done');
    },
    [pushMessage]
  );

  const handleUserInput = useCallback(
    (raw: string) => {
      const text = raw.trim();
      if (!text) return;

      switch (stage) {
        case 'idle':
        case 'done':
          startGeneration(text);
          break;

        case 'generating':
          pushMessage({
            id: uid(),
            role: 'assistant',
            kind: 'text',
            text: 'One moment — I’m still writing your blog…',
          });
          break;

        case 'ask_download': {
          const answer = parseDownloadAnswer(text);
          if (answer !== null) handleDownloadAnswer(answer);
          else {
            pushMessage({
              id: uid(),
              role: 'assistant',
              kind: 'text',
              text: 'Sorry, I didn’t catch that. Would you like to download your blog? (yes/no)',
            });
          }
          break;
        }

        case 'ask_format': {
          const format = parseFormat(text);
          if (format) handleFormatChoice(format);
          else {
            pushMessage({
              id: uid(),
              role: 'assistant',
              kind: 'text',
              text: 'Please choose a format: **md**, **pdf**, or **word**.',
            });
          }
          break;
        }

        case 'ask_post': {
          const answer = parseDownloadAnswer(text);
          if (answer !== null) handlePostAnswer(answer);
          else {
            pushMessage({
              id: uid(),
              role: 'assistant',
              kind: 'text',
              text: 'Just to confirm — can I post it? (yes/no)',
            });
          }
          break;
        }
      }
    },
    [stage, startGeneration, pushMessage, handleDownloadAnswer, handleFormatChoice, handlePostAnswer]
  );

  const handleChip = useCallback(
    (value: string) => {
      if (stage === 'ask_format') {
        handleFormatChoice(value as DownloadFormat);
      } else {
        handleUserInput(value);
      }
    },
    [stage, handleFormatChoice, handleUserInput]
  );

  /* ------------------------- History selection -------------------------- */

  const handleSelectBlog = useCallback(
    async (blogId: string) => {
      try {
        setLoading(true);
        setStage('generating'); // show the typing indicator while fetching
        const data = await fetchBlogById(blogId);
        lastBlogRef.current = data;
        setActiveBlogId(blogId);

        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'blog',
          text: `Here's "${data.blog_title || 'Untitled'}" from your recent blogs.`,
          blog: data,
        });
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: 'Would you like to download it?',
        });
        setStage('ask_download');
      } catch (err) {
        console.error('Failed to load blog:', err);
        pushMessage({
          id: uid(),
          role: 'assistant',
          kind: 'text',
          text: '❌ Failed to load that blog — it may have expired.',
        });
        setStage('done');
        refreshRecentBlogs();
      } finally {
        setLoading(false);
      }
    },
    [pushMessage, refreshRecentBlogs]
  );

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setStage('idle');
    setActiveBlogId(null);
    lastBlogRef.current = null;
  }, []);

  const chips = stage === 'idle' || stage === 'done' ? undefined : CHIPS[stage];

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar
        recentBlogs={recentBlogs}
        activeBlogId={activeBlogId}
        onSelectBlog={handleSelectBlog}
        onNewChat={handleNewChat}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto" aria-live="polite">
          <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">
            {messages.length === 0 && stage === 'idle' && (
              <div className="flex flex-col items-center justify-center text-center pt-16 chat-msg-in">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-2xl text-white shadow-lg shadow-blue-200 mb-5">
                  ✍️
                </div>
                <h1 className="text-2xl font-bold text-slate-900">
                  What should I write about?
                </h1>
                <p className="text-sm text-slate-500 mt-2 max-w-md">
                  Tell me a topic and I'll research, plan, and write a full blog post for you.
                </p>
                <div className="flex flex-wrap justify-center gap-2 mt-6">
                  {SUGGESTED_TOPICS.map((t) => (
                    <button
                      key={t}
                      onClick={() => startGeneration(t)}
                      disabled={loading}
                      className="px-3.5 py-2 text-xs font-medium rounded-full border border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 active:scale-95 transition shadow-sm disabled:opacity-50"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => {
              const isLast = i === messages.length - 1;
              return (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  chips={isLast && chips ? chips : undefined}
                  onChip={isLast ? handleChip : undefined}
                />
              );
            })}

            {stage === 'generating' && (
              <div className="flex gap-3 chat-msg-in">
                <div className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                  ✍️
                </div>
                <div className="bg-slate-100 border border-slate-200 rounded-2xl rounded-tl-md px-4 py-3 inline-flex items-center gap-2">
                  <span className="text-sm text-slate-600">Writing your blog</span>
                  <span className="typing-dots">
                    <span />
                    <span />
                    <span />
                  </span>
                </div>
              </div>
            )}

            <div ref={endRef} />
          </div>
        </div>

        {/* Composer */}
        <ChatInput
          onSend={handleUserInput}
          asOf={asOf}
          setAsOf={setAsOf}
          disabled={loading}
          placeholder={
            stage === 'ask_download' || stage === 'ask_post'
              ? 'Type yes or no…'
              : stage === 'ask_format'
                ? 'Type md, pdf or word…'
                : 'Write a blog about…'
          }
        />
      </main>
    </div>
  );
}
