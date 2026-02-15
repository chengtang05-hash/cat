"""验证 API 接口功能的测试脚本。"""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"

# 测试1：获取症状列表
print("=" * 50)
print("测试1: GET /api/symptoms")
print("=" * 50)
r = urllib.request.urlopen(f"{BASE}/api/symptoms")
data = json.loads(r.read())
print(f"分类数: {len(data['categories'])}")
total = 0
for cat in data["categories"]:
    count = len(cat["symptoms"])
    total += count
    print(f"  {cat['icon']} {cat['name']}: {count}个症状")
print(f"总计: {total}个症状")

# 测试2：诊断 - 呕吐+腹泻+食欲下降+精神萎靡
print("\n" + "=" * 50)
print("测试2: POST /api/diagnose (消化道症状)")
print("=" * 50)
req = urllib.request.Request(
    f"{BASE}/api/diagnose",
    data=json.dumps({"symptoms": ["vomiting", "diarrhea", "appetite_loss", "lethargy"]}).encode(),
    headers={"Content-Type": "application/json"},
)
r = urllib.request.urlopen(req)
data = json.loads(r.read())
print(f"诊断结果数: {data['results_count']}")
for res in data["results"]:
    print(f"  {res['match_score']}% - {res['disease_name']} ({res['severity']}) - 就医: {res['treatment']['vet_urgency']}")
    print(f"    匹配症状: {', '.join(res['matched_symptoms'])}")

# 测试3：泌尿系统症状
print("\n" + "=" * 50)
print("测试3: POST /api/diagnose (泌尿道症状)")
print("=" * 50)
req = urllib.request.Request(
    f"{BASE}/api/diagnose",
    data=json.dumps({"symptoms": ["straining_to_urinate", "blood_in_urine", "crying_when_urinating"]}).encode(),
    headers={"Content-Type": "application/json"},
)
r = urllib.request.urlopen(req)
data = json.loads(r.read())
print(f"诊断结果数: {data['results_count']}")
for res in data["results"]:
    print(f"  {res['match_score']}% - {res['disease_name']} ({res['severity']})")

# 测试4：皮肤症状
print("\n" + "=" * 50)
print("测试4: POST /api/diagnose (皮肤症状)")
print("=" * 50)
req = urllib.request.Request(
    f"{BASE}/api/diagnose",
    data=json.dumps({"symptoms": ["ring_shaped_lesion", "hair_loss", "skin_lesions", "dandruff"]}).encode(),
    headers={"Content-Type": "application/json"},
)
r = urllib.request.urlopen(req)
data = json.loads(r.read())
print(f"诊断结果数: {data['results_count']}")
for res in data["results"]:
    print(f"  {res['match_score']}% - {res['disease_name']} ({res['severity']})")

print("\n✅ 所有测试通过！")
