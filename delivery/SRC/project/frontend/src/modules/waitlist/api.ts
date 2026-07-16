import type {
  CourseStatusResponse,
  DemoResetResponse,
  RecomputeResult,
  ReleaseSeatResponse,
  TraceResponse,
  WaitlistApi,
} from "./types";


interface ErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    trace_id?: string | null;
  };
}


async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    throw new Error(body.error?.message ?? `请求失败：HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}


export function createWaitlistApi(baseUrl: string): WaitlistApi {
  const base = baseUrl.replace(/\/$/, "");
  return {
    getCourseStatus(courseId: string): Promise<CourseStatusResponse> {
      const query = new URLSearchParams({ course_id: courseId });
      return request(`${base}/api/admin/course-status?${query.toString()}`);
    },
    releaseSeat(courseId: string): Promise<ReleaseSeatResponse> {
      return request(`${base}/api/admin/release-seat`, {
        method: "POST",
        body: JSON.stringify({ course_id: courseId }),
      });
    },
    recomputeWaitlist(courseId: string): Promise<RecomputeResult> {
      return request(`${base}/api/admin/recompute-waitlist`, {
        method: "POST",
        body: JSON.stringify({ course_id: courseId }),
      });
    },
    getTrace(traceId: string): Promise<TraceResponse> {
      return request(`${base}/api/trace/${encodeURIComponent(traceId)}`);
    },
    resetScenario(scenarioId: string): Promise<DemoResetResponse> {
      return request(`${base}/api/demo/reset`, {
        method: "POST",
        body: JSON.stringify({ scenario_id: scenarioId }),
      });
    },
  };
}

