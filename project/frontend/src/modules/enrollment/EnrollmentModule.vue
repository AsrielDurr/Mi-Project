<template>
  <section class="module">
    <p class="eyebrow">M2 · 规则与选课</p>
    <h1>检查资格并提交选课</h1>

    <!-- Standalone mode -->
    <div v-if="mode === 'standalone'" class="form-card">
      <p class="current-student">当前学生：<b>{{ currentStudentId() }}</b></p>
      <div class="form-row">
        <label>
          <span>课程</span>
          <select v-model="selectedCourseId" @change="resetResult">
            <option value="">-- 选择课程 --</option>
            <option v-for="c in courseOptions" :key="c.id" :value="c.id">{{ c.id }} {{ c.name }}</option>
          </select>
        </label>
      </div>
      <button
        class="primary"
        :disabled="!selectedCourseId || loading"
        @click="submitEnrollment"
      >
        {{ loading ? '提交中...' : '提交选课' }}
      </button>
    </div>

    <!-- Integration mode -->
    <div v-if="mode === 'integration' && selection" class="banner info">
      收到选课事件：学生 <b>{{ selection.studentId }}</b> 选择课程 <b>{{ courseName(selection.courseId) }}</b>
      <span v-if="selection.recommendationTraceId" class="trace-hint">推荐追溯 {{ selection.recommendationTraceId }}</span>
    </div>

    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="loading" class="loading-msg">正在检查选课资格...</p>

    <!-- Result -->
    <div v-if="decision" class="result-card">
      <h3>选课结果</h3>

      <div class="summary-grid">
        <div class="field">
          <span class="label">学生</span>
          <span class="value">{{ decision.student_id }}</span>
        </div>
        <div class="field">
          <span class="label">课程</span>
          <span class="value">{{ decision.course_name || courseName(decision.course_id) }}</span>
        </div>
        <div class="field">
          <span class="label">规则判定</span>
          <span :class="['value', decision.rule_decision === 'PASS' ? 'text-pass' : 'text-block']">
            {{ decision.rule_decision === 'PASS' ? '通过' : '阻止' }}
          </span>
        </div>
        <div class="field">
          <span class="label">最终状态</span>
          <span :class="['value', 'status-tag', statusTagClass(decision.status)]">
            {{ statusLabel(decision.status) }}
          </span>
        </div>
        <div v-if="decision.waitlist_position !== null" class="field">
          <span class="label">候补排名</span>
          <span class="value rank">第 {{ decision.waitlist_position }} 位</span>
        </div>
        <div class="field full-width">
          <span class="label">追溯ID</span>
          <span class="value mono">{{ decision.trace_id }}</span>
        </div>
      </div>

      <h4>逐条规则检查</h4>
      <table>
        <thead>
          <tr>
            <th>规则</th>
            <th>结果</th>
            <th>原因</th>
            <th>关联课程</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(check, idx) in decision.checks" :key="idx" :class="check.passed ? 'row-pass' : 'row-fail'">
            <td><span class="rule-badge" :class="check.passed ? 'badge-pass' : 'badge-fail'">{{ ruleLabel(check.rule) }}</span></td>
            <td>{{ check.passed ? '通过' : '未通过' }}</td>
            <td>{{ check.reason }}</td>
            <td>{{ check.related_course_id ? courseName(check.related_course_id) : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

interface CourseSelectedEvent {
  studentId: string
  courseId: string
  recommendationTraceId: string
}

interface EnrollmentDecidedEvent {
  studentId: string
  courseId: string
  status: 'ENROLLED' | 'WAITLISTED' | 'REJECTED'
  enrollmentTraceId: string
}

const props = defineProps<{
  selection?: CourseSelectedEvent | null
  studentId?: string
  apiBase?: string
}>()

const emit = defineEmits<{
  (e: 'enrollment-decided', event: EnrollmentDecidedEvent): void
}>()

const mode = ref<'standalone' | 'integration'>('standalone')
const selectedCourseId = ref('')
const loading = ref(false)
const error = ref('')
const decision = ref<any>(null)
const courseNameMap = ref<Record<string, string>>({})
const courseOptions = ref<{ id: string; name: string }[]>([])

const API_BASE = () => (props.apiBase ?? import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

function courseName(courseId: string): string {
  return courseNameMap.value[courseId] || courseId
}

onMounted(async () => {
  try {
    const resp = await fetch(`${API_BASE()}/api/courses`)
    if (resp.ok) {
      const data: { course_id: string; name: string }[] = await resp.json()
      courseOptions.value = data.map(c => ({ id: c.course_id, name: c.name }))
      for (const c of data) courseNameMap.value[c.course_id] = c.name
    }
  } catch { /* fall back to bare IDs */ }
})

watch(() => props.selection, (sel) => {
  if (sel) {
    mode.value = 'integration'
    submitEnrollmentForStudent(sel.studentId, sel.courseId, sel.recommendationTraceId)
  }
}, { immediate: true })

watch(() => props.studentId, () => {
  decision.value = null
  error.value = ''
  selectedCourseId.value = ''
  mode.value = 'standalone'
})

function resetResult() { decision.value = null; error.value = '' }

function currentStudentId(): string {
  return props.studentId || props.selection?.studentId || 'S001'
}

async function submitEnrollment() {
  if (!selectedCourseId.value) return
  await submitEnrollmentForStudent(currentStudentId(), selectedCourseId.value)
}

async function submitEnrollmentForStudent(studentId: string, courseId: string, recommendationTraceId?: string) {
  loading.value = true; error.value = ''; decision.value = null
  try {
    const resp = await fetch(`${API_BASE()}/api/enroll`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, course_id: courseId, recommendation_trace_id: recommendationTraceId || null }),
    })
    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}))
      error.value = `选课失败: ${errData?.error?.message || errData?.detail || `HTTP ${resp.status}`}`
      loading.value = false
      return
    }
    const data = await resp.json()
    decision.value = data
    emit('enrollment-decided', { studentId: data.student_id, courseId: data.course_id, status: data.status, enrollmentTraceId: data.trace_id })
  } catch (e: any) {
    error.value = `网络错误: ${e.message}`
  } finally {
    loading.value = false
  }
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { ENROLLED: '选课成功', WAITLISTED: '进入候补', REJECTED: '选课失败' }
  return map[s] || s
}

function statusTagClass(s: string): string {
  const map: Record<string, string> = { ENROLLED: 'green', WAITLISTED: 'amber', REJECTED: 'red' }
  return map[s] || 'grey'
}

function ruleLabel(rule: string): string {
  const map: Record<string, string> = { DUPLICATE: '重复选课', PREREQUISITE: '先修课程', TIME_CONFLICT: '时间冲突' }
  return map[rule] || rule
}
</script>

<style scoped>
.module {
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
  color: #182230;
}

h1 { margin: 0 0 20px; font-size: 1.5rem; }
h3 { margin: 0 0 16px; font-size: 1.1rem; }
h4 { margin: 20px 0 8px; font-size: 0.95rem; color: #667085; }

.eyebrow {
  margin-bottom: 6px;
  color: #4263eb;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ── Form ─────────────────────────────── */
.form-card {
  padding: 20px;
  border: 1px solid #dfe3eb;
  border-radius: 14px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.current-student {
  margin: 0;
  font-size: 14px;
  color: #667085;
}
.current-student b { color: #182230; }

.form-row {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.form-row label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row label span {
  font-weight: 700;
  font-size: 13px;
  color: #344054;
}

select {
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid #c8cfdd;
  border-radius: 9px;
  font: inherit;
  font-size: 14px;
  color: #182230;
  background: #fff;
}
select:focus { outline: none; border-color: #4263eb; box-shadow: 0 0 0 3px rgba(66, 99, 235, 0.12); }

/* ── Buttons ───────────────────────────── */
button {
  min-height: 40px;
  padding: 0 18px;
  border-radius: 9px;
  font: inherit;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
}
button:disabled { cursor: wait; opacity: 0.55; }

.primary {
  border: 1px solid #3151d3;
  color: #fff;
  background: #4263eb;
  align-self: flex-start;
}
.primary:hover:not(:disabled) { background: #3451db; }

/* ── Banners ───────────────────────────── */
.banner {
  margin-top: 16px;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
}
.info { color: #175cd3; background: #eff8ff; }
.trace-hint { display: block; margin-top: 4px; font-size: 13px; color: #667085; }

.error {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #b42318;
  background: #fee4e2;
  font-size: 14px;
}

.loading-msg { margin-top: 16px; color: #667085; font-size: 14px; font-style: italic; }

/* ── Result card ───────────────────────── */
.result-card {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #dfe3eb;
  border-radius: 14px;
  background: #fff;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.field { display: flex; flex-direction: column; gap: 4px; }
.full-width { grid-column: 1 / -1; }

.label { font-size: 13px; color: #667085; }
.value { font-size: 15px; font-weight: 600; }
.text-pass { color: #067647; }
.text-block { color: #b42318; }
.rank { color: #e67e00; }
.mono { font-family: "SF Mono", "Cascadia Code", monospace; font-size: 13px; font-weight: 400; }

.status-tag {
  display: inline-flex;
  align-self: flex-start;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 13px;
}
.status-tag.green { color: #067647; background: #dcfae6; }
.status-tag.amber { color: #7c5700; background: #fff1cc; }
.status-tag.red   { color: #b42318; background: #fee4e2; }

/* ── Table ─────────────────────────────── */
table {
  width: 100%;
  margin-top: 12px;
  border-collapse: collapse;
  font-size: 14px;
}

th, td {
  padding: 10px;
  border-bottom: 1px solid #eaecf0;
  text-align: left;
}

th {
  color: #667085;
  font-size: 0.8rem;
  font-weight: 600;
}

.row-pass { background: #f6fef9; }
.row-fail { background: #fff8f8; }

.rule-badge {
  display: inline-flex;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.badge-pass { color: #067647; background: #dcfae6; }
.badge-fail { color: #b42318; background: #fee4e2; }
</style>
