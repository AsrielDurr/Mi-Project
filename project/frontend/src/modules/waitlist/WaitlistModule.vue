<script setup lang="ts">
import { onMounted, ref } from "vue";

import TraceTimeline from "./TraceTimeline.vue";
import type {
  CourseStatusResponse,
  RecomputeResult,
  TraceEvent,
  WaitlistApi,
  WaitlistStatus,
} from "./types";


const props = withDefaults(
  defineProps<{
    api: WaitlistApi;
    courseId?: string;
  }>(),
  {
    courseId: "AI201",
  },
);


const courseStatus = ref<CourseStatusResponse | null>(null);
const recomputeResult = ref<RecomputeResult | null>(null);
const traceEvents = ref<TraceEvent[]>([]);
const loading = ref(false);
const error = ref("");
const message = ref("");


const waitlistLabels: Record<WaitlistStatus, string> = {
  WAITING: "等待中",
  PROMOTED: "已补入",
  SKIPPED: "已跳过",
};


async function loadStatus(): Promise<void> {
  courseStatus.value = await props.api.getCourseStatus(props.courseId);
}


async function loadTrace(traceId: string): Promise<void> {
  const trace = await props.api.getTrace(traceId);
  traceEvents.value = trace.events;
}


async function runAction(action: () => Promise<void>): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    await action();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "操作失败";
  } finally {
    loading.value = false;
  }
}


async function releaseSeat(): Promise<void> {
  await runAction(async () => {
    const result = await props.api.releaseSeat(props.courseId);
    message.value = `容量 ${result.capacity_before} → ${result.capacity_after}，已释放1个名额`;
    recomputeResult.value = null;
    await loadTrace(result.trace_id);
    await loadStatus();
  });
}


async function recompute(): Promise<void> {
  await runAction(async () => {
    const result = await props.api.recomputeWaitlist(props.courseId);
    recomputeResult.value = result;
    message.value = result.promoted_student_ids.length
      ? `已补入：${result.promoted_student_ids.join("、")}`
      : "本次没有学生补入";
    await loadTrace(result.trace_id);
    await loadStatus();
  });
}


async function reset(): Promise<void> {
  await runAction(async () => {
    const result = await props.api.resetScenario("waitlist_recompute");
    message.value = `场景已重置：${result.scenario_id}`;
    recomputeResult.value = null;
    traceEvents.value = [];
    await loadStatus();
  });
}


onMounted(() => {
  void runAction(loadStatus);
});
</script>

<template>
  <main class="waitlist-module">
    <header>
      <div>
        <p class="eyebrow">M3 · 候补重算与追溯</p>
        <h1>{{ courseStatus?.course.name ?? courseId }}</h1>
      </div>
      <button data-test="reset" class="secondary" :disabled="loading" @click="reset">
        重置场景
      </button>
    </header>

    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <p v-if="message" role="status" class="message">{{ message }}</p>

    <section v-if="courseStatus" class="overview" aria-label="课程状态">
      <div>
        <span>已选 / 容量</span>
        <strong>
          {{ courseStatus.course.enrolled_count }} / {{ courseStatus.course.capacity }}
        </strong>
      </div>
      <div>
        <span>可用名额</span>
        <strong>{{ courseStatus.available_seats }}</strong>
      </div>
      <div>
        <span>候补人数</span>
        <strong>{{ courseStatus.waitlist.length }}</strong>
      </div>
    </section>

    <section v-if="courseStatus" class="panel" aria-labelledby="waitlist-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">原始申请顺序保持不变</p>
          <h2 id="waitlist-title">候补名单</h2>
        </div>
        <div class="actions">
          <button
            data-test="release-seat"
            class="secondary"
            :disabled="loading"
            @click="releaseSeat"
          >
            释放一个名额
          </button>
          <button
            data-test="recompute"
            class="primary"
            :disabled="loading"
            @click="recompute"
          >
            重新计算候补
          </button>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>排名</th>
            <th>学生</th>
            <th>申请时间</th>
            <th>状态</th>
            <th>最近原因</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in courseStatus.waitlist" :key="entry.student_id">
            <td>#{{ entry.position }}</td>
            <td>{{ entry.student_id }}</td>
            <td>{{ new Date(entry.applied_at).toLocaleString("zh-CN") }}</td>
            <td>
              <span class="status" :data-status="entry.status">
                {{ waitlistLabels[entry.status] }}
              </span>
            </td>
            <td>{{ entry.last_check_reason ?? "—" }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="recomputeResult" class="panel" aria-labelledby="result-title">
      <h2 id="result-title">本次重算结果</h2>
      <ol class="result-list">
        <li v-for="item in recomputeResult.checked" :key="item.student_id">
          <strong>{{ item.student_id }}</strong>
          <span class="status" :data-status="item.waitlist_status">
            {{ waitlistLabels[item.waitlist_status] }}
          </span>
          <p>{{ item.reason }}</p>
        </li>
      </ol>
    </section>

    <TraceTimeline :events="traceEvents" />
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  color: #182230;
  background: #f5f7fb;
  font-family:
    Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
}

.waitlist-module {
  width: min(1080px, calc(100% - 32px));
  margin: 32px auto;
}

header,
.section-heading,
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 0;
}

.eyebrow {
  margin-bottom: 6px;
  color: #4263eb;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 24px 0;
}

.overview div,
.panel {
  padding: 20px;
  border: 1px solid #dfe3eb;
  border-radius: 14px;
  background: #fff;
}

.overview span {
  display: block;
  margin-bottom: 8px;
  color: #667085;
}

.overview strong {
  font-size: 1.5rem;
}

.panel {
  margin-top: 16px;
}

button {
  min-height: 40px;
  padding: 0 16px;
  border-radius: 9px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

button:disabled {
  cursor: wait;
  opacity: 0.55;
}

.primary {
  border: 1px solid #3151d3;
  color: #fff;
  background: #4263eb;
}

.secondary {
  border: 1px solid #c8cfdd;
  color: #344054;
  background: #fff;
}

table {
  width: 100%;
  margin-top: 18px;
  border-collapse: collapse;
}

th,
td {
  padding: 12px 10px;
  border-bottom: 1px solid #eaecf0;
  text-align: left;
}

th {
  color: #667085;
  font-size: 0.8rem;
}

.status {
  display: inline-flex;
  padding: 4px 9px;
  border-radius: 999px;
  background: #eef1f6;
  font-size: 0.8rem;
  font-weight: 700;
}

.status[data-status="PROMOTED"] {
  color: #067647;
  background: #dcfae6;
}

.status[data-status="SKIPPED"] {
  color: #b42318;
  background: #fee4e2;
}

.result-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.result-list li {
  display: grid;
  grid-template-columns: 100px 90px 1fr;
  align-items: center;
  gap: 12px;
}

.result-list p {
  margin: 0;
}

.error,
.message {
  margin: 16px 0;
  padding: 12px 16px;
  border-radius: 10px;
}

.error {
  color: #b42318;
  background: #fee4e2;
}

.message {
  color: #175cd3;
  background: #eff8ff;
}

@media (max-width: 720px) {
  .overview {
    grid-template-columns: 1fr;
  }

  header,
  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .actions {
    width: 100%;
    flex-wrap: wrap;
  }

  table {
    font-size: 0.85rem;
  }

  .result-list li {
    grid-template-columns: 1fr;
  }
}
</style>

