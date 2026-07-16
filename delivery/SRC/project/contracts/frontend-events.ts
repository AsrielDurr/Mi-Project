export const CONTRACT_VERSION = "1.1.0" as const;

export type RuleDecision = "PASS" | "BLOCK";
export type EnrollmentStatus = "ENROLLED" | "WAITLISTED" | "REJECTED";
export type WaitlistStatus = "WAITING" | "PROMOTED" | "SKIPPED";
export type RecommendationSource = "MODEL" | "FALLBACK";
export type CourseStatus = "OPEN" | "CANCELLED";
export type RuleName = "DUPLICATE" | "PREREQUISITE" | "TIME_CONFLICT";

export interface CourseSelectedEvent {
  studentId: string;
  courseId: string;
  recommendationTraceId: string;
}

export interface EnrollmentDecidedEvent {
  studentId: string;
  courseId: string;
  status: EnrollmentStatus;
  enrollmentTraceId: string;
}

export interface Schedule {
  day: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN";
  start: string;
  end: string;
}

export interface StudentProfile {
  student_id: string;
  goal: string;
  skills: string[];
  available_times: string[];
  completed_course_ids: string[];
  enrolled_course_ids: string[];
}

export interface Course {
  course_id: string;
  name: string;
  description: string;
  schedule: Schedule;
  capacity: number;
  enrolled_count: number;
  prerequisite_ids: string[];
  status: CourseStatus;
}

export interface Recommendation {
  course_id: string;
  score: number;
  reason: string;
  uncertainty: string;
}

export interface RecommendationResponse {
  trace_id: string;
  source: RecommendationSource;
  model: string | null;
  prompt_version: string;
  fallback_reason: string | null;
  recommendations: Recommendation[];
}

export interface RuleCheckResult {
  rule: RuleName;
  passed: boolean;
  reason: string;
  related_course_id: string | null;
}

export interface EnrollmentDecision {
  trace_id: string;
  student_id: string;
  course_id: string;
  rule_decision: RuleDecision;
  capacity_available: boolean;
  status: EnrollmentStatus;
  waitlist_position: number | null;
  checks: RuleCheckResult[];
}

export interface WaitlistEntry {
  student_id: string;
  course_id: string;
  position: number;
  applied_at: string;
  status: WaitlistStatus;
  last_check_reason: string | null;
}

export interface RecomputeCheck {
  student_id: string;
  waitlist_status: WaitlistStatus;
  reason: string;
}

export interface RecomputeResult {
  trace_id: string;
  course_id: string;
  available_seats_before: number;
  checked: RecomputeCheck[];
  promoted_student_ids: string[];
}

export interface TraceEvent {
  event_id: string;
  trace_id: string;
  event_type: string;
  actor: "STUDENT" | "TEACHER" | "SYSTEM" | "MODEL";
  payload: Record<string, unknown>;
  created_at: string;
}

