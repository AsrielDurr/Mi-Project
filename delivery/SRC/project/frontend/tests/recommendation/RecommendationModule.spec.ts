import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import RecommendationModule from "../../src/modules/recommendation/RecommendationModule.vue";
import type { RecommendationApi } from "../../src/modules/recommendation/types";

function api(source: "MODEL" | "FALLBACK" = "MODEL"): RecommendationApi {
  return {
    recommend: vi.fn().mockResolvedValue({
      trace_id: "trace-rec-1",
      source,
      model: source === "MODEL" ? "mimo-test" : null,
      prompt_version: "v1",
      fallback_reason: source === "FALLBACK" ? "MiMo超时" : null,
      recommendations: [{
        course_id: "AI201", score: 92, reason: "匹配AI目标", uncertainty: "需确认数学基础",
      }],
    }),
  };
}

describe("RecommendationModule", () => {
  it("marks a successful model recommendation as MiMo", async () => {
    const wrapper = mount(RecommendationModule, { props: { api: api() } });
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(wrapper.text()).toContain("AI推荐 · MiMo");
    expect(wrapper.text()).toContain("AI201");
  });

  it("marks fallback visibly and emits the frozen course-selected event", async () => {
    const wrapper = mount(RecommendationModule, { props: { api: api("FALLBACK") } });
    await wrapper.get("form").trigger("submit");
    await flushPromises();
    expect(wrapper.text()).toContain("降级推荐");
    expect(wrapper.text()).toContain("MiMo超时");
    await wrapper.get("article button").trigger("click");
    expect(wrapper.emitted("course-selected")?.[0]?.[0]).toEqual({
      studentId: "S001", courseId: "AI201", recommendationTraceId: "trace-rec-1",
    });
  });

  it("rejects an empty goal without calling the API", async () => {
    const recommendationApi = api();
    const wrapper = mount(RecommendationModule, { props: { api: recommendationApi } });
    await wrapper.get("input").setValue("   ");
    await wrapper.get("form").trigger("submit");
    expect(wrapper.text()).toContain("请输入学习目标");
    expect(recommendationApi.recommend).not.toHaveBeenCalled();
  });
});
