/**
 * CareerCompass AI — Report Dashboard JavaScript
 * Renders the complete career analysis report from stored analysis data.
 * All Chart.js charts, dynamic content injection, PDF export.
 */

'use strict';

// ============================================================
// Global state
// ============================================================
let _analysis = null;
let _charts = {};

// ============================================================
// Utility helpers
// ============================================================

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmt$(n) {
  if (!n) return '$0';
  return '$' + Number(n).toLocaleString();
}

function difficultyClass(d) {
  const map = { 'Beginner': 'beginner', 'Intermediate': 'intermediate', 'Advanced': 'advanced' };
  return map[d] || 'beginner';
}

function phaseColor(i) {
  const colors = ['#0f62fe', '#24a148', '#f1620c', '#8a3ffc'];
  return colors[i] || colors[0];
}

function scrollToSection(id) {
  const el = document.getElementById('section-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  // Update sidebar active state
  document.querySelectorAll('.sidenav-link').forEach(l => l.classList.remove('active'));
  const matchingLink = document.querySelector(`.sidenav-link[onclick*="${id}"]`);
  if (matchingLink) matchingLink.classList.add('active');
}

// ============================================================
// Sidebar scroll spy
// ============================================================

function initScrollSpy() {
  const sections = document.querySelectorAll('.report-section[id]');
  const navLinks = document.querySelectorAll('.sidenav-link');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id.replace('section-', '');
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('onclick') && link.getAttribute('onclick').includes(id)) {
            link.classList.add('active');
          }
        });
      }
    });
  }, { rootMargin: '-60px 0px -60% 0px', threshold: 0 });

  sections.forEach(s => observer.observe(s));
}

// ============================================================
// Report header
// ============================================================

function renderHeader(analysis) {
  const cr = analysis.career_recommendation;
  const p = analysis.profile;

  document.getElementById('reportTitle').textContent =
    `${p.name}'s Career Report`;
  document.getElementById('reportMeta').textContent =
    `${p.branch} · ${p.college} · Generated ${new Date(analysis.generated_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`;
  document.getElementById('matchScoreDisplay').textContent = cr.match_score + '%';
  document.getElementById('motivationalMsg').textContent = analysis.motivational_message || '';
  document.getElementById('reportStudentName').textContent = `Hi, ${p.name.split(' ')[0]}`;

  // Summary cards
  const summaryGrid = document.getElementById('summaryGrid');
  summaryGrid.innerHTML = `
    <div class="summary-card">
      <div class="summary-value" style="color:var(--color-ibm-blue);">${cr.match_score}%</div>
      <div class="summary-label">Career Match</div>
    </div>
    <div class="summary-card">
      <div class="summary-value" style="color:var(--color-success);">${cr.confidence_score}%</div>
      <div class="summary-label">AI Confidence</div>
    </div>
    <div class="summary-card">
      <div class="summary-value">${fmt$(cr.avg_salary_entry)}</div>
      <div class="summary-label">Entry Salary</div>
    </div>
    <div class="summary-card">
      <div class="summary-value" style="color:var(--color-success);">+${cr.job_growth_percent}%</div>
      <div class="summary-label">Job Growth Rate</div>
    </div>
  `;
}

// ============================================================
// Career Recommendation section
// ============================================================

function renderCareerRecommendation(cr) {
  document.getElementById('primaryCareerTitle').textContent = cr.primary_career;
  document.getElementById('whyThisCareer').textContent = cr.why_this_career || '';
  document.getElementById('careerCategoryBadge').textContent = cr.career_category;
  document.getElementById('matchScoreCircle').textContent = cr.match_score + '%';
  document.getElementById('confScore').textContent = cr.confidence_score + '%';
  document.getElementById('confBar').style.width = cr.confidence_score + '%';
  document.getElementById('confExplanation').textContent = cr.confidence_explanation || '';

  // Meta grid
  const metaGrid = document.getElementById('careerMetaGrid');
  const metaItems = [
    { label: 'Market Demand', value: cr.market_demand, color: cr.market_demand === 'High' ? 'var(--color-success)' : 'var(--color-warning)' },
    { label: 'Job Growth', value: '+' + cr.job_growth_percent + '%', color: 'var(--color-success)' },
    { label: 'Senior Salary', value: fmt$(cr.avg_salary_senior), color: 'var(--color-ibm-blue)' },
  ];
  metaGrid.innerHTML = metaItems.map(m => `
    <div style="padding:.875rem;background:var(--color-surface-alt);border-radius:var(--radius-lg);border:1px solid var(--color-border);">
      <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.25rem;">${esc(m.label)}</div>
      <div style="font-size:1.375rem;font-weight:700;color:${m.color};">${esc(m.value)}</div>
    </div>
  `).join('');
}

// ============================================================
// Skill Analysis section
// ============================================================

function renderSkillAnalysis(sa) {
  const container = document.getElementById('skillsContent');

  const renderSkillGroup = (title, skills, tagClass, emptyMsg) => {
    if (!skills || skills.length === 0) return '';
    return `
      <div style="margin-bottom:1.25rem;">
        <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.625rem;">${esc(title)}</p>
        <div class="skill-tags">
          ${skills.map(s => `<span class="tag ${tagClass}">${esc(s)}</span>`).join('')}
        </div>
      </div>
    `;
  };

  container.innerHTML = `
    ${renderSkillGroup('Existing Skills', sa.existing_skills, 'tag-success', 'None identified')}
    ${renderSkillGroup('Required Skills', sa.required_skills, '', 'None identified')}
    ${renderSkillGroup('Skill Gaps', sa.skill_gap, 'tag-gap', 'No significant gaps')}
    ${Object.keys(sa.skill_gap_reasons || {}).length > 0 ? `
      <div style="margin-top:1.25rem;">
        <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.75rem;">Why These Skills Are Needed</p>
        <div style="display:flex;flex-direction:column;gap:.5rem;">
          ${Object.entries(sa.skill_gap_reasons).slice(0, 6).map(([skill, reason]) => `
            <div style="display:flex;gap:.75rem;padding:.625rem;background:var(--color-surface-alt);border-radius:var(--radius-md);border-left:3px solid var(--color-error);">
              <span style="font-size:var(--text-sm);font-weight:600;color:var(--color-error);white-space:nowrap;">${esc(skill)}</span>
              <span style="font-size:var(--text-sm);color:var(--color-text-secondary);">${esc(reason)}</span>
            </div>
          `).join('')}
        </div>
      </div>
    ` : ''}
  `;
}

// ============================================================
// Radar Chart
// ============================================================

function renderRadarChart(sa) {
  const ctx = document.getElementById('radarChart');
  if (!ctx || !sa.radar_scores) return;

  const labels = ['Technical Skills', 'Problem Solving', 'Communication', 'Industry Knowledge', 'Project Experience', 'Soft Skills'];
  const data = [
    sa.radar_scores.technical_skills || 50,
    sa.radar_scores.problem_solving || 50,
    sa.radar_scores.communication || 50,
    sa.radar_scores.industry_knowledge || 40,
    sa.radar_scores.project_experience || 35,
    sa.radar_scores.soft_skills || 55,
  ];

  if (_charts.radar) _charts.radar.destroy();
  _charts.radar = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: 'Your Profile',
        data,
        backgroundColor: 'rgba(15, 98, 254, 0.12)',
        borderColor: '#0f62fe',
        borderWidth: 2,
        pointBackgroundColor: '#0f62fe',
        pointRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: { stepSize: 20, font: { size: 10 }, color: '#8d8d8d' },
          grid: { color: 'rgba(0,0,0,0.06)' },
          angleLines: { color: 'rgba(0,0,0,0.08)' },
          pointLabels: { font: { size: 11 }, color: '#525252' },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.raw}%`,
          },
        },
      },
    },
  });
}

// ============================================================
// Salary Chart
// ============================================================

function renderSalaryChartAndCards(cr) {
  // Cards
  const salaryCards = document.getElementById('salaryCards');
  const stages = [
    { label: 'Entry Level', value: cr.avg_salary_entry, years: '0–2 yrs', color: '#8d8d8d' },
    { label: 'Mid-Level', value: cr.avg_salary_mid, years: '3–5 yrs', color: '#0f62fe' },
    { label: 'Senior Level', value: cr.avg_salary_senior, years: '5–8 yrs', color: '#24a148' },
    { label: 'Lead / Principal', value: cr.avg_salary_lead, years: '8+ yrs', color: '#8a3ffc' },
  ];

  salaryCards.innerHTML = stages.map((s, i) => `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:.875rem 0;border-bottom:1px solid var(--color-border-subtle);">
      <div style="display:flex;align-items:center;gap:.75rem;">
        <div style="width:10px;height:10px;border-radius:50%;background:${s.color};flex-shrink:0;"></div>
        <div>
          <div style="font-size:var(--text-sm);font-weight:600;">${esc(s.label)}</div>
          <div style="font-size:var(--text-xs);color:var(--color-text-muted);">${s.years}</div>
        </div>
      </div>
      <div style="font-size:1.1rem;font-weight:700;color:${s.color};">${fmt$(s.value)}</div>
    </div>
  `).join('');

  // Chart
  const ctx = document.getElementById('salaryChart');
  if (!ctx) return;

  if (_charts.salary) _charts.salary.destroy();
  _charts.salary = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Entry', 'Mid-Level', 'Senior', 'Lead'],
      datasets: [{
        label: 'Annual Salary (USD)',
        data: [cr.avg_salary_entry, cr.avg_salary_mid, cr.avg_salary_senior, cr.avg_salary_lead],
        backgroundColor: ['rgba(141,141,141,0.2)', 'rgba(15,98,254,0.2)', 'rgba(36,161,72,0.2)', 'rgba(138,63,252,0.2)'],
        borderColor: ['#8d8d8d', '#0f62fe', '#24a148', '#8a3ffc'],
        borderWidth: 2,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => `${fmt$(ctx.raw)}/yr` },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: v => '$' + (v / 1000).toFixed(0) + 'k',
            font: { size: 11 },
            color: '#525252',
          },
          grid: { color: 'rgba(0,0,0,0.05)' },
        },
        x: {
          ticks: { font: { size: 11 }, color: '#525252' },
          grid: { display: false },
        },
      },
    },
  });
}

// ============================================================
// Skill Gap + Demand Charts
// ============================================================

function renderAuxCharts(sa, cr) {
  // Skill gap chart
  const gapCtx = document.getElementById('skillGapChart');
  if (gapCtx && sa.existing_skills && sa.skill_gap) {
    const existing = sa.existing_skills.slice(0, 6);
    const gaps = sa.skill_gap.slice(0, 4);
    const labels = [...existing, ...gaps];
    const data = [
      ...existing.map(() => 100),
      ...gaps.map(() => 15),
    ];
    const colors = [
      ...existing.map(() => 'rgba(36,161,72,0.7)'),
      ...gaps.map(() => 'rgba(218,30,40,0.7)'),
    ];

    if (_charts.skillGap) _charts.skillGap.destroy();
    _charts.skillGap = new Chart(gapCtx, {
      type: 'bar',
      data: {
        labels: labels.map(l => l.length > 12 ? l.slice(0, 12) + '…' : l),
        datasets: [{
          data,
          backgroundColor: colors,
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => ctx.raw === 100 ? 'You have this skill' : 'Skill gap — needs attention',
            },
          },
        },
        scales: {
          x: { max: 100, ticks: { display: false }, grid: { display: false }, border: { display: false } },
          y: { ticks: { font: { size: 10 }, color: '#525252' }, grid: { display: false } },
        },
      },
    });
  }

  // Job demand chart (simulated trend)
  const demandCtx = document.getElementById('demandChart');
  if (demandCtx) {
    const baseGrowth = cr.job_growth_percent || 15;
    const years = ['2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027'];
    const demandData = years.map((_, i) => {
      const base = 60 + i * (baseGrowth / 3);
      return Math.min(99, base + (Math.random() * 4 - 2));
    });

    if (_charts.demand) _charts.demand.destroy();
    _charts.demand = new Chart(demandCtx, {
      type: 'line',
      data: {
        labels: years,
        datasets: [{
          label: 'Job Demand Index',
          data: demandData.map(d => Math.round(d)),
          borderColor: '#0f62fe',
          backgroundColor: 'rgba(15,98,254,0.08)',
          borderWidth: 2.5,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#0f62fe',
          pointRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => `Demand Index: ${ctx.raw}` } },
        },
        scales: {
          y: {
            beginAtZero: false,
            min: 40,
            max: 100,
            ticks: { font: { size: 10 }, color: '#525252' },
            grid: { color: 'rgba(0,0,0,0.05)' },
          },
          x: {
            ticks: { font: { size: 10 }, color: '#525252' },
            grid: { display: false },
          },
        },
      },
    });
  }
}

// ============================================================
// Career Timeline
// ============================================================

function renderCareerTimeline(timeline) {
  const container = document.getElementById('timelineContent');
  if (!timeline || timeline.length === 0) {
    container.innerHTML = '<p class="text-muted">Timeline data not available.</p>';
    return;
  }

  container.innerHTML = timeline.map((stage, i) => `
    <div class="timeline-stage">
      <div class="timeline-year">
        <div class="timeline-year-num">Y${stage.years_from_now}</div>
        <div class="timeline-year-label">Year ${stage.years_from_now}</div>
      </div>
      <div style="flex:1;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;margin-bottom:.5rem;">
          <h4 style="font-size:var(--text-base);font-weight:600;">${esc(stage.stage)}</h4>
          <span style="font-size:var(--text-base);font-weight:700;color:var(--color-success);">${fmt$(stage.expected_salary)}/yr</span>
        </div>
        <p style="font-size:var(--text-sm);color:var(--color-text-secondary);line-height:1.5;margin-bottom:.625rem;">${esc(stage.description)}</p>
        ${stage.key_skills_needed && stage.key_skills_needed.length > 0 ? `
          <div class="skill-tags">
            ${stage.key_skills_needed.map(s => `<span class="tag">${esc(s)}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

// ============================================================
// 24-Month Roadmap
// ============================================================

function renderDetailList(items, color, bullet = '▸') {
  if (!items || items.length === 0) return '';
  return `
    <div class="phase-detail-list">
      ${items.map(item => `
        <div class="phase-detail-item">
          <span class="phase-detail-bullet" style="color:${color};">${bullet}</span>
          <span>${esc(item)}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function renderRoadmap(roadmap) {
  const container = document.getElementById('roadmapContent');
  const phases = ['phase_1', 'phase_2', 'phase_3', 'phase_4'];
  const levelClass = ['beginner', 'intermediate', 'advanced', 'expert'];

  container.innerHTML = phases.map((key, i) => {
    const phase = roadmap[key];
    if (!phase) return '';
    const color = phaseColor(i);
    const lvlClass = levelClass[i];

    const hasTopics      = phase.topics && phase.topics.length > 0;
    const hasSubtopics   = phase.subtopics && phase.subtopics.length > 0;
    const hasExercises   = phase.practical_exercises && phase.practical_exercises.length > 0;
    const hasMiniProjects= phase.mini_projects && phase.mini_projects.length > 0;
    const hasGoals       = phase.goals && phase.goals.length > 0;
    const hasResources   = phase.key_resources && phase.key_resources.length > 0;

    return `
      <div class="roadmap-phase">
        <div class="phase-marker" style="background:${color};">${i + 1}</div>
        <div class="phase-header">
          <div style="display:flex;align-items:center;gap:.625rem;flex-wrap:wrap;">
            <h3 class="phase-title">${esc(phase.title)}</h3>
            <span class="phase-level-badge phase-level-${lvlClass}">${esc(phase.level || lvlClass)}</span>
          </div>
          <span class="phase-duration">${esc(phase.duration)}</span>
        </div>
        <div class="phase-content">
          <!-- Meta row -->
          <div class="phase-meta">
            <div class="phase-meta-item">
              <div class="meta-label">Weekly Focus</div>
              <div class="meta-value">${esc(phase.weekly_focus)}</div>
            </div>
            <div class="phase-meta-item">
              <div class="meta-label">Milestone</div>
              <div class="meta-value">${esc(phase.monthly_milestone)}</div>
            </div>
            <div class="phase-meta-item">
              <div class="meta-label">Study Hours / Week</div>
              <div class="meta-value" style="color:${color};font-size:1.1rem;font-weight:700;">${phase.study_hours_per_week}h</div>
            </div>
          </div>

          <!-- Goals -->
          ${hasGoals ? `
            <div style="margin-bottom:.875rem;">
              <p style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--color-text-muted);margin-bottom:.5rem;">Goals</p>
              ${renderDetailList(phase.goals, color)}
            </div>
          ` : ''}

          <!-- Topics + Subtopics (2-col grid) -->
          ${(hasTopics || hasSubtopics) ? `
            <div class="phase-detail-grid">
              ${hasTopics ? `
                <div class="phase-detail-block">
                  <div class="phase-detail-block-title">
                    <svg width="11" height="11" viewBox="0 0 16 16" fill="${color}"><circle cx="8" cy="8" r="8"/></svg>
                    Topics to Study
                  </div>
                  ${renderDetailList(phase.topics, color, '▸')}
                </div>
              ` : ''}
              ${hasSubtopics ? `
                <div class="phase-detail-block">
                  <div class="phase-detail-block-title">
                    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="${color}" stroke-width="2"><rect x="2" y="2" width="12" height="12" rx="2"/></svg>
                    Subtopics &amp; Concepts
                  </div>
                  ${renderDetailList(phase.subtopics, color, '◦')}
                </div>
              ` : ''}
            </div>
          ` : ''}

          <!-- Exercises + Mini Projects (2-col grid) -->
          ${(hasExercises || hasMiniProjects) ? `
            <div class="phase-detail-grid">
              ${hasExercises ? `
                <div class="phase-detail-block">
                  <div class="phase-detail-block-title">
                    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="${color}" stroke-width="2"><polyline points="4 8 6 10 12 4"/><rect x="1" y="1" width="14" height="14" rx="2"/></svg>
                    Practical Exercises
                  </div>
                  ${renderDetailList(phase.practical_exercises, color, '•')}
                </div>
              ` : ''}
              ${hasMiniProjects ? `
                <div class="phase-detail-block">
                  <div class="phase-detail-block-title">
                    <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="${color}" stroke-width="2"><polygon points="8 1 10 6 15 6 11 9 13 14 8 11 3 14 5 9 1 6 6 6"/></svg>
                    Mini Projects
                  </div>
                  ${renderDetailList(phase.mini_projects, color, '•')}
                </div>
              ` : ''}
            </div>
          ` : ''}

          <!-- Expected outcome -->
          ${phase.expected_outcome ? `
            <div class="phase-outcome-box">
              <div class="phase-outcome-label">Expected Outcome</div>
              ${esc(phase.expected_outcome)}
            </div>
          ` : ''}

          <!-- Key Resources -->
          ${hasResources ? `
            <div style="margin-top:.875rem;">
              <p style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;color:var(--color-text-muted);margin-bottom:.5rem;">Key Resources</p>
              <div class="skill-tags">
                ${phase.key_resources.map(r => `<span class="tag">${esc(r)}</span>`).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

// ============================================================
// Projects
// ============================================================

let _allProjects = [];

function renderProjects(projects) {
  _allProjects = [];
  ['beginner', 'intermediate', 'advanced'].forEach(level => {
    (projects[level] || []).forEach(p => {
      _allProjects.push({ ...p, level });
    });
  });
  renderProjectCards('all');
}

function filterProjects(filter) {
  // Update tab styles
  ['all', 'beginner', 'intermediate', 'advanced'].forEach(f => {
    const tab = document.getElementById('tab-' + f);
    if (tab) {
      tab.className = f === filter
        ? 'btn btn-sm btn-secondary active-tab'
        : 'btn btn-sm btn-ghost';
    }
  });
  renderProjectCards(filter);
}

function renderProjectCards(filter) {
  const container = document.getElementById('projectsContent');
  const filtered = filter === 'all' ? _allProjects : _allProjects.filter(p => p.level === filter);

  if (filtered.length === 0) {
    container.innerHTML = '<p class="text-muted" style="padding:1rem;">No projects found.</p>';
    return;
  }

  // Group by level for display
  const groups = filter === 'all'
    ? ['beginner', 'intermediate', 'advanced']
    : [filter];

  container.innerHTML = groups.map(level => {
    const levelProjects = filtered.filter(p => p.level === level);
    if (levelProjects.length === 0) return '';
    const levelLabels = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' };

    return `
      <div style="margin-bottom:2rem;">
        <h4 style="font-size:var(--text-base);font-weight:700;color:var(--color-text-primary);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem;">
          <span class="difficulty-badge difficulty-${level}">${levelLabels[level]}</span>
          Projects
        </h4>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem;">
          ${levelProjects.map(p => renderProjectCard(p)).join('')}
        </div>
      </div>
    `;
  }).join('');
}

function renderProjectCard(p) {
  return `
    <div class="project-card">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:.5rem;margin-bottom:.75rem;">
        <h5 style="font-size:var(--text-base);font-weight:600;color:var(--color-text-primary);line-height:1.3;">${esc(p.title)}</h5>
        <span class="difficulty-badge difficulty-${p.level}" style="flex-shrink:0;">${esc(p.difficulty)}</span>
      </div>
      <p style="font-size:var(--text-sm);color:var(--color-text-secondary);line-height:1.5;margin-bottom:.875rem;">${esc(p.description)}</p>
      <div style="margin-bottom:.625rem;">
        <span style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--color-text-muted);">Technologies</span>
        <div class="skill-tags" style="margin-top:.375rem;">
          ${(p.technologies || []).map(t => `<span class="tag">${esc(t)}</span>`).join('')}
        </div>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:.75rem;padding-top:.625rem;border-top:1px solid var(--color-border-subtle);">
        <span style="font-size:var(--text-xs);color:var(--color-text-muted);">⏱ ${esc(p.estimated_time)}</span>
        <span style="font-size:var(--text-xs);font-weight:600;color:var(--color-ibm-blue);" title="${esc(p.expected_outcome)}">View Outcome →</span>
      </div>
    </div>
  `;
}

// ============================================================
// Certifications
// ============================================================

function certLevelClass(level) {
  const map = { 'Beginner': 'cert-level-beginner', 'Intermediate': 'cert-level-intermediate', 'Advanced': 'cert-level-advanced', 'Expert': 'cert-level-expert' };
  return map[level] || 'cert-level-intermediate';
}

function certDiffClass(diff) {
  const map = { 'Easy': 'cert-difficulty-easy', 'Medium': 'cert-difficulty-medium', 'Hard': 'cert-difficulty-hard' };
  return map[diff] || 'cert-difficulty-medium';
}

function renderCertifications(certs) {
  const container = document.getElementById('certsContent');
  if (!certs || certs.length === 0) {
    container.innerHTML = '<p class="text-muted">No certification recommendations available.</p>';
    return;
  }

  container.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:1.25rem;">
      ${certs.map(c => `
        <div class="cert-card" style="flex-direction:column;gap:.75rem;">
          <!-- Header row -->
          <div style="display:flex;align-items:flex-start;gap:.875rem;">
            <div class="cert-badge">${esc((c.provider || '').slice(0,5))}</div>
            <div style="flex:1;min-width:0;">
              <a href="${c.url || 'https://www.google.com/search?q=' + encodeURIComponent(c.name + ' certification ' + c.provider)}" target="_blank" style="font-size:var(--text-sm);font-weight:700;color:var(--color-ibm-blue);line-height:1.3;margin-bottom:.3rem;text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
                ${esc(c.name)}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
              <div style="font-size:var(--text-xs);color:var(--color-text-muted);">${esc(c.provider)}</div>
            </div>
          </div>
          <!-- Badges row -->
          <div style="display:flex;flex-wrap:wrap;gap:.375rem;align-items:center;">
            <span class="badge ${certLevelClass(c.level)}" style="font-size:.65rem;">${esc(c.level)}</span>
            ${c.difficulty ? `<span class="badge ${certDiffClass(c.difficulty)}" style="font-size:.65rem;">${esc(c.difficulty)}</span>` : ''}
            <span class="badge badge-gray" style="font-size:.65rem;">⏱ ${esc(c.duration)}</span>
            <span class="badge badge-gray" style="font-size:.65rem;">${esc(c.cost)}</span>
          </div>
          <!-- Why important -->
          <div class="why-box">${esc(c.why_important)}</div>
          <!-- Skills gained -->
          ${c.skills_gained && c.skills_gained.length > 0 ? `
            <div>
              <p style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.375rem;">Skills Gained</p>
              <div class="cert-skills-list">
                ${c.skills_gained.map(s => `<span class="cert-skill-chip">${esc(s)}</span>`).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      `).join('')}
    </div>
  `;
}

// ============================================================
// Learning Resources
// ============================================================

function renderLearningResources(lr) {
  const container = document.getElementById('resourcesContent');

  const booksHtml = lr.books && lr.books.length > 0 ? `
    <div style="margin-bottom:2rem;">
      <h4 style="font-size:var(--text-base);font-weight:600;color:var(--color-text-primary);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem;">
        Books
      </h4>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.875rem;">
        ${lr.books.map(b => `
          <div style="padding:.875rem;border:1px solid var(--color-border);border-radius:var(--radius-lg);background:var(--color-bg);">
            <a href="${b.url || 'https://www.google.com/search?q=' + encodeURIComponent(b.title + ' book ' + b.author)}" target="_blank" style="font-size:var(--text-sm);font-weight:600;margin-bottom:.25rem;color:var(--color-ibm-blue);text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
              ${esc(b.title)}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
            <div style="font-size:var(--text-xs);color:var(--color-text-muted);margin-bottom:.5rem;">by ${esc(b.author)}</div>
            <div style="display:flex;justify-content:space-between;align-items:flex-end;">
              <p style="font-size:var(--text-xs);color:var(--color-text-secondary);flex:1;">${esc(b.why_read)}</p>
              <span class="badge badge-gray" style="margin-left:.5rem;flex-shrink:0;">${esc(b.difficulty)}</span>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  const ytHtml = lr.youtube_channels && lr.youtube_channels.length > 0 ? `
    <div style="margin-bottom:2rem;">
      <h4 style="font-size:var(--text-base);font-weight:600;color:var(--color-text-primary);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem;">
        YouTube Channels
      </h4>
      <div style="display:flex;flex-direction:column;gap:.625rem;">
        ${lr.youtube_channels.map(y => `
          <div style="display:flex;align-items:flex-start;gap:.75rem;padding:.75rem;border:1px solid var(--color-border);border-radius:var(--radius-md);background:var(--color-bg);">
            <div style="width:36px;height:36px;background:#ff0000;border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="white"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </div>
            <div style="flex:1;">
              <a href="${y.url || 'https://www.youtube.com/results?search_query=' + encodeURIComponent(y.channel_name)}" target="_blank" style="font-size:var(--text-sm);font-weight:600;color:var(--color-ibm-blue);text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
                ${esc(y.channel_name)}
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
              <div style="font-size:var(--text-xs);color:var(--color-text-muted);">${esc(y.focus_area)}</div>
              <div style="font-size:var(--text-xs);color:var(--color-text-secondary);margin-top:.25rem;">${esc(y.why_watch)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  const coursesHtml = lr.online_courses && lr.online_courses.length > 0 ? `
    <div>
      <h4 style="font-size:var(--text-base);font-weight:600;color:var(--color-text-primary);margin-bottom:1rem;display:flex;align-items:center;gap:.5rem;">
        Online Courses
      </h4>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.875rem;">
        ${lr.online_courses.map(c => `
          <div style="padding:.875rem;border:1px solid var(--color-border);border-radius:var(--radius-lg);background:var(--color-bg);">
            <a href="${c.url || 'https://www.google.com/search?q=' + encodeURIComponent(c.title + ' course ' + c.platform)}" target="_blank" style="font-size:var(--text-sm);font-weight:600;margin-bottom:.25rem;color:var(--color-ibm-blue);text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
              ${esc(c.title)}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
            <div style="font-size:var(--text-xs);color:var(--color-text-muted);margin-bottom:.375rem;">${esc(c.platform)} · ${esc(c.instructor)} · ${esc(c.duration)}</div>
            <p style="font-size:var(--text-xs);color:var(--color-text-secondary);">${esc(c.why_take)}</p>
          </div>
        `).join('')}
      </div>
    </div>
  ` : '';

  container.innerHTML = booksHtml + ytHtml + coursesHtml || '<p class="text-muted">No resources available.</p>';
}

// ============================================================
// Action Plan
// ============================================================

function renderActionPlan(ap) {
  const container = document.getElementById('actionContent');

  const renderBucket = (key, label, colorClass) => {
    const items = ap[key] || [];
    if (items.length === 0) return '';
    return `
      <div style="margin-bottom:1.75rem;">
        <h4 style="font-size:var(--text-base);font-weight:600;color:var(--color-text-primary);margin-bottom:1rem;">${esc(label)}</h4>
        ${items.map(item => `
          <div class="action-item ${colorClass}">
            <div style="flex:1;">
              <div style="font-size:var(--text-sm);font-weight:600;color:var(--color-text-primary);margin-bottom:.25rem;">→ ${esc(item.action)}</div>
              <div style="font-size:var(--text-xs);color:var(--color-text-secondary);line-height:1.5;">${esc(item.reason)}</div>
            </div>
            <div style="flex-shrink:0;min-width:80px;text-align:right;">
              <span class="badge badge-gray" style="font-size:.65rem;">${esc(item.time_to_complete)}</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  };
  container.innerHTML = `
    ${renderBucket('immediate_actions', 'Immediate Actions (This Week)', 'immediate')}
    ${renderBucket('short_term', 'Short-Term Goals (1–3 Months)', 'short')}
    ${renderBucket('long_term', 'Long-Term Goals (3–12 Months)', 'long')}
  `;
}

// ============================================================
// Internship Strategy
// ============================================================

function renderInternshipStrategy(ist) {
  const container = document.getElementById('internshipContent');
  const readinessColors = {
    'Not Ready': 'var(--color-error)',
    'Getting Ready': 'var(--color-warning)',
    'Ready': 'var(--color-success)',
    'Highly Ready': 'var(--color-ibm-blue)',
  };
  const color = readinessColors[ist.readiness_level] || 'var(--color-warning)';

  container.innerHTML = `
    <div style="display:grid;grid-template-columns:auto 1fr;gap:1.5rem;align-items:start;margin-bottom:1.5rem;">
      <div style="padding:.875rem 1.25rem;background:var(--color-surface-alt);border-radius:var(--radius-lg);border:2px solid ${color};text-align:center;">
        <div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--color-text-muted);margin-bottom:.25rem;">Readiness</div>
        <div style="font-size:var(--text-sm);font-weight:700;color:${color};">${esc(ist.readiness_level)}</div>
      </div>
      <p style="font-size:var(--text-sm);color:var(--color-text-secondary);line-height:1.6;">${esc(ist.readiness_reason)}</p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;">
      ${ist.target_companies && ist.target_companies.length > 0 ? `
        <div>
          <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.625rem;">Target Companies</p>
          <div class="skill-tags">
            ${ist.target_companies.map(c => `<span class="badge badge-blue">${esc(c)}</span>`).join('')}
          </div>
        </div>
      ` : ''}
      ${ist.best_platforms && ist.best_platforms.length > 0 ? `
        <div>
          <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.625rem;">Best Platforms</p>
          <div class="skill-tags">
            ${ist.best_platforms.map(p => `<span class="badge badge-gray">${esc(p)}</span>`).join('')}
          </div>
        </div>
      ` : ''}
    </div>

    ${ist.preparation_steps && ist.preparation_steps.length > 0 ? `
      <div style="margin-top:1.25rem;">
        <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.625rem;">Preparation Steps</p>
        <div style="display:flex;flex-direction:column;gap:.375rem;">
          ${ist.preparation_steps.map((s, i) => `
            <div style="display:flex;align-items:flex-start;gap:.75rem;font-size:var(--text-sm);color:var(--color-text-secondary);">
              <span style="min-width:22px;height:22px;background:var(--color-ibm-blue);color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;">${i+1}</span>
              ${esc(s)}
            </div>
          `).join('')}
        </div>
      </div>
    ` : ''}

    ${ist.application_tips ? `
      <div style="margin-top:1.25rem;padding:1rem;background:var(--color-ibm-blue-light);border-radius:var(--radius-md);border:1px solid var(--color-ibm-blue-mid);">
        <p style="font-size:var(--text-xs);font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-ibm-blue);margin-bottom:.375rem;">Application Tips</p>
        <p style="font-size:var(--text-sm);color:var(--color-text-primary);line-height:1.55;">${esc(ist.application_tips)}</p>
      </div>
    ` : ''}
  `;
}

// ============================================================
// Interview Preparation
// ============================================================

function renderInterviewPrep(ip) {
  const container = document.getElementById('interviewContent');

  const renderList = (title, items) => {
    if (!items || items.length === 0) return '';
    return `
      <div style="margin-bottom:1.5rem;">
        <h4 style="font-size:var(--text-sm);font-weight:600;color:var(--color-text-primary);margin-bottom:.75rem;">${esc(title)}</h4>
        <div style="display:flex;flex-direction:column;gap:.375rem;">
          ${items.map(item => `
            <div style="display:flex;align-items:flex-start;gap:.5rem;font-size:var(--text-sm);color:var(--color-text-secondary);padding:.5rem .625rem;border-radius:var(--radius-sm);background:var(--color-surface-alt);">
              <span style="color:var(--color-ibm-blue);flex-shrink:0;">•</span>
              ${esc(item)}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  };

  container.innerHTML = `
    ${ip.tips ? `<div style="padding:1rem 1.25rem;background:var(--color-success-light);border-radius:var(--radius-lg);border:1px solid rgba(36,161,72,.2);margin-bottom:1.5rem;font-size:var(--text-sm);color:var(--color-text-primary);line-height:1.6;">${esc(ip.tips)}</div>` : ''}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;">
      <div>
        ${renderList('Focus Areas', ip.focus_areas)}
        ${renderList('Technical Topics', ip.technical_topics)}
      </div>
      <div>
        ${renderList('Common Questions', ip.common_questions)}
        ${renderList('Resources', ip.preparation_resources)}
      </div>
    </div>
  `;
}

// ============================================================
// Profile Building
// ============================================================

function renderProfileBuilding(pb) {
  const container = document.getElementById('profileBuildingContent');

  const renderTips = (title, tips) => {
    if (!tips || tips.length === 0) return '';
    return `
      <div style="padding:1.25rem;border:1px solid var(--color-border);border-radius:var(--radius-lg);background:var(--color-bg);">
        <h4 style="font-size:var(--text-sm);font-weight:600;color:var(--color-text-primary);margin-bottom:.875rem;">${esc(title)}</h4>
        <ul style="display:flex;flex-direction:column;gap:.5rem;">
          ${tips.map(t => `
            <li style="display:flex;align-items:flex-start;gap:.5rem;font-size:var(--text-sm);color:var(--color-text-secondary);">
              <span style="color:var(--color-ibm-blue);flex-shrink:0;margin-top:2px;">•</span>
              ${esc(t)}
            </li>
          `).join('')}
        </ul>
      </div>
    `;
  };

  container.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
      ${renderTips('Resume', pb.resume_tips)}
      ${renderTips('LinkedIn Profile', pb.linkedin_tips)}
      ${renderTips('GitHub Profile', pb.github_tips)}
      ${renderTips('Portfolio', pb.portfolio_tips)}
    </div>
  `;
}

// ============================================================
// Related Careers
// ============================================================

// Platform icon color map
const PLATFORM_COLORS = {
  'coursera':           { bg: '#0056D2', text: 'white', abbr: 'CRS' },
  'ibm skillsbuild':    { bg: '#0f62fe', text: 'white', abbr: 'IBM' },
  'ibm':                { bg: '#0f62fe', text: 'white', abbr: 'IBM' },
  'microsoft learn':    { bg: '#00a4ef', text: 'white', abbr: 'MS' },
  'freecodecamp':       { bg: '#0a0a23', text: 'white', abbr: 'FCC' },
  'freeCodeCamp':       { bg: '#0a0a23', text: 'white', abbr: 'FCC' },
  'aws skill builder':  { bg: '#ff9900', text: '#111', abbr: 'AWS' },
  'google cloud skills boost': { bg: '#4285F4', text: 'white', abbr: 'GCP' },
  'cisco skills for all': { bg: '#1ba0d7', text: 'white', abbr: 'CSC' },
  'edx':                { bg: '#02262b', text: 'white', abbr: 'edX' },
  'udemy':              { bg: '#a435f0', text: 'white', abbr: 'UDM' },
  'pluralsight':        { bg: '#f15b2a', text: 'white', abbr: 'PST' },
  'tryhackme':          { bg: '#212c42', text: 'white', abbr: 'THM' },
  'hackthebox':         { bg: '#9fef00', text: '#111', abbr: 'HTB' },
  'linkedin learning':  { bg: '#0a66c2', text: 'white', abbr: 'LIN' },
  'youtube':            { bg: '#ff0000', text: 'white', abbr: 'YT' },
};

function getPlatformStyle(name) {
  const key = (name || '').toLowerCase();
  for (const [k, v] of Object.entries(PLATFORM_COLORS)) {
    if (key.includes(k)) return v;
  }
  return { bg: '#525252', text: 'white', abbr: (name || 'PLT').slice(0, 3).toUpperCase() };
}

function renderPlatforms(lr) {
  const container = document.getElementById('platformsContent');
  if (!container) return;
  const platforms = (lr && lr.platforms) || [];

  if (platforms.length === 0) {
    container.innerHTML = '<p style="color:var(--color-text-muted);font-size:var(--text-sm);">No platform resources were recommended. Run a fresh analysis to generate them.</p>';
    return;
  }

  container.innerHTML = `
    <div class="platform-grid">
      ${platforms.map(pl => {
        const style = getPlatformStyle(pl.name);
        const href = pl.url && pl.url.startsWith('http') ? pl.url : `https://www.google.com/search?q=${encodeURIComponent(pl.resource_title + ' ' + pl.name)}`;
        return `
          <a href="${href}" target="_blank" rel="noopener noreferrer" class="resource-link-item">
            <div class="resource-platform-icon" style="background:${style.bg};color:${style.text};">${style.abbr}</div>
            <div class="resource-link-body">
              <div class="resource-link-title">${esc(pl.resource_title)}</div>
              <div style="font-size:.68rem;font-weight:600;color:var(--color-text-muted);margin-bottom:.25rem;">${esc(pl.name)}</div>
              <div class="resource-link-desc">${esc(pl.description)}</div>
            </div>
            <span class="${pl.is_free ? 'resource-free-badge' : 'resource-paid-badge'}">${pl.is_free ? 'Free' : 'Paid'}</span>
          </a>
        `;
      }).join('')}
    </div>
  `;
}

function renderRelatedCareers(related) {
  const container = document.getElementById('relatedContent');
  if (!related || related.length === 0) {
    container.innerHTML = '<p class="text-muted">No related careers found.</p>';
    return;
  }

  const demandColor = { 'High': 'var(--color-success)', 'Medium': 'var(--color-warning)', 'Low': 'var(--color-text-muted)' };

  container.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.25rem;">
      ${related.map(r => {
        const dColor = demandColor[r.market_demand] || demandColor['Medium'];
        const progressSteps = (r.career_progression || []).flatMap((step, idx, arr) =>
          idx < arr.length - 1
            ? [`<span class="progression-step">${esc(step)}</span><span class="progression-arrow">→</span>`]
            : [`<span class="progression-step">${esc(step)}</span>`]
        ).join('');

        return `
          <div class="related-career-card-v2">
            <div class="related-career-header">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:.5rem;margin-bottom:.375rem;">
                <div style="font-size:var(--text-base);font-weight:600;color:var(--color-text-primary);">${esc(r.title)}</div>
                <div style="text-align:right;flex-shrink:0;">
                  <div style="font-size:1.25rem;font-weight:700;color:var(--color-ibm-blue);line-height:1;">${r.similarity}%</div>
                  <div style="font-size:.6rem;color:var(--color-text-muted);">match</div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="font-size:.68rem;font-weight:600;color:${dColor};">${esc(r.market_demand)} Demand</span>
                <span style="color:var(--color-border);">·</span>
                <span style="font-size:.68rem;font-weight:600;color:var(--color-success);">${fmt$(r.avg_salary)}/yr avg.</span>
              </div>
              <div class="progress-bar-wrap" style="margin-top:.5rem;height:3px;">
                <div class="progress-bar-fill" style="width:${r.similarity}%;background:var(--color-ibm-blue);"></div>
              </div>
            </div>
            <div class="related-career-body">
              <p style="font-size:var(--text-xs);color:var(--color-text-secondary);line-height:1.55;margin-bottom:.75rem;">${esc(r.description)}</p>
              ${r.required_skills && r.required_skills.length > 0 ? `
                <div style="margin-bottom:.625rem;">
                  <p style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.375rem;">Key Skills</p>
                  <div class="skill-tags">
                    ${r.required_skills.slice(0,5).map(s => `<span class="tag">${esc(s)}</span>`).join('')}
                  </div>
                </div>
              ` : ''}
              ${progressSteps ? `
                <div>
                  <p style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted);margin-bottom:.375rem;">Career Progression</p>
                  <div class="related-career-progression">${progressSteps}</div>
                </div>
              ` : ''}
              ${r.future_scope ? `
                <div style="margin-top:.625rem;padding:.5rem .75rem;background:var(--color-surface-alt);border-radius:var(--radius-sm);font-size:var(--text-xs);color:var(--color-text-secondary);line-height:1.5;">${esc(r.future_scope)}</div>
              ` : ''}
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// ============================================================
// Search
// ============================================================

function searchReport(query) {
  if (!query.trim()) {
    document.querySelectorAll('.report-section').forEach(s => s.style.display = '');
    return;
  }
  const q = query.toLowerCase();
  document.querySelectorAll('.report-section').forEach(section => {
    const text = section.textContent.toLowerCase();
    section.style.display = text.includes(q) ? '' : 'none';
  });
}

// ============================================================
// PDF Export
// ============================================================

async function exportPDF() {
  const btn = document.getElementById('exportBtn');
  const origText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:15px;height:15px;border-width:2px;"></div> Generating PDF…';

  try {
    const response = await fetch('/api/export/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analysis: _analysis }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || 'PDF generation failed');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const name = (_analysis?.profile?.name || 'student').replace(/ /g, '_');
    link.href = url;
    link.download = `CareerCompass_Report_${name}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast('PDF downloaded successfully!', 'success');

  } catch (err) {
    showToast('PDF export failed: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = origText;
  }
}

// ============================================================
// Main render orchestrator
// ============================================================

function renderFullReport(analysis) {
  _analysis = analysis;

  try { renderHeader(analysis); } catch(e) { console.error('Header error:', e); }
  try { renderCareerRecommendation(analysis.career_recommendation); } catch(e) { console.error('CR error:', e); }
  try { renderSkillAnalysis(analysis.skill_analysis); } catch(e) { console.error('Skills error:', e); }
  try { renderCareerTimeline(analysis.career_timeline); } catch(e) { console.error('Timeline error:', e); }
  try { renderRoadmap(analysis.roadmap); } catch(e) { console.error('Roadmap error:', e); }
  try { renderProjects(analysis.projects); } catch(e) { console.error('Projects error:', e); }
  try { renderCertifications(analysis.certifications); } catch(e) { console.error('Certs error:', e); }
  try { renderLearningResources(analysis.learning_resources); } catch(e) { console.error('Resources error:', e); }
  try { renderPlatforms(analysis.learning_resources); } catch(e) { console.error('Platforms error:', e); }
  try { renderActionPlan(analysis.action_plan); } catch(e) { console.error('Action error:', e); }
  try { renderInternshipStrategy(analysis.internship_strategy); } catch(e) { console.error('Internship error:', e); }
  try { renderInterviewPrep(analysis.interview_preparation); } catch(e) { console.error('Interview error:', e); }
  try { renderProfileBuilding(analysis.profile_building); } catch(e) { console.error('Profile building error:', e); }
  try { renderRelatedCareers(analysis.related_careers); } catch(e) { console.error('Related error:', e); }

  // Charts — slight delay to ensure DOM is painted
  requestAnimationFrame(() => {
    try { renderRadarChart(analysis.skill_analysis); } catch(e) { console.error('Radar error:', e); }
    try { renderSalaryChartAndCards(analysis.career_recommendation); } catch(e) { console.error('Salary error:', e); }
    try { renderAuxCharts(analysis.skill_analysis, analysis.career_recommendation); } catch(e) { console.error('Aux charts error:', e); }
  });

  // Init scroll spy
  initScrollSpy();

  // Animate progress bars
  setTimeout(() => {
    document.querySelectorAll('.progress-bar-fill[style*="width:0%"]').forEach(bar => {
      const target = bar.dataset.target;
      if (target) bar.style.width = target + '%';
    });
    // Confidence bar
    const confBar = document.getElementById('confBar');
    if (confBar && analysis.career_recommendation) {
      confBar.style.width = '0%';
      setTimeout(() => {
        confBar.style.width = analysis.career_recommendation.confidence_score + '%';
      }, 200);
    }
  }, 100);
}

// ============================================================
// Page initialization
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const analysisStr = sessionStorage.getItem('careercompass_analysis');

  if (!analysisStr) {
    document.getElementById('reportLoading').innerHTML = `
      <div style="text-align:center;max-width:440px;padding:2rem;">
        <div style="margin-bottom:1rem;color:var(--color-error);">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <h2 style="font-size:1.5rem;font-weight:700;color:var(--color-text-primary);margin-bottom:.75rem;">No Report Found</h2>
        <p style="color:var(--color-text-secondary);font-size:.9rem;line-height:1.6;margin-bottom:1.5rem;">
          No career analysis data was found. Please fill out your profile and run the analysis first.
        </p>
        <a href="/profile" class="btn btn-primary">Start Analysis</a>
      </div>
    `;
    return;
  }

  let analysis;
  try {
    analysis = JSON.parse(analysisStr);
  } catch (e) {
    console.error('Failed to parse analysis data:', e);
    document.getElementById('reportLoading').innerHTML = `
      <div style="text-align:center;padding:2rem;">
        <p style="color:var(--color-error);margin-bottom:1rem;">Report data is corrupted.</p>
        <a href="/profile" class="btn btn-primary">Start New Analysis</a>
      </div>
    `;
    return;
  }

  // Render report
  renderFullReport(analysis);

  // Show report, hide loading
  document.getElementById('reportLoading').style.display = 'none';
  document.getElementById('reportPage').style.display = 'block';
});
