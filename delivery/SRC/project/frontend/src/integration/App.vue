<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { EnrollmentModule } from "../modules/enrollment";
import {
  createRecommendationApi,
  RecommendationModule,
  type CourseSelectedEvent,
} from "../modules/recommendation";
import { StudentStatusModule } from "../modules/student-status";
import { createWaitlistApi, WaitlistModule } from "../modules/waitlist";
import { courseCatalog } from "../shared/courseCatalog";

const baseUrl = import.meta.env.VITE_API_BASE_URL
  ?? `${window.location.protocol}//${window.location.hostname}:8000`;
const recommendationApi = createRecommendationApi(baseUrl);
const waitlistApi = createWaitlistApi(baseUrl);
const selection = ref<CourseSelectedEvent | null>(null);
const statusRefresh = ref(0);
const teacherCourseId = ref("AI201");
const route = ref(window.location.pathname === "/teacher" ? "teacher" : "student");
const title = computed(() => route.value === "teacher" ? "教师候补管理" : "学生选课助手");

const students = ref<{ student_id: string; name: string }[]>([]);
const currentStudentId = ref("S001");

onMounted(async () => {
  try {
    const resp = await fetch(`${baseUrl}/api/students`);
    if (resp.ok) {
      students.value = await resp.json();
      if (students.value.length > 0 && !students.value.some(s => s.student_id === currentStudentId.value)) {
        currentStudentId.value = students.value[0].student_id;
      }
    }
  } catch { /* use fallback list */ }
});

watch(currentStudentId, () => {
  selection.value = null;
});

function studentLabel(s: { student_id: string; name: string }): string {
  return s.name ? `${s.name}（${s.student_id}）` : s.student_id;
}

function navigate(next: "student" | "teacher"): void {
  route.value = next;
  window.history.pushState({}, "", `/${next}`);
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div><b>AI课程选课系统</b><span>{{ title }}</span></div>
      <nav class="topbar-center">
        <label class="student-select" v-if="route === 'student'">
          <span>当前学生</span>
          <select v-model="currentStudentId" @change="statusRefresh++">
            <option v-for="s in students" :key="s.student_id" :value="s.student_id">
              {{ studentLabel(s) }}
            </option>
          </select>
        </label>
      </nav>
      <nav>
        <button :class="{ active: route === 'student' }" @click="navigate('student')">学生端</button>
        <button :class="{ active: route === 'teacher' }" @click="navigate('teacher')">教师端</button>
      </nav>
    </header>
    <main v-if="route === 'student'" class="student-layout">
      <div class="student-grid">
        <RecommendationModule
          :api="recommendationApi"
          :student-id="currentStudentId"
          @course-selected="selection = $event"
        />
        <EnrollmentModule
          :selection="selection"
          :student-id="currentStudentId"
          :api-base="baseUrl"
          @enrollment-decided="statusRefresh++"
        />
      </div>
      <StudentStatusModule
        :student-id="currentStudentId"
        :api-base="baseUrl"
        :refresh-trigger="statusRefresh"
      />
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
:global(body) {
  margin: 0;
  color: #182230;
  background: #f5f7fb;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
}
.app-shell { min-height: 100vh; }
.topbar { display: flex; justify-content: space-between; align-items: center; gap: 20px; padding: 14px 28px; background: #fff; border-bottom: 1px solid #e4e7ef; }
.topbar > div { display: flex; gap: 12px; align-items: baseline; }
.topbar span { color: #667085; }

.topbar-center { flex: 1; display: flex; justify-content: center; }
.student-select { display: flex; align-items: center; gap: 10px; }
.student-select span { font-weight: 700; font-size: 14px; color: #344054; }
.student-select select {
  min-height: 36px;
  min-width: 200px;
  padding: 0 12px;
  border: 1px solid #c8cfdd;
  border-radius: 9px;
  font: inherit;
  font-size: 14px;
  color: #182230;
  background: #fff;
}

nav { display: flex; gap: 8px; }
nav button { min-height: 36px; padding: 0 16px; border: 0; border-radius: 9px; background: #edf0f7; font: inherit; font-size: 14px; font-weight: 600; cursor: pointer; }
nav button.active { background: #4263eb; color: #fff; }
.student-layout { padding: 24px; max-width: 1280px; margin: 0 auto; }
.student-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; align-items: start; }
.teacher-page { padding-top: 24px; }
.course-toolbar { display: flex; align-items: center; gap: 12px; width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 16px 20px; border: 1px solid #dfe3eb; border-radius: 14px; background: #fff; font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif; }
.course-toolbar label { font-weight: 700; }
.course-toolbar select { min-width: 240px; min-height: 40px; padding: 0 12px; border: 1px solid #c8cfdd; border-radius: 9px; color: #182230; background: #fff; font: inherit; }
@media (max-width: 900px) { .student-grid { grid-template-columns: 1fr; } .topbar { flex-wrap: wrap; } }
</style>
