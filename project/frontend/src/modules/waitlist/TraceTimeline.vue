<script setup lang="ts">
import { computed } from "vue";

import type { TraceEvent } from "./types";


const props = defineProps<{
  events: TraceEvent[];
}>();


const eventLabels: Record<string, string> = {
  SEAT_RELEASED: "释放名额",
  WAITLIST_RECOMPUTED: "开始候补重算",
  WAITLIST_ELIGIBILITY_CHECKED: "重新检查资格",
  WAITLIST_SKIPPED: "候补跳过",
  WAITLIST_PROMOTED: "候补补入",
  SCENARIO_RESET: "重置演示场景",
};


const orderedEvents = computed(() =>
  [...props.events].sort(
    (left, right) =>
      new Date(left.created_at).getTime() - new Date(right.created_at).getTime(),
  ),
);


function describe(event: TraceEvent): string {
  const student = event.payload.student_id;
  const reason = event.payload.reason;
  if (typeof student === "string" && typeof reason === "string") {
    return `${student}：${reason}`;
  }
  if (typeof student === "string") {
    return student;
  }
  const course = event.payload.course_id;
  return typeof course === "string" ? course : "";
}
</script>

<template>
  <section class="trace" aria-labelledby="trace-title">
    <h3 id="trace-title">决策追溯</h3>
    <p v-if="orderedEvents.length === 0" class="empty">暂无追溯事件</p>
    <ol v-else>
      <li v-for="event in orderedEvents" :key="event.event_id">
        <div>
          <strong>{{ eventLabels[event.event_type] ?? event.event_type }}</strong>
          <span>{{ event.actor }}</span>
        </div>
        <p v-if="describe(event)">{{ describe(event) }}</p>
        <time :datetime="event.created_at">
          {{ new Date(event.created_at).toLocaleString("zh-CN") }}
        </time>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.trace {
  margin-top: 24px;
}

.trace h3 {
  margin-bottom: 12px;
}

.trace ol {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.trace li {
  padding-left: 14px;
  border-left: 3px solid #4263eb;
}

.trace li div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.trace span,
.trace time,
.empty {
  color: #667085;
  font-size: 0.875rem;
}

.trace p {
  margin: 5px 0;
}
</style>
