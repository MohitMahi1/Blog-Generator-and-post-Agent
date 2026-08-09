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
    <div className="space-y-4">
      <div className="flex gap-3">
        <button
          onClick={downloadMd}
          className="px-4 py-2 bg-slate-800 text-white rounded-lg text-sm hover:bg-slate-700"
        >
          ⬇️ Download Markdown
        </button>
      </div>

      <div className="prose max-w-none bg-white p-6 rounded-xl border border-slate-200">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            img: ({ src, alt }) => (
              <img
                src={src?.startsWith('http') ? src : `http://localhost:8000/${src}`}
                alt={alt || ''}
                className="rounded-lg my-4 max-w-full"
              />
            ),
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    </div>
  );
}