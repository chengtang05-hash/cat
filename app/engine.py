"""
猫病诊断引擎模块。

基于加权匹配算法，将用户输入的症状与疾病知识库进行匹配，
返回按匹配度排序的诊断结果列表。
"""

import json
import pathlib
from dataclasses import dataclass, field


# 数据目录路径
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"


@dataclass
class DiagnosisResult:
    """单个诊断结果。"""
    disease_id: str
    disease_name: str
    category: str
    severity: str
    description: str
    match_score: float  # 匹配度百分比 0-100
    matched_symptoms: list[str] = field(default_factory=list)  # 匹配到的症状ID
    unmatched_symptoms: list[str] = field(default_factory=list)  # 疾病有但用户没报告的症状
    treatment: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典用于JSON序列化。"""
        return {
            "disease_id": self.disease_id,
            "disease_name": self.disease_name,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "match_score": round(self.match_score, 1),
            "matched_symptoms": self.matched_symptoms,
            "unmatched_symptoms": self.unmatched_symptoms,
            "treatment": self.treatment,
        }


class DiagnosisEngine:
    """
    猫病诊断引擎。

    使用加权Jaccard相似度算法，根据用户输入的症状
    从知识库中匹配可能的疾病并返回排序结果。
    """

    def __init__(self):
        """初始化引擎，加载知识库数据。"""
        self.diseases: list[dict] = []
        self.symptoms_map: dict[str, str] = {}  # id -> name 映射
        self._load_data()

    def _load_data(self):
        """从JSON文件加载疾病和症状数据。"""
        # 加载疾病数据
        diseases_file = DATA_DIR / "diseases.json"
        with open(diseases_file, "r", encoding="utf-8") as f:
            self.diseases = json.load(f)

        # 加载症状数据并建立映射
        symptoms_file = DATA_DIR / "symptoms.json"
        with open(symptoms_file, "r", encoding="utf-8") as f:
            symptoms_data = json.load(f)
            for category in symptoms_data["categories"]:
                for symptom in category["symptoms"]:
                    self.symptoms_map[symptom["id"]] = symptom["name"]

    def get_symptom_name(self, symptom_id: str) -> str:
        """获取症状的中文名称。"""
        return self.symptoms_map.get(symptom_id, symptom_id)

    def diagnose(
        self,
        symptoms: list[str],
        min_score: float = 15.0,
        max_results: int = 8,
    ) -> list[DiagnosisResult]:
        """
        根据输入症状进行诊断。

        Args:
            symptoms: 用户选择的症状ID列表
            min_score: 最低匹配度阈值（百分比）
            max_results: 最大返回结果数

        Returns:
            按匹配度降序排列的诊断结果列表
        """
        if not symptoms:
            return []

        results: list[DiagnosisResult] = []
        input_set = set(symptoms)

        for disease in self.diseases:
            disease_symptoms = disease.get("symptoms", {})
            if not disease_symptoms:
                continue

            # 计算加权匹配度
            score = self._calculate_match_score(input_set, disease_symptoms)

            if score >= min_score:
                # 找出匹配和未匹配的症状
                matched = [s for s in symptoms if s in disease_symptoms]
                unmatched = [s for s in disease_symptoms if s not in input_set]

                result = DiagnosisResult(
                    disease_id=disease["id"],
                    disease_name=disease["name"],
                    category=disease.get("category", ""),
                    severity=disease.get("severity", ""),
                    description=disease.get("description", ""),
                    match_score=score,
                    matched_symptoms=matched,
                    unmatched_symptoms=unmatched,
                    treatment=disease.get("treatment", {}),
                )
                results.append(result)

        # 按匹配度降序排序
        results.sort(key=lambda r: r.match_score, reverse=True)
        return results[:max_results]

    def _calculate_match_score(
        self, input_symptoms: set[str], disease_symptoms: dict[str, int]
    ) -> float:
        """
        计算加权匹配度。

        算法：
        1. 对用户输入的每个症状，如果疾病也有该症状，累加该症状的权重
        2. 将累加权重除以疾病所有症状的总权重，得到匹配百分比
        3. 额外奖励：匹配到高权重症状（≥8）时给予额外加分

        Args:
            input_symptoms: 用户输入的症状ID集合
            disease_symptoms: 疾病的症状字典 {symptom_id: weight}

        Returns:
            匹配度百分比 (0-100)
        """
        total_weight = sum(disease_symptoms.values())
        if total_weight == 0:
            return 0.0

        matched_weight = 0.0
        high_priority_bonus = 0.0

        for symptom_id, weight in disease_symptoms.items():
            if symptom_id in input_symptoms:
                matched_weight += weight
                # 匹配到高权重症状额外加分
                if weight >= 8:
                    high_priority_bonus += 2.0

        # 基础匹配度
        base_score = (matched_weight / total_weight) * 100

        # 加入高优先级奖励（上限10分）
        bonus = min(high_priority_bonus, 10.0)

        # 最终得分（不超过100）
        return min(base_score + bonus, 100.0)

    def get_all_symptoms(self) -> dict:
        """获取所有可用症状（按分类）。"""
        symptoms_file = DATA_DIR / "symptoms.json"
        with open(symptoms_file, "r", encoding="utf-8") as f:
            return json.load(f)
