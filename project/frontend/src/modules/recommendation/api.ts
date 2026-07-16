import type { RecommendationApi, RecommendationResponse, StudentProfile } from "./types";

export function createRecommendationApi(baseUrl: string): RecommendationApi {
  const base = baseUrl.replace(/\/$/, "");
  return {
    async recommend(student: StudentProfile): Promise<RecommendationResponse> {
      const response = await fetch(`${base}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student }),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.error?.message ?? body.detail ?? `HTTP ${response.status}`);
      }
      return body as RecommendationResponse;
    },
  };
}
