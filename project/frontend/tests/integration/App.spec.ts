import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import App from "../../src/integration/App.vue";


describe("teacher course switching", () => {
  afterEach(() => {
    window.history.replaceState({}, "", "/student");
  });

  it("offers all demo courses and passes the selected course to the waitlist module", async () => {
    window.history.replaceState({}, "", "/teacher");
    const wrapper = mount(App, {
      global: {
        stubs: {
          WaitlistModule: {
            props: ["api", "courseId"],
            template: '<div data-test="waitlist-stub">{{ courseId }}</div>',
          },
        },
      },
    });

    const selector = wrapper.get('[data-test="teacher-course-select"]');
    expect(selector.findAll("option")).toHaveLength(8);
    expect(wrapper.get('[data-test="waitlist-stub"]').text()).toBe("AI201");

    await selector.setValue("ALG201");

    expect(wrapper.get('[data-test="waitlist-stub"]').text()).toBe("ALG201");
  });
});

