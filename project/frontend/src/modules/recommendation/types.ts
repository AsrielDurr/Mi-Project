export interface StudentProfile {
  student_id: string;
  goal: string;
  skills: string[];
  available_times: string[];
  completed_course_ids: string[];
  enrolled_course_ids: string[];
}

export interface Recommendation {
  course_id: string;
  score: number;
  reason: string;
  uncertainty: string;
}

export interface RecommendationResponse {
  trace_id: string;
  source: "MODEL" | "FALLBACK";
  model: string | null;
  prompt_version: string;
  fallback_reason: string | null;
  recommendations: Recommendation[];
}

export interface RecommendationApi {
  recommend(student: StudentProfile): Promise<RecommendationResponse>;
}

export interface CourseSelectedEvent {
  studentId: string;
  courseId: string;
  recommendationTraceId: string;
}
