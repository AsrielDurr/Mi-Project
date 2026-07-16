import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import WaitlistModule from "../../src/modules/waitlist/WaitlistModule.vue";
import type { WaitlistApi } from "../../src/modules/waitlist/types";


const courseStatus = {
  course: {
    course_id: "AI201",
    name: "人工智能基础",
    description: "",
    schedule: { day: "TUE", start: "10:00", end: "12:00" },
    capacity: 30,
    enrolled_count: 30,
    prerequisite_ids: ["CS101"],
    status: "OPEN",
  },
  available_seats: 0,
  enrolled_student_ids: [],
  waitlist: [
    {
      student_id: "S002",
      course_id: "AI201",
      position: 1,
      applied_at: "2026-07-16T09:00:00+08:00",
      status: "WAITING",
      last_check_reason: null,
    },
    {
      student_id: "S005",
      course_id: "AI201",
      position: 2,
      applied_at: "2026-07-16T09:05:00+08:00",
      status: "WAITING",
      last_check_reason: null,
    },
  ],
} as const;


function createApi(): WaitlistApi {
  return {
    getCourseStatus: vi.fn().mockResolvedValue(courseStatus),
    releaseSeat: vi.fn().mockResolvedValue({
      trace_id: "trace-seat-001",
      course_id: "AI201",
      capacity_before: 30,
      capacity_after: 31,
      enrolled_count: 30,
      available_seats: 1,
    }),
    recomputeWaitlist: vi.fn().mockResolvedValue({
      trace_id: "trace-recompute-001",
      course_id: "AI201",
      available_seats_before: 1,
      checked: [
        {
          student_id: "S002",
          waitlist_status: "SKIPPED",
          reason: "与DB202上课时间冲突",
        },
        {
          student_id: "S005",
          waitlist_status: "PROMOTED",
          reason: "资格有效并成功补入",
        },
      ],
      promoted_student_ids: ["S005"],
    }),
    getTrace: vi.fn().mockResolvedValue({
      trace_id: "trace-recompute-001",
      events: [],
    }),
    resetScenario: vi.fn().mockResolvedValue({
      trace_id: "trace-reset-001",
      scenario_id: "waitlist_recompute",
      course_ids: ["AI201"],
      student_ids: ["S002", "S005"],
    }),
  };
}


describe("WaitlistModule", () => {
  it("shows course capacity and ordered waitlist", async () => {
    const api = createApi();
    const wrapper = mount(WaitlistModule, {
      props: { api, courseId: "AI201" },
    });

    await flushPromises();

    expect(wrapper.text()).toContain("人工智能基础");
    expect(wrapper.text()).toContain("30 / 30");
    expect(wrapper.text()).toContain("S002");
    expect(wrapper.text()).toContain("S005");
    expect(wrapper.text().indexOf("S002")).toBeLessThan(
      wrapper.text().indexOf("S005"),
    );
  });

  it("releases a seat through the API without changing state locally", async () => {
    const api = createApi();
    const wrapper = mount(WaitlistModule, {
      props: { api, courseId: "AI201" },
    });
    await flushPromises();

    await wrapper.get('[data-test="release-seat"]').trigger("click");
    await flushPromises();

    expect(api.releaseSeat).toHaveBeenCalledTimes(1);
    expect(api.releaseSeat).toHaveBeenCalledWith("AI201");
    expect(api.getCourseStatus).toHaveBeenCalledTimes(2);
  });

  it("shows skipped and promoted candidates after recomputation", async () => {
    const api = createApi();
    const wrapper = mount(WaitlistModule, {
      props: { api, courseId: "AI201" },
    });
    await flushPromises();

    await wrapper.get('[data-test="recompute"]').trigger("click");
    await flushPromises();

    expect(api.recomputeWaitlist).toHaveBeenCalledWith("AI201");
    expect(wrapper.text()).toContain("S002");
    expect(wrapper.text()).toContain("已跳过");
    expect(wrapper.text()).toContain("与DB202上课时间冲突");
    expect(wrapper.text()).toContain("S005");
    expect(wrapper.text()).toContain("已补入");
  });
});

