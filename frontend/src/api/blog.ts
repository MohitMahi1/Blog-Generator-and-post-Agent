import axios from 'axios';
import type { GenerateResponse } from '../types/blog';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export async function generateBlog(topic: string, asOf: string): Promise<GenerateResponse> {
  const res = await api.post<GenerateResponse>('/api/v1/generate', {
    topic,
    as_of: asOf,
  });
  return res.data;
}