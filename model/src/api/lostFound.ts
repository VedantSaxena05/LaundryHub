import { apiRequest } from "./client";

export interface LostFoundPost {
  id: string;
  post_type: "lost" | "found";
  item_description: string;
  color: string;
  last_seen_location: string;
  resolved: boolean;
  posted_by?: string;
  created_at: string;
}

export interface LostFoundMatch {
  id: string;
  post_id: string;
  matched_post_id: string;
  score: number;
}

export const lostFoundApi = {
  list: (token: string, postType?: string, resolved?: boolean) =>
    apiRequest<LostFoundPost[]>("/lost-found", {
      token,
      params: {
        ...(postType ? { post_type: postType } : {}),
        ...(resolved !== undefined ? { resolved: String(resolved) } : {}),
      },
    }),

  create: (token: string, data: { post_type: string; item_description: string; color: string; last_seen_location: string }) =>
    apiRequest<LostFoundPost>("/lost-found", { method: "POST", token, body: data }),

  resolve: (token: string, postId: string) =>
    apiRequest<LostFoundPost>(`/lost-found/${postId}/resolve`, { method: "POST", token }),

  getMatches: (token: string, postId: string) =>
    apiRequest<LostFoundMatch[]>(`/lost-found/${postId}/matches`, { token }),
};
