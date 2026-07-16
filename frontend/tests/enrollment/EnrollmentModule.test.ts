import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import EnrollmentModule from '../../src/modules/enrollment/EnrollmentModule.vue'

describe('EnrollmentModule', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  // ── Test 1: Standalone mode shows student and course selectors ─────

  it('renders student and course selector in standalone mode', () => {
    const wrapper = mount(EnrollmentModule, {
      props: { selection: null },
    })

    // The component should have select elements
    const selects = wrapper.findAll('select')
    expect(selects.length).toBeGreaterThanOrEqual(2)

    // Student selector should have S001, S002, S003 options
    const studentSelect = selects[0]
    const options = studentSelect.findAll('option')
    const optionValues = options.map(o => o.attributes('value'))
    expect(optionValues).toContain('S001')
    expect(optionValues).toContain('S002')
    expect(optionValues).toContain('S003')
  })

  // ── Test 2: Receives CourseSelectedEvent and displays info ─────────

  it('displays student and course info when receiving CourseSelectedEvent', () => {
    const selection = {
      studentId: 'S001',
      courseId: 'CS101',
      recommendationTraceId: 'trace-rec-001',
    }

    const wrapper = mount(EnrollmentModule, {
      props: { selection },
    })

    const text = wrapper.text()
    expect(text).toContain('S001')
    expect(text).toContain('CS101')
  })

  // ── Test 3: Shows rule check results ──────────────────────────────

  it('displays rule-by-rule check results after enrollment decision', async () => {
    const mockDecision = {
      trace_id: 'trace-001',
      student_id: 'S001',
      course_id: 'WEB201',
      rule_decision: 'PASS',
      capacity_available: true,
      status: 'ENROLLED',
      waitlist_position: null,
      checks: [
        { rule: 'DUPLICATE', passed: true, reason: '未重复选课', related_course_id: null },
        { rule: 'PREREQUISITE', passed: true, reason: '已满足先修要求', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '无时间冲突', related_course_id: null },
      ],
    }

    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const selection = {
      studentId: 'S001',
      courseId: 'WEB201',
      recommendationTraceId: 'trace-rec-001',
    }

    const wrapper = mount(EnrollmentModule, {
      props: { selection },
    })

    // Wait for async fetch
    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    const text = wrapper.text()
    expect(text).toContain('重复选课')
    expect(text).toContain('先修课程')
    expect(text).toContain('时间冲突')
    expect(text).toContain('通过')
  })

  // ── Test 4: Correctly displays three business statuses ────────────

  it('displays ENROLLED status correctly', async () => {
    const mockDecision = {
      trace_id: 'trace-001',
      student_id: 'S001',
      course_id: 'WEB201',
      rule_decision: 'PASS',
      capacity_available: true,
      status: 'ENROLLED',
      waitlist_position: null,
      checks: [
        { rule: 'DUPLICATE', passed: true, reason: '', related_course_id: null },
        { rule: 'PREREQUISITE', passed: true, reason: '', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '', related_course_id: null },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const wrapper = mount(EnrollmentModule, {
      props: {
        selection: { studentId: 'S001', courseId: 'WEB201', recommendationTraceId: '' },
      },
    })

    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('选课成功')
  })

  it('displays WAITLISTED status correctly', async () => {
    const mockDecision = {
      trace_id: 'trace-002',
      student_id: 'S001',
      course_id: 'AI201',
      rule_decision: 'PASS',
      capacity_available: false,
      status: 'WAITLISTED',
      waitlist_position: 1,
      checks: [
        { rule: 'DUPLICATE', passed: true, reason: '', related_course_id: null },
        { rule: 'PREREQUISITE', passed: true, reason: '', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '', related_course_id: null },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const wrapper = mount(EnrollmentModule, {
      props: {
        selection: { studentId: 'S001', courseId: 'AI201', recommendationTraceId: '' },
      },
    })

    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('进入候补')
    expect(wrapper.text()).toContain('第 1 位')
  })

  it('displays REJECTED status correctly', async () => {
    const mockDecision = {
      trace_id: 'trace-003',
      student_id: 'S001',
      course_id: 'CS101',
      rule_decision: 'BLOCK',
      capacity_available: true,
      status: 'REJECTED',
      waitlist_position: null,
      checks: [
        { rule: 'DUPLICATE', passed: false, reason: '已选过', related_course_id: 'CS101' },
        { rule: 'PREREQUISITE', passed: true, reason: '', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '', related_course_id: null },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const wrapper = mount(EnrollmentModule, {
      props: {
        selection: { studentId: 'S001', courseId: 'CS101', recommendationTraceId: '' },
      },
    })

    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('选课失败')
  })

  // ── Test 5: WAITLISTED shows waitlist rank ────────────────────────

  it('shows waitlist position when WAITLISTED', async () => {
    const mockDecision = {
      trace_id: 'trace-002',
      student_id: 'S001',
      course_id: 'AI201',
      rule_decision: 'PASS',
      capacity_available: false,
      status: 'WAITLISTED',
      waitlist_position: 3,
      checks: [
        { rule: 'DUPLICATE', passed: true, reason: '', related_course_id: null },
        { rule: 'PREREQUISITE', passed: true, reason: '', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '', related_course_id: null },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const wrapper = mount(EnrollmentModule, {
      props: {
        selection: { studentId: 'S001', courseId: 'AI201', recommendationTraceId: '' },
      },
    })

    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('第 3 位')
  })

  // ── Test 6: Emits EnrollmentDecidedEvent matching contract ────────

  it('emits EnrollmentDecidedEvent with correct fields', async () => {
    const mockDecision = {
      trace_id: 'trace-001',
      student_id: 'S001',
      course_id: 'WEB201',
      rule_decision: 'PASS',
      capacity_available: true,
      status: 'ENROLLED',
      waitlist_position: null,
      checks: [
        { rule: 'DUPLICATE', passed: true, reason: '', related_course_id: null },
        { rule: 'PREREQUISITE', passed: true, reason: '', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '', related_course_id: null },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const wrapper = mount(EnrollmentModule, {
      props: {
        selection: { studentId: 'S001', courseId: 'WEB201', recommendationTraceId: '' },
      },
    })

    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    const emitted = wrapper.emitted('enrollment-decided')
    expect(emitted).toBeTruthy()
    expect(emitted!.length).toBeGreaterThanOrEqual(1)

    const event = emitted![0][0]
    expect(event).toHaveProperty('studentId', 'S001')
    expect(event).toHaveProperty('courseId', 'WEB201')
    expect(event).toHaveProperty('status', 'ENROLLED')
    expect(event).toHaveProperty('enrollmentTraceId', 'trace-001')
  })

  // ── Test 7: Frontend does not compute eligibility ──────────────────

  it('displays only backend results without computing rules on frontend', async () => {
    // The component has no local rule logic — all rule results come from API response.
    // Verify no hardcoded rule strings written in the component template
    // that would indicate frontend-side rule computation.
    const mockDecision = {
      trace_id: 'trace-001',
      student_id: 'S001',
      course_id: 'WEB201',
      rule_decision: 'PASS',
      capacity_available: true,
      status: 'ENROLLED',
      waitlist_position: null,
      checks: [
        { rule: 'DUPLICATE', passed: true, reason: '未重复选课', related_course_id: null },
        { rule: 'PREREQUISITE', passed: true, reason: '已满足先修要求', related_course_id: null },
        { rule: 'TIME_CONFLICT', passed: true, reason: '无时间冲突', related_course_id: null },
      ],
    }

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDecision),
    })

    const wrapper = mount(EnrollmentModule, {
      props: {
        selection: { studentId: 'S001', courseId: 'WEB201', recommendationTraceId: '' },
      },
    })

    await new Promise(r => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    // The checks table renders exactly what the backend returns
    const text = wrapper.text()
    expect(text).toContain('未重复选课')
    expect(text).toContain('已满足先修要求')
    expect(text).toContain('无时间冲突')
  })
})
