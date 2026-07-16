<script setup lang="ts">
import { ref, watch } from "vue";

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

watch(() => props.studentId, () => {
  result.value = null;
  error.value = "";
});

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
  <section class="module">
    <p class="eyebrow">M1 · AI课程推荐</p>
    <h1>找到适合你的下一门课</h1>

    <form @submit.prevent="runRecommendation">
      <label for="goal">学习目标</label>
      <input id="goal" v-model="goal" placeholder="例如：人工智能" />
      <button type="submit" class="primary" :disabled="loading">
        {{ loading ? "MiMo分析中..." : "获取AI推荐" }}
      </button>
    </form>

    <p v-if="error" role="alert" class="error">{{ error }}</p>

    <aside v-if="result?.source === 'MODEL'" class="banner model">
      AI推荐 · MiMo {{ result.model }}
    </aside>
    <aside v-if="result?.source === 'FALLBACK'" class="banner fallback">
      <strong>降级推荐</strong>
      <span>{{ result.fallback_reason }}</span>
    </aside>

    <div v-if="result" class="cards">
      <article v-for="item in result.recommendations" :key="item.course_id">
        <header>
          <strong>{{ item.course_name || item.course_id }}</strong>
          <span class="score">{{ item.score }}分</span>
        </header>
        <p>{{ item.reason }}</p>
        <small>{{ item.uncertainty }}</small>
        <button type="button" class="primary" @click="selectCourse(item.course_id)">选择这门课</button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.module {
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
  color: #182230;
}

h1 { margin: 0 0 20px; font-size: 1.5rem; }

.eyebrow {
  margin-bottom: 6px;
  color: #4263eb;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

form {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 20px;
  border: 1px solid #dfe3eb;
  border-radius: 14px;
  background: #fff;
}

label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

input {
  flex: 1;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid #c8cfdd;
  border-radius: 9px;
  font: inherit;
  font-size: 14px;
  color: #182230;
  background: #fff;
}
input::placeholder { color: #a0a6b5; }
input:focus { outline: none; border-color: #4263eb; box-shadow: 0 0 0 3px rgba(66, 99, 235, 0.12); }

button {
  min-height: 40px;
  padding: 0 18px;
  border-radius: 9px;
  font: inherit;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}
button:disabled { cursor: wait; opacity: 0.55; }

.primary {
  border: 1px solid #3151d3;
  color: #fff;
  background: #4263eb;
}
.primary:hover:not(:disabled) { background: #3451db; }

.banner {
  margin-top: 16px;
  padding: 14px 18px;
  border-radius: 10px;
  display: flex;
  gap: 12px;
  font-size: 14px;
}
.model  { color: #067647; background: #dcfae6; }
.fallback { color: #7c5700; background: #fff1cc; }

.cards {
  display: grid;
  gap: 14px;
  margin-top: 16px;
}

article {
  padding: 20px;
  border: 1px solid #dfe3eb;
  border-radius: 14px;
  background: #fff;
}

article header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

article header strong { font-size: 1.05rem; }

.score {
  font-weight: 700;
  font-size: 1.1rem;
  color: #4263eb;
}

article p { margin: 0 0 8px; font-size: 14px; line-height: 1.5; color: #344054; }

article small { display: block; margin-bottom: 12px; color: #667085; font-size: 13px; line-height: 1.5; }

article button { width: 100%; }

.error {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #b42318;
  background: #fee4e2;
  font-size: 14px;
}
</style>
