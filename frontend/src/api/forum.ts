import { apiRequest } from "./client";

export interface ForumPost {
  id: string;
  category: string;
  title: string;
  body: string;
  is_anonymous: boolean;
  posted_by?: string;
  author_name?: string;
  upvotes?: number;
  reply_count?: number;
  is_pinned?: boolean;
  created_at: string;
}

export interface ForumReply {
  id: string;
  body: string;
  is_anonymous: boolean;
  posted_by?: string;
  author_name?: string;
  created_at: string;
}

export const forumApi = {
  list: (token: string, category?: string, page = 1, pageSize = 20) =>
    apiRequest<ForumPost[]>("/forum", {
      token,
      params: {
        ...(category ? { category } : {}),
        page: String(page),
        page_size: String(pageSize),
      },
    }),

  create: (token: string, data: { category: string; title: string; body: string; is_anonymous: boolean }) =>
    apiRequest<ForumPost>("/forum", { method: "POST", token, body: data }),

  upvote: (token: string, postId: string) =>
    apiRequest(`/forum/${postId}/upvote`, { method: "POST", token }),

  reply: (token: string, postId: string, data: { body: string; is_anonymous: boolean }) =>
    apiRequest<ForumReply>(`/forum/${postId}/replies`, { method: "POST", token, body: data }),

  pin: (token: string, postId: string) =>
    apiRequest(`/forum/${postId}/pin`, { method: "POST", token }),
};
