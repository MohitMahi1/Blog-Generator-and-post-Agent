import axios from 'axios';
import type { GenerateResponse, BlogListItem, BlogListResponse } from '../types/blog';

const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
});

function makeSessionId(): string {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : 'session_' + Math.random().toString(36).substring(2, 11);
}

export function getSessionId(): string {
  let sessionId = sessionStorage.getItem('blog_session_id');
  if (!sessionId) {
    sessionId = makeSessionId();
    sessionStorage.setItem('blog_session_id', sessionId);
  }
  return sessionId;
}

// Guard so React StrictMode's double-invoked initializer only performs the
// refresh cleanup once per page load.
let sessionResetDone = false;

/**
 * Called once per page load. If a previous session exists (e.g. the page was
 * refreshed), deletes that session's blogs from the server and issues a fresh
 * session id — so refreshing the site wipes old blogs, while clicking
 * "New chat" (no reload) keeps the same session and its blogs for 15 minutes.
 */
export function startNewSession(): string {
  if (!sessionResetDone) {
    sessionResetDone = true;
    const previous = sessionStorage.getItem('blog_session_id');
    if (previous) {
      // Fire-and-forget: the previous session's blogs no longer belong to anyone.
      api.delete(`/api/v1/blogs/${encodeURIComponent(previous)}`).catch(() => {
        // Session may already be empty or cleaned up — that's fine.
      });
      sessionStorage.removeItem('blog_session_id');
    }
  }
  return getSessionId();
}

export async function generateBlog(
  topic: string, 
  asOf: string, 
  sessionId?: string
): Promise<GenerateResponse> {
  const sid = sessionId || getSessionId();
  const res = await api.post<GenerateResponse>('/api/v1/generate', {
    topic,
    as_of: asOf,
    session_id: sid,
  });
  return res.data;
}

export async function fetchSessionBlogs(sessionId?: string): Promise<BlogListItem[]> {
  const sid = sessionId || getSessionId();
  const res = await api.get<BlogListResponse>(`/api/v1/blogs/${encodeURIComponent(sid)}`);
  return res.data.blogs || [];
}

export async function fetchBlogById(blogId: string): Promise<GenerateResponse> {
  const res = await api.get<GenerateResponse>(`/api/v1/blog/${blogId}`);
  return res.data;
}

export async function deleteBlog(blogId: string): Promise<void> {
  await api.delete(`/api/v1/blog/${blogId}`);
}