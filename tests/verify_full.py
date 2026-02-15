# -*- coding: utf-8 -*-
"""完整验证脚本：API 接口与前端页面验证。"""
import sys
import io
import urllib.request
import json

# 解决 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"


def verify_homepage():
    """验证首页 HTML 加载。"""
    print("=" * 60)
    print("验证 1: 首页 HTML 加载")
    print("=" * 60)
    r = urllib.request.urlopen(f"{BASE}/")
    html = r.read().decode("utf-8")
    checks = {
        "HTML 长度": f"{len(html)} 字符",
        "包含标题": "猫咪健康诊断" in html,
        "包含品种选择(cat-breed)": "cat-breed" in html,
        "包含症状容器(symptoms-container)": "symptoms-container" in html,
        "包含 app.js": "app.js" in html,
        "包含 style.css": "style.css" in html,
        "包含步骤指引(step-1/2/3)": "step-1" in html and "step-2" in html,
    }
    for k, v in checks.items():
        status = "PASS" if v else "FAIL"
        print(f"  [{status}] {k}: {v}")
    return all(v for v in checks.values() if isinstance(v, bool))


def verify_symptoms():
    """验证症状接口。"""
    print()
    print("=" * 60)
    print("验证 2: GET /api/symptoms")
    print("=" * 60)
    r = urllib.request.urlopen(f"{BASE}/api/symptoms")
    data = json.loads(r.read())
    cats = data["categories"]
    print(f"  分类数: {len(cats)}")
    total = 0
    for cat in cats:
        count = len(cat["symptoms"])
        total += count
        print(f"    {cat['icon']} {cat['name']}: {count}个症状")
    print(f"  总计: {total}个症状")
    ok = len(cats) > 0 and total > 20
    print(f"  [{'PASS' if ok else 'FAIL'}] 症状数据充足")
    return ok


def verify_breeds():
    """验证品种接口。"""
    print()
    print("=" * 60)
    print("验证 3: GET /api/breeds")
    print("=" * 60)
    r = urllib.request.urlopen(f"{BASE}/api/breeds")
    breeds = json.loads(r.read())
    print(f"  品种数: {len(breeds)}")
    for b in breeds[:5]:
        print(f"    - {b['id']}: {b['name']}")
    if len(breeds) > 5:
        print(f"    ... 后续省略，共 {len(breeds)} 个品种")
    ok = len(breeds) >= 20
    print(f"  [{'PASS' if ok else 'FAIL'}] 品种数 >= 20")
    return ok


def verify_diagnose_basic():
    """验证基础诊断功能。"""
    print()
    print("=" * 60)
    print("验证 4: POST /api/diagnose (消化道症状)")
    print("=" * 60)
    payload = {
        "symptoms": ["vomiting", "diarrhea", "appetite_loss", "lethargy"]
    }
    req = urllib.request.Request(
        f"{BASE}/api/diagnose",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f"  结果数: {data['results_count']}")
    for res in data["results"][:3]:
        print(f"    {res['match_score']}% - {res['disease_name']} ({res['severity']})")
        print(f"      药物: {len(res['treatment'].get('medications', []))}种")
        print(f"      就医: {res['treatment'].get('vet_urgency', 'N/A')}")
    ok = data["results_count"] > 0
    has_treatment = all(
        "treatment" in r and r["treatment"].get("medications")
        for r in data["results"][:3]
    )
    print(f"  [{'PASS' if ok else 'FAIL'}] 有诊断结果")
    print(f"  [{'PASS' if has_treatment else 'FAIL'}] 治疗方案完整")
    return ok and has_treatment


def verify_breed_specific():
    """验证品种专属诊断逻辑。"""
    print()
    print("=" * 60)
    print("验证 5: POST /api/diagnose (折耳猫 + 骨骼症状)")
    print("=" * 60)
    payload = {
        "symptoms": ["limping", "stiffness"],
        "breed_id": "scottish_fold",
    }
    req = urllib.request.Request(
        f"{BASE}/api/diagnose",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f"  结果数: {data['results_count']}")
    has_osteo = False
    has_breed_advice = False
    for res in data["results"]:
        star = ""
        if res["disease_id"] == "osteochondrodysplasia":
            has_osteo = True
            if res.get("breed_advice") and len(res["breed_advice"]) > 0:
                has_breed_advice = True
                star = " ★品种专属"
        print(f"    {res['match_score']}% - {res['disease_name']}{star}")
        if res.get("breed_advice"):
            for advice in res["breed_advice"][:2]:
                print(f"      建议: {advice}")
    print(f"  [{'PASS' if has_osteo else 'FAIL'}] 匹配到软骨骨营养不良")
    print(f"  [{'PASS' if has_breed_advice else 'FAIL'}] 包含品种专属建议")
    return has_osteo and has_breed_advice


def verify_no_breed():
    """验证不选择品种时的正常诊断。"""
    print()
    print("=" * 60)
    print("验证 6: POST /api/diagnose (不选品种)")
    print("=" * 60)
    payload = {"symptoms": ["sneezing", "runny_nose", "watery_eyes"]}
    req = urllib.request.Request(
        f"{BASE}/api/diagnose",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f"  结果数: {data['results_count']}")
    for res in data["results"][:2]:
        print(f"    {res['match_score']}% - {res['disease_name']}")
    ok = data["results_count"] > 0
    print(f"  [{'PASS' if ok else 'FAIL'}] 不选品种也能正常诊断")
    return ok


if __name__ == "__main__":
    results = []
    results.append(("首页 HTML", verify_homepage()))
    results.append(("症状接口", verify_symptoms()))
    results.append(("品种接口", verify_breeds()))
    results.append(("基础诊断", verify_diagnose_basic()))
    results.append(("品种专属", verify_breed_specific()))
    results.append(("无品种诊断", verify_no_breed()))

    print()
    print("=" * 60)
    print("总结")
    print("=" * 60)
    all_pass = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{status}] {name}")

    if all_pass:
        print("\n  ✅ 全部验证通过！")
    else:
        print("\n  ❌ 存在失败项，请检查")
