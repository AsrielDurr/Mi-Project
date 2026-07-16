<script setup lang="ts">
import { computed, ref } from "vue";

import { EnrollmentModule } from "../modules/enrollment";
import {
  createRecommendationApi,
  RecommendationModule,
  type CourseSelectedEvent,
} from "../modules/recommendation";
import { createWaitlistApi, WaitlistModule } from "../modules/waitlist";
import { courseCatalog } from "../shared/courseCatalog";

const baseUrl = import.meta.env.VITE_API_BASE_URL
  ?? `${window.location.protocol}//${window.location.hostname}:8000`;
const recommendationApi = createRecommendationApi(baseUrl);
const waitlistApi = createWaitlistApi(baseUrl);
const selection = ref<CourseSelectedEvent | null>(null);
const teacherCourseId = ref("AI201");
const route = ref(window.location.pathname === "/teacher" ? "teacher" : "student");
const title = computed(() => route.value === "teacher" ? "教师候补管理" : "学生选课助手");

function navigate(next: "student" | "teacher"): void {
  route.value = next;
  window.history.pushState({}, "", `/${next}`);
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div><b>AI课程选课系统</b><span>{{ title }}</span></div>
      <nav>
        <button :class="{ active: route === 'student' }" @click="navigate('student')">学生端</button>
        <button :class="{ active: route === 'teacher' }" @click="navigate('teacher')">教师端</button>
      </nav>
    </header>
    <main v-if="route === 'student'" class="student-grid">
      <RecommendationModule
        :api="recommendationApi"
        student-id="S001"
        @course-selected="selection = $event"
      />
      <EnrollmentModule :selection="selection" :api-base="baseUrl" />
    </main>
    <main v-else class="teacher-page">
      <section class="course-toolbar" aria-label="教师端课程切换">
        <label for="teacher-course">查看课程</label>
        <select
          id="teacher-course"
          v-model="teacherCourseId"
          data-test="teacher-course-select"
        >
          <option
            v-for="course in courseCatalog"
            :key="course.courseId"
            :value="course.courseId"
          >
            {{ course.name }}（{{ course.courseId }}）
          </option>
        </select>
      </section>
      <WaitlistModule :api="waitlistApi" :course-id="teacherCourseId" />
    </main>
  </div>
</template>

<style scoped>
:global(body) { margin: 0; background: #f7f8fc; color: #172033; }
.app-shell { min-height: 100vh; }
.topbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 28px; background: #fff; border-bottom: 1px solid #e4e7ef; font-family: system-ui, sans-serif; }
.topbar div { display: flex; gap: 12px; align-items: baseline; }
.topbar span { color: #667085; }
nav { display: flex; gap: 8px; }
nav button { border: 0; padding: 8px 14px; border-radius: 8px; background: #edf0f7; cursor: pointer; }
nav button.active { background: #2f4ee6; color: #fff; }
.student-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; padding: 24px; align-items: start; }
.teacher-page { padding-top: 24px; }
.course-toolbar { display: flex; align-items: center; gap: 12px; width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 16px 20px; border: 1px solid #dfe3eb; border-radius: 14px; background: #fff; font-family: system-ui, sans-serif; }
.course-toolbar label { font-weight: 700; }
.course-toolbar select { min-width: 240px; min-height: 40px; padding: 0 12px; border: 1px solid #c8cfdd; border-radius: 9px; color: #172033; background: #fff; font: inherit; }
@media (max-width: 900px) { .student-grid { grid-template-columns: 1fr; } }
</style>

