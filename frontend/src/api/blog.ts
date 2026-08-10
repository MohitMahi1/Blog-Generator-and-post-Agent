import axios from 'axios';
import type { GenerateResponse, BlogListItem, BlogListResponse } from '../types/blog';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export function getSessionId(): string {
  let sessionId = sessionStorage.getItem('blog_session_id');
  if (!sessionId) {
    sessionId = typeof crypto !== 'undefined' && crypto.randomUUID 
      ? crypto.randomUUID() 
      : 'session_' + Math.random().toString(36).substring(2, 11);
    sessionStorage.setItem('blog_session_id', sessionId);
  }
  return sessionId;
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
  const res = await api.get<BlogListResponse>(`/api/v1/blogs/${sid}`);
  return res.data.blogs || [];
}

export async function fetchBlogById(blogId: string): Promise<GenerateResponse> {
  const res = await api.get<GenerateResponse>(`/api/v1/blog/${blogId}`);
  return res.data;
}

export async function deleteBlog(blogId: string): Promise<void> {
  await api.delete(`/api/v1/blog/${blogId}`);
}