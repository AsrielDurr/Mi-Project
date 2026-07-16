<script setup lang="ts">
import { ref } from "vue";

import type {
  CourseSelectedEvent,
  RecommendationApi,
  RecommendationResponse,
  StudentProfile,
} from "./types";

const props = defineProps<{ api: RecommendationApi; studentId?: string }>();
const emit = defineEmits<{ "course-selected": [event: CourseSelectedEvent] }>();

const goal = ref("人工智能");
const loading = ref(false);
const error = ref("");
const result = ref<RecommendationResponse | null>(null);

async function runRecommendation(): Promise<void> {
  if (!goal.value.trim()) {
    error.value = "请输入学习目标";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    const student: StudentProfile = {
      student_id: props.studentId ?? "S001",
      goal: goal.value.trim(),
      skills: ["Python"],
      available_times: ["上午"],
      completed_course_ids: ["CS101"],
      enrolled_course_ids: ["DB202"],
    };
    result.value = await props.api.recommend(student);
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "推荐失败";
  } finally {
    loading.value = false;
  }
}

function selectCourse(courseId: string): void {
  if (!result.value) return;
  emit("course-selected", {
    studentId: props.studentId ?? "S001",
    courseId,
    recommendationTraceId: result.value.trace_id,
  });
}
</script>

<template>
  <section class="recommendation-module">
    <p class="eyebrow">M1 · AI课程推荐</p>
    <h1>找到适合你的下一门课</h1>
    <form @submit.prevent="runRecommendation">
      <label for="goal">学习目标</label>
      <input id="goal" v-model="goal" placeholder="例如：人工智能" />
      <button type="submit" :disabled="loading">
        {{ loading ? "MiMo分析中..." : "获取AI推荐" }}
      </button>
    </form>
    <p v-if="error" role="alert" class="error">{{ error }}</p>

    <aside v-if="result?.source === 'MODEL'" class="source model">
      AI推荐 · MiMo {{ result.model }}
    </aside>
    <aside v-if="result?.source === 'FALLBACK'" class="source fallback">
      <strong>降级推荐</strong>
      <span>{{ result.fallback_reason }}</span>
    </aside>

    <div v-if="result" class="cards">
      <article v-for="item in result.recommendations" :key="item.course_id">
        <header><strong>{{ item.course_id }}</strong><b>{{ item.score }}分</b></header>
        <p>{{ item.reason }}</p>
        <small>{{ item.uncertainty }}</small>
        <button type="button" @click="selectCourse(item.course_id)">选择这门课</button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.recommendation-module { max-width: 760px; margin: 0 auto; padding: 24px; font-family: system-ui, sans-serif; }
.eyebrow { color: #3451db; font-weight: 700; }
form { display: flex; gap: 10px; align-items: end; padding: 18px; background: #f5f7ff; border-radius: 12px; }
label { font-weight: 700; }
input { flex: 1; padding: 10px; border: 1px solid #bdc5dd; border-radius: 8px; }
button { padding: 10px 16px; border: 0; border-radius: 8px; background: #2f4ee6; color: white; cursor: pointer; }
.source { margin-top: 18px; padding: 12px; border-radius: 8px; display: flex; gap: 12px; }
.model { background: #e9f8ee; color: #176b36; }
.fallback { background: #fff1cc; color: #7c5700; }
.cards { display: grid; gap: 12px; margin-top: 16px; }
article { border: 1px solid #d8ddeb; border-radius: 12px; padding: 16px; }
article header { display: flex; justify-content: space-between; }
article button { margin-top: 12px; }
.error { color: #b42318; }
small { color: #667085; }
</style>
