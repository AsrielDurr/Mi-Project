import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TraceTimeline from "../../src/modules/waitlist/TraceTimeline.vue";


describe("TraceTimeline", () => {
  it("renders events in chronological order", () => {
    const wrapper = mount(TraceTimeline, {
      props: {
        events: [
          {
            event_id: "event-001",
            trace_id: "trace-001",
            event_type: "SEAT_RELEASED",
            actor: "TEACHER",
            payload: { course_id: "AI201" },
            created_at: "2026-07-16T10:00:00+08:00",
          },
          {
            event_id: "event-002",
            trace_id: "trace-001",
            event_type: "WAITLIST_PROMOTED",
            actor: "SYSTEM",
            payload: { student_id: "S005" },
            created_at: "2026-07-16T10:00:02+08:00",
          },
        ],
      },
    });

    expect(wrapper.text()).toContain("释放名额");
    expect(wrapper.text()).toContain("候补补入");
    expect(wrapper.text().indexOf("释放名额")).toBeLessThan(
      wrapper.text().indexOf("候补补入"),
    );
  });
});
