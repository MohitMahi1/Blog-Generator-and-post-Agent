import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Props {
  markdown: string;
  title: string;
}

export default function PreviewTab({ markdown, title }: Props) {
  if (!markdown) {
    return <div className="text-slate-500">No markdown generated yet.</div>;
  }

  const downloadMd = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_').toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Download button */}
      <div className="flex gap-3">
        <button
          onClick={downloadMd}
          className="px-4 py-2 bg-slate-800 text-white rounded-lg text-sm hover:bg-slate-700 transition"
        >
          ⬇️ Download Markdown
        </button>
      </div>

      {/* Blog-style container */}
      <article className="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-8 py-10 md:px-12 md:py-12">
          <div className="prose prose-slate prose-lg max-w-none
            prose-headings:font-bold prose-headings:text-slate-900
            prose-h1:text-3xl prose-h1:mb-6
            prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
            prose-h3:text-xl prose-h3:mt-8
            prose-p:text-slate-700 prose-p:leading-relaxed
            prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
            prose-strong:text-slate-900
            prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
            prose-pre:bg-slate-900 prose-pre:text-slate-100
            prose-img:rounded-xl prose-img:shadow-md
            prose-li:marker:text-slate-400">
            
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                img: ({ src, alt }) => (
                  <img
                    src={src?.startsWith('http') ? src : `http://localhost:8000/${src}`}
                    alt={alt || ''}
                    className="rounded-xl my-8 w-full object-cover shadow-md"
                  />
                ),
              }}
            >
              {markdown}
            </ReactMarkdown>
          </div>
        </div>
      </article>
    </div>
  );
}