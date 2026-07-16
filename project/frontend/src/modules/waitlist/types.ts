export type CourseStatusValue = "OPEN" | "CANCELLED";
export type WaitlistStatus = "WAITING" | "PROMOTED" | "SKIPPED";

export interface Schedule {
  day: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN";
  start: string;
  end: string;
}

export interface Course {
  course_id: string;
  name: string;
  description: string;
  schedule: Schedule;
  capacity: number;
  enrolled_count: number;
  prerequisite_ids: string[];
  status: CourseStatusValue;
}

export interface WaitlistEntry {
  student_id: string;
  course_id: string;
  position: number;
  applied_at: string;
  status: WaitlistStatus;
  last_check_reason: string | null;
}

export interface CourseStatusResponse {
  course: Course;
  available_seats: number;
  enrolled_student_ids: string[];
  waitlist: WaitlistEntry[];
}

export interface ReleaseSeatResponse {
  trace_id: string;
  course_id: string;
  capacity_before: number;
  capacity_after: number;
  enrolled_count: number;
  available_seats: number;
}

export interface RecomputeCheck {
  student_id: string;
  waitlist_status: "PROMOTED" | "SKIPPED";
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

export interface TraceResponse {
  trace_id: string;
  events: TraceEvent[];
}

export interface DemoResetResponse {
  trace_id: string;
  scenario_id: string;
  course_ids: string[];
  student_ids: string[];
}

export interface WaitlistApi {
  getCourseStatus(courseId: string): Promise<CourseStatusResponse>;
  releaseSeat(courseId: string): Promise<ReleaseSeatResponse>;
  recomputeWaitlist(courseId: string): Promise<RecomputeResult>;
  getTrace(traceId: string): Promise<TraceResponse>;
  resetScenario(scenarioId: string): Promise<DemoResetResponse>;
}

