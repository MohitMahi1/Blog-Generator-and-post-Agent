import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API_URL = import.meta.env.VITE_API_URL || '';

interface Props {
  markdown: string;
}

/** Renders raw markdown as a styled, blog-like article (shared by PreviewTab and chat). */
export default function BlogArticle({ markdown }: Props) {
  if (!markdown) {
    return <div className="text-slate-500">No markdown generated yet.</div>;
  }

  return (
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
          img: ({ src, alt }) => {
            let finalSrc = src || '';
            if (!finalSrc.startsWith('http')) {
              const cleanSrc = finalSrc.startsWith('/') ? finalSrc : `/${finalSrc}`;
              finalSrc = `${API_URL}${cleanSrc}`;
            }
            return (
              <img
                src={finalSrc}
                alt={alt || ''}
                className="rounded-xl my-8 w-full object-cover shadow-md"
              />
            );
          },
        }}

      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
