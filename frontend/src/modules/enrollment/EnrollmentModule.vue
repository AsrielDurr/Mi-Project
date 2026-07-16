<template>
  <div class="enrollment-module">
    <h2>M2 规则与选课模块</h2>

    <!-- Standalone mode: manual selection -->
    <div v-if="mode === 'standalone'" class="standalone-controls">
      <div class="form-group">
        <label>学生:</label>
        <select v-model="selectedStudentId" @change="resetResult">
          <option value="">-- 选择学生 --</option>
          <option v-for="sid in studentIds" :key="sid" :value="sid">{{ sid }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>课程:</label>
        <select v-model="selectedCourseId" @change="resetResult">
          <option value="">-- 选择课程 --</option>
          <option v-for="cid in courseIds" :key="cid" :value="cid">{{ cid }}</option>
        </select>
      </div>
      <button
        :disabled="!selectedStudentId || !selectedCourseId || loading"
        @click="submitEnrollment"
      >
        {{ loading ? '提交中...' : '提交选课' }}
      </button>
    </div>

    <!-- Integration mode: receive CourseSelectedEvent -->
    <div v-if="mode === 'integration' && selection" class="integration-info">
      <p>收到选课事件: 学生 {{ selection.studentId }} 选择课程 {{ selection.courseId }}</p>
      <p v-if="selection.recommendationTraceId">
        推荐追溯ID: {{ selection.recommendationTraceId }}
      </p>
    </div>

    <!-- Error display -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">正在检查选课资格...</div>

    <!-- Result display -->
    <div v-if="decision" class="decision-result">
      <h3>选课结果</h3>

      <div class="summary">
        <div class="field">
          <span class="label">学生ID:</span>
          <span>{{ decision.student_id }}</span>
        </div>
        <div class="field">
          <span class="label">课程ID:</span>
          <span>{{ decision.course_id }}</span>
        </div>
        <div class="field">
          <span class="label">规则判定:</span>
          <span :class="decision.rule_decision === 'PASS' ? 'pass' : 'block'">
            {{ decision.rule_decision === 'PASS' ? '通过' : '阻止' }}
          </span>
        </div>
        <div class="field">
          <span class="label">最终状态:</span>
          <span :class="`status-${decision.status.toLowerCase()}`">
            {{ statusLabel(decision.status) }}
          </span>
        </div>
        <div v-if="decision.waitlist_position !== null" class="field">
          <span class="label">候补排名:</span>
          <span class="waitlist-rank">第 {{ decision.waitlist_position }} 位</span>
        </div>
        <div class="field">
          <span class="label">追溯ID:</span>
          <span class="trace-id">{{ decision.trace_id }}</span>
        </div>
      </div>

      <h4>逐条规则检查</h4>
      <table class="checks-table">
        <thead>
          <tr>
            <th>规则</th>
            <th>结果</th>
            <th>原因</th>
            <th>关联课程</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(check, idx) in decision.checks"
            :key="idx"
            :class="check.passed ? 'check-pass' : 'check-fail'"
          >
            <td>{{ ruleLabel(check.rule) }}</td>
            <td>{{ check.passed ? '通过' : '未通过' }}</td>
            <td>{{ check.reason }}</td>
            <td>{{ check.related_course_id || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

// ── Props (integration mode) ──────────────────────────────────────

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
}>()

const emit = defineEmits<{
  (e: 'enrollment-decided', event: EnrollmentDecidedEvent): void
}>()

// ── State ──────────────────────────────────────────────────────────

const mode = ref<'standalone' | 'integration'>('standalone')
const selectedStudentId = ref('')
const selectedCourseId = ref('')
const loading = ref(false)
const error = ref('')
const decision = ref<any>(null)

// Fixed demo data matching backend demo
const studentIds = ['S001', 'S002', 'S003']
const courseIds = ['CS101', 'AI201', 'DB202', 'ML301', 'WEB201']

const API_BASE = 'http://localhost:8102'

// ── Integration mode watcher ───────────────────────────────────────

watch(
  () => props.selection,
  (sel) => {
    if (sel) {
      mode.value = 'integration'
      submitEnrollmentForStudent(sel.studentId, sel.courseId)
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.selection) {
    mode.value = 'integration'
    submitEnrollmentForStudent(props.selection.studentId, props.selection.courseId)
  }
})

// ── Methods ────────────────────────────────────────────────────────

function resetResult() {
  decision.value = null
  error.value = ''
}

async function submitEnrollment() {
  if (!selectedStudentId.value || !selectedCourseId.value) return
  await submitEnrollmentForStudent(selectedStudentId.value, selectedCourseId.value)
}

async function submitEnrollmentForStudent(studentId: string, courseId: string) {
  loading.value = true
  error.value = ''
  decision.value = null

  try {
    const resp = await fetch(`${API_BASE}/api/enroll`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        course_id: courseId,
      }),
    })

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}))
      const msg = errData?.error?.message || `HTTP ${resp.status}`
      error.value = `选课失败: ${msg}`
      loading.value = false
      return
    }

    const data = await resp.json()
    decision.value = data

    emit('enrollment-decided', {
      studentId: data.student_id,
      courseId: data.course_id,
      status: data.status,
      enrollmentTraceId: data.trace_id,
    })
  } catch (e: any) {
    error.value = `网络错误: ${e.message}`
  } finally {
    loading.value = false
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    ENROLLED: '选课成功',
    WAITLISTED: '进入候补',
    REJECTED: '选课失败',
  }
  return map[status] || status
}

function ruleLabel(rule: string): string {
  const map: Record<string, string> = {
    DUPLICATE: '重复选课',
    PREREQUISITE: '先修课程',
    TIME_CONFLICT: '时间冲突',
  }
  return map[rule] || rule
}
</script>

<style scoped>
.enrollment-module {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, sans-serif;
}

h2 { color: #333; margin-bottom: 20px; }
h3 { margin-top: 20px; color: #555; }
h4 { color: #666; margin-top: 16px; }

.standalone-controls {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.form-group label {
  width: 60px;
  font-weight: 600;
}

select {
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

button {
  margin-top: 8px;
  padding: 8px 20px;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:disabled {
  background: #aaa;
  cursor: not-allowed;
}

.integration-info {
  background: #e8f4fd;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.error-message {
  background: #ffe0e0;
  color: #c00;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

.loading {
  color: #666;
  font-style: italic;
  padding: 10px 0;
}

.decision-result {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.field {
  flex: 1 1 200px;
}

.label {
  font-weight: 600;
  margin-right: 4px;
}

.pass { color: #2a0; font-weight: 600; }
.block { color: #c00; font-weight: 600; }
.status-enrolled { color: #2a0; font-weight: 700; }
.status-waitlisted { color: #e67e00; font-weight: 700; }
.status-rejected { color: #c00; font-weight: 700; }
.waitlist-rank { color: #e67e00; font-weight: 600; }
.trace-id { font-family: monospace; font-size: 13px; }

.checks-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}

.checks-table th,
.checks-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  font-size: 14px;
}

.checks-table th {
  background: #f0f0f0;
  font-weight: 600;
}

.check-pass { background: #f0fff0; }
.check-fail { background: #fff0f0; }
</style>
