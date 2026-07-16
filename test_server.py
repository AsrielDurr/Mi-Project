"""测试M1服务"""

import json
import requests

BASE_URL = "http://localhost:8001"

def test_health():
    print("1. 测试健康检查...")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"   状态: {resp.status_code}")
    print(f"   响应: {resp.json()}")
    return resp.status_code == 200


def test_recommend_ai_student():
    print("\n2. 测试AI方向学生推荐...")
    payload = {
        "student": {
            "student_id": "S001",
            "goal": "人工智能",
            "skills": ["Python"],
            "available_times": ["上午"],
            "completed_course_ids": ["CS101"],
            "enrolled_course_ids": ["DB202"],
            "timePreference": "上午"
        }
    }
    resp = requests.post(f"{BASE_URL}/api/recommend", json=payload)
    print(f"   状态: {resp.status_code}")
    result = resp.json()
    print(f"   trace_id: {result.get('trace_id')}")
    print(f"   source: {result.get('source')}")
    print(f"   推荐数量: {len(result.get('recommendations', []))}")
    for r in result.get("recommendations", []):
        print(f"     - {r['course_id']}: {r['score']}分 | {r['reason']}")
    return resp.status_code == 200


def test_recommend_dev_student():
    print("\n3. 测试软件开发学生推荐...")
    payload = {
        "student": {
            "student_id": "S009",
            "goal": "软件开发",
            "skills": ["Python", "JavaScript"],
            "available_times": ["下午"],
            "completed_course_ids": ["CS101", "AI201"],
            "enrolled_course_ids": [],
            "timePreference": "下午"
        }
    }
    resp = requests.post(f"{BASE_URL}/api/recommend", json=payload)
    print(f"   状态: {resp.status_code}")
    result = resp.json()
    print(f"   trace_id: {result.get('trace_id')}")
    print(f"   source: {result.get('source')}")
    print(f"   推荐数量: {len(result.get('recommendations', []))}")
    for r in result.get("recommendations", []):
        print(f"     - {r['course_id']}: {r['score']}分 | {r['reason']}")
    return resp.status_code == 200


if __name__ == "__main__":
    print("=" * 60)
    print("M1推荐模块 API 测试")
    print("=" * 60)
    
    try:
        test_health()
        test_recommend_ai_student()
        test_recommend_dev_student()
        print("\n" + "=" * 60)
        print("所有测试通过!")
        print("=" * 60)
    except requests.ConnectionError:
        print("\n错误: 无法连接到服务，请确保服务已启动")
        print("运行: python main.py")
