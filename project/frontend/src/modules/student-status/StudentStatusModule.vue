<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import { courseCatalog } from "../../shared/courseCatalog";

const props = withDefaults(
  defineProps<{
    studentId?: string;
    apiBase?: string;
    refreshTrigger?: number;
  }>(),
  { studentId: "S001" }
);

const API_BASE = () =>
  (props.apiBase ?? import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

interface EnrollmentEntry {
  course_id: string;
  status: string;
}

interface WaitlistEntry {
  student_id: string;
  course_id: string;
  position: number;
  applied_at: string;
  status: string;
  last_check_reason: string | null;
}

interface StudentStatus {
  student_id: string;
  enrollments: EnrollmentEntry[];
  waitlist_entries: WaitlistEntry[];
}

const status = ref<StudentStatus | null>(null);
const loading = ref(false);
const error = ref("");

const nameMap: Record<string, string> = {};
for (const c of courseCatalog) {
  nameMap[c.courseId] = c.name;
}

function courseName(courseId: string): string {
  return nameMap[courseId] || courseId;
}

let timer: ReturnType<typeof setInterval> | null = null;

async function fetchStatus(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const resp = await fetch(`${API_BASE()}/api/student/status?student_id=${props.studentId}`);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      error.value = err?.error?.message || err?.detail || `HTTP ${resp.status}`;
      return;
    }
    status.value = await resp.json();
  } catch (e: any) {
    error.value = `网络错误: ${e.message}`;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchStatus();
  timer = setInterval(fetchStatus, 5000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

watch(() => props.refreshTrigger, () => fetchStatus());

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    ENROLLED: "已选",
    WAITING: "候补中",
    SKIPPED: "已跳过",
    PROMOTED: "已补入",
  };
  return map[s] || s;
}

function tagClass(s: string): string {
  const map: Record<string, string> = { WAITING: "amber", SKIPPED: "red", PROMOTED: "green", ENROLLED: "green" };
  return map[s] || "grey";
}
</script>

<template>
  <section class="module">
    <div class="header-row">
      <div>
        <p class="eyebrow">M3 · 选课状态</p>
        <h1>我的选课状态</h1>
      </div>
      <button class="secondary" :disabled="loading" @click="fetchStatus">
        {{ loading ? "刷新中..." : "刷新" }}
      </button>
    </div>
    <p class="student-hint">学生 {{ props.studentId }}</p>

    <p v-if="error" role="alert" class="error">{{ error }}</p>

    <div v-if="status" class="grid">
      <!-- Enrolled -->
      <div class="card">
        <div class="card-head">
          <h3>已选课程</h3>
          <span class="count">{{ status.enrollments.length }}</span>
        </div>
        <ul v-if="status.enrollments.length">
          <li v-for="e in status.enrollments" :key="e.course_id">
            <span class="cname">{{ courseName(e.course_id) }}</span>
            <span class="cid">{{ e.course_id }}</span>
            <span class="tag green">{{ statusLabel(e.status) }}</span>
          </li>
        </ul>
        <p v-else class="empty">暂无已选课程</p>
      </div>

      <!-- Waitlisted -->
      <div class="card">
        <div class="card-head">
          <h3>候补队列</h3>
          <span class="count">{{ status.waitlist_entries.length }}</span>
        </div>
        <ul v-if="status.waitlist_entries.length">
          <li v-for="w in status.waitlist_entries" :key="w.course_id">
            <div class="wrow">
              <span class="cname">{{ courseName(w.course_id) }}</span>
              <span class="cid">{{ w.course_id }}</span>
              <span class="tag" :class="tagClass(w.status)">{{ statusLabel(w.status) }}</span>
              <span class="pos">#{{ w.position }}</span>
            </div>
            <p v-if="w.last_check_reason" class="reason">{{ w.last_check_reason }}</p>
          </li>
        </ul>
        <p v-else class="empty">暂未进入任何候补队列</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.module {
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
  color: #182230;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

h1 { margin: 0 0 4px; font-size: 1.5rem; }

.eyebrow {
  margin-bottom: 6px;
  color: #4263eb;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.student-hint { margin: 0 0 20px; color: #667085; font-size: 14px; }

button {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 9px;
  font: inherit;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
}
button:disabled { cursor: wait; opacity: 0.55; }

.secondary {
  border: 1px solid #c8cfdd;
  color: #344054;
  background: #fff;
}
.secondary:hover:not(:disabled) { background: #f5f7fb; }

.error {
  padding: 12px 16px;
  border-radius: 10px;
  color: #b42318;
  background: #fee4e2;
  font-size: 14px;
  margin-bottom: 16px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.card {
  padding: 20px;
  border: 1px solid #dfe3eb;
  border-radius: 14px;
  background: #fff;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.card-head h3 { margin: 0; font-size: 1rem; }

.count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  padding: 0 8px;
  border-radius: 999px;
  background: #edf0f7;
  color: #344054;
  font-size: 13px;
  font-weight: 700;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

li {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wrow {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.cname { font-weight: 700; font-size: 15px; }
.cid { color: #667085; font-size: 13px; }

.tag {
  display: inline-flex;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: #eef1f6;
  color: #344054;
}
.tag.green { color: #067647; background: #dcfae6; }
.tag.amber { color: #7c5700; background: #fff1cc; }
.tag.red   { color: #b42318; background: #fee4e2; }

.pos { color: #e67e00; font-weight: 700; font-size: 14px; }

.reason { margin: 2px 0 0; font-size: 13px; color: #667085; }

.empty { color: #a0a6b5; font-size: 14px; font-style: italic; margin: 0; }

@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
