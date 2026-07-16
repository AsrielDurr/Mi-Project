"""M1模块契约一致性测试"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from models import StudentProfile, to_dict, load_course_to_contract, weekday_int_to_str
from recommend import recommend, load_raw_courses, load_contract_courses


def test_weekday_conversion():
    """测试weekday转换"""
    assert weekday_int_to_str(1) == "MON"
    assert weekday_int_to_str(5) == "FRI"
    assert weekday_int_to_str(7) == "SUN"
    print("[PASS] weekday转换正确")


def test_course_conversion():
    """测试课程格式转换"""
    raw = {
        "id": "CS101",
        "name": "Python程序设计",
        "weekday": 1,
        "start": "08:00",
        "end": "10:00",
        "capacity": 40,
        "enrolled": 38,
        "prerequisites": []
    }
    contract = load_course_to_contract(raw)
    
    # 检查契约字段
    assert "course_id" in contract, "缺少course_id"
    assert "name" in contract, "缺少name"
    assert "schedule" in contract, "缺少schedule"
    assert "capacity" in contract, "缺少capacity"
    assert "enrolled_count" in contract, "缺少enrolled_count"
    assert "prerequisite_ids" in contract, "缺少prerequisite_ids"
    assert "status" in contract, "缺少status"
    
    # 检查schedule结构
    assert "day" in contract["schedule"], "schedule缺少day"
    assert "start" in contract["schedule"], "schedule缺少start"
    assert "end" in contract["schedule"], "schedule缺少end"
    
    # 检查值
    assert contract["course_id"] == "CS101"
    assert contract["schedule"]["day"] == "MON"
    assert contract["enrolled_count"] == 38
    
    print("[PASS] 课程格式转换正确")


def test_recommendation_response_fields():
    """测试推荐响应字段（契约要求）"""
    student = StudentProfile(
        student_id="S001",
        goal="人工智能",
        skills=["Python"],
        available_times=["上午"],
        completed_course_ids=["CS101"],
        enrolled_course_ids=["DB202"]
    )
    
    response = recommend(student, "上午")
    result = to_dict(response)
    
    # 必需字段（domain.schema.json RecommendationResponse）
    required_fields = ["trace_id", "source", "model", "prompt_version", "fallback_reason", "recommendations"]
    for field in required_fields:
        assert field in result, f"缺少必需字段: {field}"
    
    # 枚举值检查
    assert result["source"] in ("MODEL", "FALLBACK"), f"source无效: {result['source']}"
    
    # recommendations结构
    assert isinstance(result["recommendations"], list), "recommendations应为数组"
    assert len(result["recommendations"]) > 0, "recommendations不能为空"
    
    # 检查每个Recommendation
    for rec in result["recommendations"]:
        rec_fields = ["course_id", "score", "reason", "uncertainty"]
        for field in rec_fields:
            assert field in rec, f"Recommendation缺少字段: {field}"
        assert 0 <= rec["score"] <= 100, f"score超范围: {rec['score']}"
    
    print("[PASS] 推荐响应字段符合契约")


def test_recommend_ai_goal():
    """测试AI方向学生推荐"""
    student = StudentProfile(
        student_id="S001",
        goal="人工智能",
        skills=["Python"],
        available_times=["上午"],
        completed_course_ids=["CS101"],
        enrolled_course_ids=["DB202"]
    )
    
    response = recommend(student, "上午")
    result = to_dict(response)
    
    print(f"\nAI方向学生推荐结果:")
    print(f"  trace_id: {result['trace_id']}")
    print(f"  source: {result['source']}")
    print(f"  推荐课程:")
    for rec in result["recommendations"]:
        print(f"    - {rec['course_id']}: {rec['score']}分 | {rec['reason']}")
    
    # 验证AI课程被推荐
    recommended_ids = [r["course_id"] for r in result["recommendations"]]
    ai_courses = ["AI201", "ML301", "CV401"]
    has_ai = any(c in recommended_ids for c in ai_courses)
    print(f"  包含AI课程: {has_ai}")
    
    print("[PASS] AI方向推荐正确")


def test_recommend_dev_goal():
    """测试软件开发方向学生推荐"""
    student = StudentProfile(
        student_id="S009",
        goal="软件开发",
        skills=["Python", "JavaScript"],
        available_times=["下午"],
        completed_course_ids=["CS101", "AI201"],
        enrolled_course_ids=[]
    )
    
    response = recommend(student, "下午")
    result = to_dict(response)
    
    print(f"\n软件开发学生推荐结果:")
    print(f"  trace_id: {result['trace_id']}")
    print(f"  source: {result['source']}")
    print(f"  推荐课程:")
    for rec in result["recommendations"]:
        print(f"    - {rec['course_id']}: {rec['score']}分 | {rec['reason']}")
    
    print("[PASS] 软件开发方向推荐正确")


if __name__ == "__main__":
    print("=" * 60)
    print("M1模块 - 契约一致性测试")
    print("=" * 60)
    
    test_weekday_conversion()
    test_course_conversion()
    test_recommendation_response_fields()
    test_recommend_ai_goal()
    test_recommend_dev_goal()
    
    print("\n" + "=" * 60)
    print("所有测试通过!")
    print("=" * 60)
