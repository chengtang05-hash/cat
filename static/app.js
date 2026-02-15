/**
 * 猫咪健康诊断系统 - 前端交互逻辑
 */

// 状态管理
const state = {
    symptoms: [],        // 所有症状数据
    selected: new Set(), // 已选症状ID集合
    symptomNames: {},    // 症状ID到名称的映射
};

// === 初始化 ===
document.addEventListener('DOMContentLoaded', () => {
    loadSymptoms();
    loadBreeds();
    document.getElementById('symptom-search').addEventListener('input', filterSymptoms);
});

// 加载品种数据
async function loadBreeds() {
    try {
        const res = await fetch('/api/breeds');
        const breeds = await res.json();
        const select = document.getElementById('cat-breed');
        select.innerHTML = breeds.map(b =>
            `<option value="${b.id}">${b.name}</option>`
        ).join('');
        // 默认选中通用/普通猫 (假设它是列表第一个或特定ID，这里默认让后端顺序决定)
    } catch (err) {
        console.error('加载品种失败', err);
        document.getElementById('cat-breed').innerHTML = '<option value="">加载失败</option>';
    }
}

// 加载症状数据
async function loadSymptoms() {
    try {
        const res = await fetch('/api/symptoms');
        const data = await res.json();
        state.symptoms = data.categories;
        // 建立ID->名称映射
        data.categories.forEach(cat => {
            cat.symptoms.forEach(s => { state.symptomNames[s.id] = s.name; });
        });
        renderSymptoms();
    } catch (err) {
        document.getElementById('symptoms-container').innerHTML =
            '<div class="no-results"><div class="icon">😿</div><p>加载症状数据失败，请刷新重试</p></div>';
    }
}

// 渲染症状标签
function renderSymptoms() {
    const container = document.getElementById('symptoms-container');
    container.innerHTML = state.symptoms.map(cat => `
        <div class="symptom-category" data-category="${cat.id}">
            <div class="category-title">${cat.icon} ${cat.name}</div>
            <div class="symptom-tags">
                ${cat.symptoms.map(s => `
                    <span class="symptom-tag" data-id="${s.id}"
                          onclick="toggleSymptom('${s.id}', this)">${s.name}</span>
                `).join('')}
            </div>
        </div>
    `).join('');
}

// 切换症状选中状态
function toggleSymptom(id, el) {
    if (state.selected.has(id)) {
        state.selected.delete(id);
        el.classList.remove('selected');
    } else {
        state.selected.add(id);
        el.classList.add('selected');
    }
    updateSelectedUI();
}

// 更新选中状态UI
function updateSelectedUI() {
    const count = state.selected.size;
    const summary = document.getElementById('selected-summary');
    const countEl = document.getElementById('selected-count');
    const btn = document.getElementById('btn-diagnose');

    summary.style.display = count > 0 ? 'flex' : 'none';
    countEl.textContent = count;
    btn.disabled = count === 0;
}

// 清除所有选中
function clearSymptoms() {
    state.selected.clear();
    document.querySelectorAll('.symptom-tag.selected').forEach(el => el.classList.remove('selected'));
    updateSelectedUI();
}

// 搜索过滤症状
function filterSymptoms(e) {
    const query = e.target.value.trim().toLowerCase();
    document.querySelectorAll('.symptom-tag').forEach(tag => {
        const name = tag.textContent.toLowerCase();
        tag.classList.toggle('hidden', query && !name.includes(query));
    });
    // 隐藏空分类
    document.querySelectorAll('.symptom-category').forEach(cat => {
        const visible = cat.querySelectorAll('.symptom-tag:not(.hidden)').length;
        cat.style.display = visible > 0 ? '' : 'none';
    });
}

// === 诊断 ===
async function runDiagnosis() {
    if (state.selected.size === 0) return;

    const btn = document.getElementById('btn-diagnose');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;margin:0;border-width:2px;"></div> <span>正在分析...</span>';

    // 更新步骤指引
    setStep(2);

    try {
        const res = await fetch('/api/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symptoms: Array.from(state.selected),
                breed_id: document.getElementById('cat-breed').value || null,
                cat_age: document.getElementById('cat-age').value || null,
                cat_weight: parseFloat(document.getElementById('cat-weight').value) || null,
            }),
        });
        const data = await res.json();
        renderResults(data);
        setStep(3);

        // 滚动到结果
        document.getElementById('results-section').style.display = '';
        document.getElementById('symptoms-section').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
        alert('诊断请求失败，请稍后重试');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🩺</span><span>开始诊断</span>';
    }
}

// 返回症状选择
function backToSymptoms() {
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('symptoms-section').style.display = '';
    setStep(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 更新步骤状态
function setStep(active) {
    for (let i = 1; i <= 3; i++) {
        const el = document.getElementById(`step-${i}`);
        el.classList.remove('active', 'completed');
        if (i < active) el.classList.add('completed');
        if (i === active) el.classList.add('active');
    }
}

// === 结果渲染 ===
// === 结果渲染 ===
function renderResults(data) {
    const container = document.getElementById('results-container');

    if (!data.results || data.results.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <div class="icon">🤔</div>
                <p>未找到匹配的疾病</p>
                <p style="font-size:0.85rem;margin-top:8px;color:var(--text-muted);">
                    请尝试选择更多症状，或直接咨询兽医
                </p>
            </div>`;
        return;
    }

    container.innerHTML = data.results.map((r, i) => {
        const scoreClass = r.match_score >= 60 ? 'high' : r.match_score >= 35 ? 'medium' : 'low';
        const urgencyIcon = r.treatment.vet_urgency === '紧急' ? '🚨' :
            r.treatment.vet_urgency === '推荐' ? '🏥' : '💡';

        return `
        <div class="result-card" id="card-${i}">
            <div class="result-header" onclick="toggleCard(${i})">
                <div class="result-score ${scoreClass}">${r.match_score}%</div>
                <div class="result-info">
                    <div class="result-name">${r.disease_name}</div>
                    <div class="result-meta">
                        <span class="result-badge badge-severity-${r.severity}">${r.severity}</span>
                        <span style="color:var(--text-muted)">匹配 ${r.matched_symptoms.length} 个症状</span>
                    </div>
                </div>
                <span class="result-toggle">▼</span>
            </div>
            <div class="result-detail">
                <div class="detail-content">
                    <p style="font-size:0.88rem;color:var(--text-secondary);margin-top:14px;line-height:1.6;">
                        ${r.description}
                    </p>

                    <div class="detail-section">
                        <h4>✅ 匹配的症状</h4>
                        <div class="matched-symptoms">
                            ${r.matched_symptoms.map(s =>
            `<span class="matched-tag">${getName(s)}</span>`
        ).join('')}
                        </div>
                        ${r.unmatched_symptoms.length > 0 ? `
                        <h4 style="margin-top:10px;font-size:0.82rem;color:var(--text-muted);">
                            可能还会出现的症状
                        </h4>
                        <div class="matched-symptoms">
                            ${r.unmatched_symptoms.map(s =>
            `<span class="unmatched-tag">${getName(s)}</span>`
        ).join('')}
                        </div>` : ''}
                    </div>

                    ${r.breed_advice && r.breed_advice.length > 0 ? `
                    <div class="detail-section" style="background-color: #fff8e1; border-color: #ffe082;">
                        <h4 style="color: #f57f17;">🐱 品种专属建议</h4>
                        <ul style="margin: 0; padding-left: 20px; color: #5d4037;">
                            ${r.breed_advice.map(advice => `<li>${advice}</li>`).join('')}
                        </ul>
                    </div>` : ''}

                    <div class="detail-section">
                        <h4>💊 药物治疗</h4>
                        ${r.treatment.medications.map(m => `
                            <div class="med-card">
                                <div class="med-name">${m.name}</div>
                                <div class="med-dosage">📝 ${m.dosage}</div>
                                ${m.notes ? `<div class="med-notes">⚠️ ${m.notes}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>

                    <div class="detail-section">
                        <h4>🍽️ 饮食调养</h4>
                        <div class="diet-section">
                            <div class="diet-card recommended">
                                <h5>✅ 推荐食物</h5>
                                <ul>${(r.treatment.diet.recommended || []).map(f =>
            `<li>${f}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="diet-card forbidden">
                                <h5>❌ 禁忌食物</h5>
                                <ul>${(r.treatment.diet.forbidden || []).map(f =>
                `<li>${f}</li>`).join('') || '<li style="color:var(--text-muted)">无特殊禁忌</li>'}
                                </ul>
                            </div>
                        </div>
                        ${r.treatment.diet.tips ? `
                            <div class="diet-tips">${r.treatment.diet.tips}</div>
                        ` : ''}
                    </div>

                    <div class="detail-section">
                        <h4>🏠 日常护理</h4>
                        <div class="care-text">${r.treatment.care}</div>
                    </div>

                    <div class="vet-urgency vet-${r.treatment.vet_urgency}">
                        ${urgencyIcon} 就医建议：${r.treatment.vet_urgency}
                    </div>
                </div>
            </div>
        </div>`;
    }).join('');

    // 自动展开第一个结果
    if (data.results.length > 0) toggleCard(0);
}

// 获取症状名称
function getName(id) {
    return state.symptomNames[id] || id;
}

// 展开/收起卡片
function toggleCard(index) {
    const card = document.getElementById(`card - ${index}`);
    card.classList.toggle('expanded');
}
