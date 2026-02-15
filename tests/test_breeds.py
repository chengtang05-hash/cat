import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_breeds():
    """测试获取品种列表接口。"""
    response = client.get("/api/breeds")
    assert response.status_code == 200
    breeds = response.json()
    assert len(breeds) >= 20
    
    # 验证关键品种是否存在
    breed_ids = [b["id"] for b in breeds]
    assert "jianzhou" in breed_ids
    assert "scottish_fold" in breed_ids
    assert "british_shorthair" in breed_ids

def test_diagnose_jianzhou_obesity():
    """测试简州猫对肥胖症的匹配和建议。"""
    # 简州猫 + 肥胖相关症状
    payload = {
        "symptoms": ["weight_gain", "appetite_increase"],
        "breed_id": "jianzhou"
    }
    response = client.post("/api/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    results = data["results"]
    assert len(results) > 0
    
    # 预期第一名是肥胖症 (obesity), 因为简州猫对 obesity 有易感性 (+10分)
    top_result = results[0]
    assert top_result["disease_id"] == "obesity"
    
    # 验证有专门的品种建议
    assert "breed_advice" in top_result
    assert len(top_result["breed_advice"]) > 0
    # 简州猫的建议里应该有"体重管理"或"耳朵护理"
    advice_text = "".join(top_result["breed_advice"])
    assert "体重管理" in advice_text or "耳朵护理" in advice_text

def test_diagnose_fold_cat_score_boost():
    """测试折耳猫对软骨病的加分逻辑。"""
    symptoms = ["limping", "stiffness"]
    
    # 1. 普通猫诊断
    payload_normal = {
        "symptoms": symptoms,
        "breed_id": "general"  # 假设 general 没有这个 predisposition
    }
    res_normal = client.post("/api/diagnose", json=payload_normal)
    score_normal = 0
    for r in res_normal.json()["results"]:
        if r["disease_id"] == "osteochondrodysplasia":
            score_normal = r["match_score"]
            break
            
    # 2. 折耳猫诊断
    payload_fold = {
        "symptoms": symptoms,
        "breed_id": "scottish_fold" # 有 osteochondrodysplasia
    }
    res_fold = client.post("/api/diagnose", json=payload_fold)
    score_fold = 0
    for r in res_fold.json()["results"]:
        if r["disease_id"] == "osteochondrodysplasia":
            score_fold = r["match_score"]
            break

    # 折耳猫的分数应该比普通猫高 (因为有 +10 加分)
    # 注意：如果普通猫也匹配到了 osteochondrodysplasia，基础分应该是一样的，只是折耳猫有加分
    assert score_fold > score_normal
    print(f"Normal Score: {score_normal}, Fold Score: {score_fold}")
