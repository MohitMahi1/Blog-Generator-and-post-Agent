import type { BlogListItem } from '../types/blog';

interface Props {
  recentBlogs?: BlogListItem[];
  activeBlogId?: string | null;
  onSelectBlog?: (blogId: string) => void;
  onNewChat?: () => void;
}

export default function Sidebar({
  recentBlogs = [],
  activeBlogId,
  onSelectBlog,
  onNewChat,
}: Props) {
  return (
    <div className="w-72 shrink-0 bg-white border-r border-slate-200 p-5 flex flex-col gap-5 h-screen sticky top-0 overflow-y-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm shadow-sm">
            ✍️
          </span>
          <div>
            <h2 className="text-sm font-bold text-slate-800 leading-tight">Blog Writer</h2>
            <p className="text-[10px] text-slate-400 leading-tight">Agent · LangGraph</p>
          </div>
        </div>
        {onNewChat && (
          <button
            onClick={onNewChat}
            title="New chat"
            className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded-lg font-medium transition"
          >
            + New
          </button>
        )}
      </div>

      {/* Recent Blogs Section */}
      <div className="flex flex-col gap-2 pt-2">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <span>Recent Blogs</span>
          <span className="text-[10px] text-slate-400">15m auto-delete</span>
        </div>

        {recentBlogs.length === 0 ? (
          <div className="text-xs text-slate-400 bg-slate-50 border border-dashed border-slate-200 rounded-lg p-3 text-center">
            No blogs yet. Start a chat below!
          </div>
        ) : (
          <div className="flex flex-col gap-1 max-h-72 overflow-y-auto pr-1">
            {recentBlogs.map((b) => {
              const isActive = b.blog_id === activeBlogId;
              const dateStr = new Date(b.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              });
              return (
                <button
                  key={b.blog_id}
                  onClick={() => onSelectBlog && onSelectBlog(b.blog_id)}
                  className={`text-left p-2 rounded-lg text-xs transition flex flex-col gap-0.5 ${
                    isActive
                      ? 'bg-blue-50 border border-blue-200 text-blue-800 font-semibold'
                      : 'hover:bg-slate-100 text-slate-700 border border-transparent'
                  }`}
                >
                  <span className="truncate w-full">{b.blog_title || 'Untitled Blog'}</span>
                  <span className="text-[10px] text-slate-400">{dateStr}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-auto text-xs text-slate-400">
        Powered by LangGraph + Supabase
      </div>
    </div>
  );
}
