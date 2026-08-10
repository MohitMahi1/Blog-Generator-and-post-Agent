import type { BlogListItem } from '../types/blog';

interface Props {
  topic: string;
  setTopic: (v: string) => void;
  asOf: string;
  setAsOf: (v: string) => void;
  onGenerate: () => void;
  loading: boolean;
  recentBlogs?: BlogListItem[];
  activeBlogId?: string | null;
  onSelectBlog?: (blogId: string) => void;
  onNewBlog?: () => void;
}

export default function Sidebar({
  topic,
  setTopic,
  asOf,
  setAsOf,
  onGenerate,
  loading,
  recentBlogs = [],
  activeBlogId,
  onSelectBlog,
  onNewBlog,
}: Props) {
  return (
    <div className="w-80 bg-white border-r border-slate-200 p-5 flex flex-col gap-5 h-screen sticky top-0 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-800">Blog Writing Agent</h2>
        {onNewBlog && (
          <button
            onClick={onNewBlog}
            title="New Blog"
            className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded font-medium transition"
          >
            + New
          </button>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Topic</label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          rows={4}
          className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. Introduction to LangGraph with real examples"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">As-of date</label>
        <input
          type="date"
          value={asOf}
          onChange={(e) => setAsOf(e.target.value)}
          className="w-full border border-slate-300 rounded-lg p-2 text-sm"
        />
      </div>

      <button
        onClick={onGenerate}
        disabled={loading || !topic.trim()}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium py-2.5 rounded-lg transition"
      >
        {loading ? 'Generating…' : '🚀 Generate Blog'}
      </button>

      {/* Recent Blogs Section */}
      {recentBlogs.length > 0 && (
        <div className="flex flex-col gap-2 pt-3 border-t border-slate-200">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <span>Recent Blogs</span>
            <span className="text-[10px] text-slate-400">15m auto-delete</span>
          </div>
          <div className="flex flex-col gap-1 max-h-48 overflow-y-auto pr-1">
            {recentBlogs.map((b) => {
              const isActive = b.blog_id === activeBlogId;
              const dateStr = new Date(b.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              return (
                <button
                  key={b.blog_id}
                  onClick={() => onSelectBlog && onSelectBlog(b.blog_id)}
                  className={`text-left p-2 rounded-lg text-xs transition flex flex-col gap-0.5 ${
                    isActive
                      ? 'bg-blue-50 border border-blue-200 text-blue-800 font-semibold'
                      : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <span className="truncate w-full">{b.blog_title || 'Untitled Blog'}</span>
                  <span className="text-[10px] text-slate-400">{dateStr}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-auto text-xs text-slate-400">
        Powered by LangGraph + Supabase
      </div>
    </div>
  );
}