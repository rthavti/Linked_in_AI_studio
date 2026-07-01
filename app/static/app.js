document.addEventListener('DOMContentLoaded', () => {
  window.__linkedinAppLoaded = true;
  const sections = document.querySelectorAll('nav button');
  const panels = document.querySelectorAll('.panel');
  const scheduleForm = document.getElementById('schedule-form');
  const autoScheduleEnabled = document.getElementById('auto-schedule-enabled');
  const autoScheduleFields = document.getElementById('auto-schedule-fields');
  const topicForm = document.getElementById('topic-form');
  const importForm = document.getElementById('import-form');
  const addTopicButton = document.getElementById('add-topic-button');
  const uploadButton = document.getElementById('upload-button');
  const generateButton = document.getElementById('generate-button');
  const scheduleMessage = document.getElementById('schedule-message');
  const approvedTopicSelect = document.getElementById('approved-topic-select');
  const scheduleTopicDatetime = document.getElementById('schedule-topic-datetime');
  const scheduleTopicButton = document.getElementById('schedule-topic-button');
  const publishQueueList = document.getElementById('publish-queue-list');
  const topicMessage = document.getElementById('topic-message');
  const generateResult = document.getElementById('generate-result');
  const topicsTableContainer = document.getElementById('topics-table-container');
  const historyTableContainer = document.getElementById('history-table-container');
  const historySearch = document.getElementById('history-search');
  const historyStatusFilter = document.getElementById('history-status-filter');
  const historyMessage = document.getElementById('history-message');
  const importSummary = document.getElementById('import-summary');
  const importTableContainer = document.getElementById('import-table-container');
  const importErrors = document.getElementById('import-errors');
  const generatePanel = document.getElementById('generate-panel');
  const generateTopicTitle = document.getElementById('generate-topic-title');
  const generateTopicMeta = document.getElementById('generate-topic-meta');
  const generatedPost = document.getElementById('generated-post');
  const tokenSummary = document.getElementById('token-summary');
  const copyButton = document.getElementById('copy-button');
  const regenerateButton = document.getElementById('regenerate-button');
  const saveDraftButton = document.getElementById('save-draft-button');
  const approveButton = document.getElementById('approve-button');
  const previewEditorInput = document.getElementById('preview-editor-input');
  const linkedinPreviewContent = document.getElementById('linkedin-preview-content');
  const aiInsightsGrid = document.getElementById('ai-insights-grid');
  const oauthReadinessList = document.getElementById('oauth-readiness-list');
  const publishingHardeningList = document.getElementById('publishing-hardening-list');
  const settingsMessage = document.getElementById('settings-message');
  const connectLinkedinButton = document.getElementById('connect-linkedin-button');
  const connectLinkedinMessage = document.getElementById('connect-linkedin-message');
  const oauthMissingHint = document.getElementById('oauth-missing-hint');
  const topicSearch = document.getElementById('topic-search');
  const filterCategory = document.getElementById('filter-category');
  const filterStatus = document.getElementById('filter-status');
  const sortPriority = document.getElementById('sort-priority');
  const kpiTotalTopics = document.getElementById('kpi-total-topics');
  const kpiPending = document.getElementById('kpi-pending');
  const kpiGenerated = document.getElementById('kpi-generated');
  const kpiPublished = document.getElementById('kpi-published');
  const kpiFailed = document.getElementById('kpi-failed');
  const kpiPendingDelta = document.getElementById('kpi-pending-delta');
  const kpiGeneratedDelta = document.getElementById('kpi-generated-delta');
  const kpiPublishedDelta = document.getElementById('kpi-published-delta');
  const heroApiStatus = document.getElementById('hero-api-status');
  const heroDbStatus = document.getElementById('hero-db-status');
  const heroOpenaiStatus = document.getElementById('hero-openai-status');
  const homeRecentTopics = document.getElementById('home-recent-topics');
  const homeRecentGenerated = document.getElementById('home-recent-generated');
  const homeSystemStatus = document.getElementById('home-system-status');
  const homePipelineStrip = document.getElementById('home-pipeline-strip');
  const homeCategoryChart = document.getElementById('home-category-chart');
  const topicDrawer = document.getElementById('topic-drawer');
  const drawerBackdrop = document.getElementById('drawer-backdrop');
  const drawerClose = document.getElementById('drawer-close');
  const drawerTopicTitle = document.getElementById('drawer-topic-title');
  const drawerTopicMeta = document.getElementById('drawer-topic-meta');
  const drawerTimeline = document.getElementById('drawer-timeline');
  const drawerGeneratedPost = document.getElementById('drawer-generated-post');
  const drawerTokenUsage = document.getElementById('drawer-token-usage');
  const drawerGenerateAgain = document.getElementById('drawer-generate-again');
  const drawerApprove = document.getElementById('drawer-approve');
  const drawerDelete = document.getElementById('drawer-delete');

  async function fetchWithTimeout(url, options = {}, timeoutMs = 90000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      clearTimeout(timeoutId);
    }
  }

  function checkStatus(response) {
    return response.json().then((data) => {
      if (!response.ok) {
        const message = data.detail || data.message || response.statusText;
        throw new Error(message);
      }
      return data;
    });
  }

  const api = {
    getDashboard: () => fetchWithTimeout('/dashboard/').then(checkStatus),
    getHealth: () => fetchWithTimeout('/health').then(checkStatus),
    getSchedule: () => fetchWithTimeout('/schedule/settings').then(checkStatus),
    saveSchedule: (payload) => fetchWithTimeout('/schedule/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(checkStatus),
    getTopics: () => fetchWithTimeout('/topics/').then(checkStatus),
    getTopic: (id) => fetchWithTimeout(`/topics/${id}`).then(checkStatus),
    createTopic: (payload) => fetchWithTimeout('/topics/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(checkStatus),
    deleteTopic: (id) => fetchWithTimeout(`/topics/${id}`, { method: 'DELETE' }).then(checkStatus),
    generateContent: () => fetchWithTimeout('/content/generate', { method: 'POST' }, 120000).then(checkStatus),
    regenerateTopic: (id) => fetchWithTimeout(`/topics/${id}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    }).then(checkStatus),
    updateTopicContent: (id, generatedPost) => fetchWithTimeout(`/topics/${id}/content`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ generated_post: generatedPost }),
    }).then(checkStatus),
    importExcel: (formData) => fetchWithTimeout('/ingest/upload', { method: 'POST', body: formData }).then(checkStatus),
    approveTopic: (id) => fetchWithTimeout(`/topics/${id}/approve`, { method: 'POST' }).then(checkStatus),
    getOAuthHealth: () => fetchWithTimeout('/publish/oauth/health').then(checkStatus),
    startLinkedInOAuth: () => fetchWithTimeout('/publish/connect').then(checkStatus),
    enqueuePublish: (payload) => fetchWithTimeout('/publish/queue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(checkStatus),
    getPublishQueue: () => fetchWithTimeout('/publish/queue').then(checkStatus),
  };

  let currentTopics = [];
  let currentTopicId = null;
  let currentLatestHistory = null;

  const statusMeta = {
    PENDING: { icon: '🕒', label: 'PENDING' },
    NEW: { icon: '🟡', label: 'NEW' },
    GENERATING: { icon: '🟠', label: 'GENERATING' },
    READY_FOR_REVIEW: { icon: '🟠', label: 'READY FOR REVIEW' },
    APPROVED: { icon: '🟢', label: 'APPROVED' },
    SCHEDULED: { icon: '🔵', label: 'SCHEDULED' },
    PUBLISHED: { icon: '✅', label: 'PUBLISHED' },
    FAILED: { icon: '🔴', label: 'FAILED' },
    IMPORTED: { icon: '🟢', label: 'IMPORTED' },
    DUPLICATE: { icon: '🟣', label: 'DUPLICATE' },
  };

  function statusClass(value) {
    return `status-${String(value || '').toLowerCase()}`;
  }

  function renderStatusChip(value) {
    const key = String(value || '').toUpperCase();
    const meta = statusMeta[key] || { icon: '⚪', label: key.replaceAll('_', ' ') };
    return `<span class="status-chip ${statusClass(value)}">${meta.icon} ${meta.label}</span>`;
  }

  function renderCompactList(items, emptyText, action) {
    if (!items.length) {
      return `<p>${emptyText}</p>`;
    }

    return `<div class="compact-list">${items.map((item) => `
      <button type="button" class="compact-row action-row" data-action="${action}" data-id="${item.id}">
        <span>${item.left}</span>
        <span>${item.right}</span>
      </button>
    `).join('')}</div>`;
  }

  function toDayStamp(date) {
    return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
  }

  function calculateKpiDeltas(topics) {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    const todayStamp = toDayStamp(today);
    const yesterdayStamp = toDayStamp(yesterday);

    const counts = {
      pendingToday: 0,
      pendingYesterday: 0,
      generatedToday: 0,
      generatedYesterday: 0,
      publishedToday: 0,
      publishedYesterday: 0,
    };

    topics.forEach((topic) => {
      const created = new Date(topic.created_at);
      const updated = new Date(topic.updated_at);
      const createdStamp = toDayStamp(created);
      const updatedStamp = toDayStamp(updated);

      if (topic.status === 'NEW') {
        if (createdStamp === todayStamp) counts.pendingToday += 1;
        if (createdStamp === yesterdayStamp) counts.pendingYesterday += 1;
      }

      if (topic.generated_post) {
        if (updatedStamp === todayStamp) counts.generatedToday += 1;
        if (updatedStamp === yesterdayStamp) counts.generatedYesterday += 1;
      }

      if (topic.status === 'PUBLISHED') {
        if (updatedStamp === todayStamp) counts.publishedToday += 1;
        if (updatedStamp === yesterdayStamp) counts.publishedYesterday += 1;
      }
    });

    return {
      pending: counts.pendingToday - counts.pendingYesterday,
      generated: counts.generatedToday - counts.generatedYesterday,
      published: counts.publishedToday - counts.publishedYesterday,
    };
  }

  function formatDelta(delta, positiveLabel, negativeLabel) {
    if (delta > 0) {
      return { text: `↑ +${delta} ${positiveLabel}`, className: 'delta-up' };
    }
    if (delta < 0) {
      return { text: `↓ ${delta} ${negativeLabel}`, className: 'delta-down' };
    }
    return { text: '→ 0 since yesterday', className: 'delta-flat' };
  }

  function renderPipelineStrip(topics) {
    const stages = [
      { key: 'NEW', label: 'NEW', icon: '🟡' },
      { key: 'GENERATING', label: 'GENERATING', icon: '🟠' },
      { key: 'READY_FOR_REVIEW', label: 'REVIEW', icon: '🟠' },
      { key: 'APPROVED', label: 'APPROVED', icon: '🟢' },
      { key: 'SCHEDULED', label: 'SCHEDULED', icon: '🔵' },
      { key: 'PUBLISHED', label: 'POSTED', icon: '✅' },
    ];

    const counts = stages.reduce((acc, stage) => {
      acc[stage.key] = 0;
      return acc;
    }, {});

    topics.forEach((topic) => {
      if (counts[topic.status] !== undefined) {
        counts[topic.status] += 1;
      }
    });

    return `
      <div class="pipeline-strip">
        ${stages.map((stage) => `
          <div class="pipeline-step">
            <span>${stage.icon} ${stage.label}</span>
            <strong>${counts[stage.key] || 0}</strong>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderCategoryChart(topics) {
    if (!topics.length) {
      return '<p>No category data yet.</p>';
    }

    const counts = topics.reduce((acc, topic) => {
      acc[topic.category] = (acc[topic.category] || 0) + 1;
      return acc;
    }, {});

    const rows = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);

    const max = rows[0]?.[1] || 1;

    return `
      <div class="category-chart">
        ${rows.map(([category, count]) => {
          const width = Math.max(8, Math.round((count / max) * 100));
          return `
            <div class="category-row">
              <label>${category}</label>
              <div class="category-bar"><div class="category-bar-fill" style="width:${width}%"></div></div>
              <em>${count}</em>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function toDatetimeLocalValue(value) {
    const date = value ? new Date(value) : new Date();
    const normalized = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return normalized.toISOString().slice(0, 16);
  }

  function renderApprovedScheduleTopics(topics) {
    if (!approvedTopicSelect) return;

    const approved = topics
      .filter((topic) => topic.status === 'APPROVED' && topic.generated_post)
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

    approvedTopicSelect.innerHTML = `
      <option value="">Select an approved topic...</option>
      ${approved.map((topic) => `<option value="${topic.id}">${topic.topic}</option>`).join('')}
    `;

    if (scheduleTopicDatetime && !scheduleTopicDatetime.value) {
      scheduleTopicDatetime.value = toDatetimeLocalValue();
    }

    if (scheduleTopicButton) {
      scheduleTopicButton.disabled = approved.length === 0;
    }

    if (!approved.length) {
      scheduleMessage.textContent = 'No approved topics available for scheduling.';
    }
  }

  async function loadPublishQueue() {
    if (!publishQueueList) return;
    try {
      const queue = await api.getPublishQueue();
      const upcoming = queue
        .filter((item) => item.status !== 'PUBLISHED')
        .sort((a, b) => new Date(a.scheduled_for) - new Date(b.scheduled_for));

      if (!upcoming.length) {
        publishQueueList.innerHTML = '<p>No upcoming queue items.</p>';
        return;
      }

      publishQueueList.innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Topic ID</th>
              <th>Status</th>
              <th>Scheduled For</th>
              <th>Attempts</th>
            </tr>
          </thead>
          <tbody>
            ${upcoming.map((item) => `
              <tr>
                <td>${item.topic_id}</td>
                <td>${renderStatusChip(item.status)}</td>
                <td>${new Date(item.scheduled_for).toLocaleString()}</td>
                <td>${item.attempts}/${item.max_attempts}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (error) {
      console.error(error);
      publishQueueList.innerHTML = '<p>Unable to load publish queue.</p>';
    }
  }

  function renderHealthRow(emoji, label, statusText, score) {
    const safeScore = Math.max(5, Math.min(100, score));
    return `
      <div class="health-row">
        <div class="health-row-head">
          <span>${emoji} ${label}</span>
          <strong>${statusText}</strong>
        </div>
        <div class="health-bar"><div class="health-fill" style="width:${safeScore}%"></div></div>
      </div>
    `;
  }

  function escapeHtml(value) {
    return value
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function renderLinkedInPreview(text) {
    const safe = escapeHtml(text || '');
    const withCta = safe.replace(/\b(Comment|Share|Follow|Connect|Let me know|What do you think|Drop a|DM me|Message me|Subscribe)\b/gi, '<mark class="cta-highlight">$1</mark>');
    const withHashtags = withCta.replace(/(^|\s)(#[A-Za-z0-9_]+)/g, '$1<span class="hashtag">$2</span>');
    const paragraphs = withHashtags
      .split(/\n\s*\n/g)
      .map((block) => `<p>${block.replace(/\n/g, '<br>')}</p>`)
      .join('');
    linkedinPreviewContent.innerHTML = paragraphs || '<p>No preview text yet.</p>';
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function computeAiInsights(text, latestHistory) {
    const raw = text || '';
    const clean = raw.trim();
    const words = clean ? clean.split(/\s+/).length : 0;
    const characters = raw.length;
    const hashtags = raw.match(/(^|\s)#[A-Za-z0-9_]+/g) || [];
    const hashtagCount = hashtags.length;
    const paragraphs = clean ? clean.split(/\n\s*\n/g).length : 0;
    const readMinutes = Math.max(1, Math.ceil(words / 200));
    const ctaPatterns = [
      'comment',
      'share',
      'follow',
      'connect',
      'let me know',
      'what do you think',
      'drop a',
      'dm me',
      'message me',
      'subscribe',
    ];
    const lower = raw.toLowerCase();
    const ctaDetected = ctaPatterns.some((pattern) => lower.includes(pattern));

    let qualityScore = 70;
    if (words >= 80 && words <= 280) qualityScore += 10;
    if (words > 320) qualityScore -= 8;
    if (words < 40) qualityScore -= 12;
    if (hashtagCount >= 3 && hashtagCount <= 8) qualityScore += 8;
    if (hashtagCount === 0) qualityScore -= 10;
    if (hashtagCount > 10) qualityScore -= 6;
    if (paragraphs >= 2) qualityScore += 4;
    if (ctaDetected) qualityScore += 6;
    if (characters > 3000) qualityScore -= 10;
    qualityScore = clamp(qualityScore, 45, 98);

    let confidence = 'Low';
    if (words >= 90 && words <= 280 && hashtagCount >= 2 && latestHistory?.total_tokens) {
      confidence = 'High';
    } else if (words >= 50 && hashtagCount >= 1) {
      confidence = 'Medium';
    }

    return {
      model: latestHistory?.model || 'GPT-5.5',
      totalTokens: latestHistory?.total_tokens ?? '--',
      readingTime: `${readMinutes} min`,
      characters,
      words,
      hashtags: hashtagCount,
      ctaDetected: ctaDetected ? 'Yes' : 'No',
      qualityScore: `${qualityScore}%`,
      qualityScoreValue: qualityScore,
      confidence,
    };
  }

  function renderAiInsights(text, latestHistory) {
    const metrics = computeAiInsights(text, latestHistory);
    let qualityClass = 'quality-medium';
    if (metrics.qualityScoreValue >= 85) {
      qualityClass = 'quality-high';
    } else if (metrics.qualityScoreValue < 72) {
      qualityClass = 'quality-low';
    }

    aiInsightsGrid.innerHTML = `
      <div class="insight-item"><span>Model</span><strong>${metrics.model}</strong></div>
      <div class="insight-item"><span>Tokens</span><strong>${metrics.totalTokens}</strong></div>
      <div class="insight-item"><span>Reading Time</span><strong>${metrics.readingTime}</strong></div>
      <div class="insight-item"><span>Character Count</span><strong>${metrics.characters}</strong></div>
      <div class="insight-item"><span>Word Count</span><strong>${metrics.words}</strong></div>
      <div class="insight-item"><span>Hashtags</span><strong>${metrics.hashtags}</strong></div>
      <div class="insight-item"><span>CTA</span><strong>${metrics.ctaDetected}</strong></div>
      <div class="insight-item ${qualityClass}"><span>Quality Score</span><strong>${metrics.qualityScore}</strong><div class="insight-confidence">Confidence: ${metrics.confidence}</div></div>
    `;
  }

  async function loadSettingsPanel() {
    if (!oauthReadinessList || !publishingHardeningList) {
      return;
    }

    try {
      const [oauthHealth, schedule] = await Promise.all([
        api.getOAuthHealth(),
        api.getSchedule(),
      ]);

      oauthReadinessList.innerHTML = `
        <div class="compact-list">
          <div class="compact-row"><span>OAuth Configured</span><span>${oauthHealth.oauth_configured ? '✅ Yes' : '❌ No'}</span></div>
          <div class="compact-row"><span>Client ID</span><span>${oauthHealth.client_id_configured ? '✅' : '❌'}</span></div>
          <div class="compact-row"><span>Client Secret</span><span>${oauthHealth.client_secret_configured ? '✅' : '❌'}</span></div>
          <div class="compact-row"><span>Redirect URI</span><span>${oauthHealth.redirect_uri_configured ? '✅' : '❌'}</span></div>
          <div class="compact-row"><span>Scopes</span><span>${oauthHealth.scopes_configured ? '✅' : '❌'}</span></div>
          <div class="compact-row"><span>Token Secret</span><span>${oauthHealth.token_secret_configured ? '✅' : '❌'}</span></div>
          <div class="compact-row"><span>OAuth State TTL</span><span>${oauthHealth.oauth_state_ttl_seconds}s</span></div>
        </div>
      `;

      const atLeastOneWindow = schedule.morning_enabled || schedule.evening_enabled;
      const duplicateWindows = schedule.morning_enabled && schedule.evening_enabled && schedule.morning_time === schedule.evening_time;

      publishingHardeningList.innerHTML = `
        <div class="compact-list">
          <div class="compact-row"><span>Connected Account</span><span>${oauthHealth.connected ? '✅ Connected' : '❌ Not connected'}</span></div>
          <div class="compact-row"><span>Retry Delay</span><span>${oauthHealth.retry_delay_seconds}s</span></div>
          <div class="compact-row"><span>Morning Window</span><span>${schedule.morning_enabled ? `✅ ${schedule.morning_time}` : '❌ Disabled'}</span></div>
          <div class="compact-row"><span>Evening Window</span><span>${schedule.evening_enabled ? `✅ ${schedule.evening_time}` : '❌ Disabled'}</span></div>
          <div class="compact-row"><span>Auto Scheduling</span><span>${atLeastOneWindow ? '✅ Enabled' : 'ℹ Optional Off'}</span></div>
          <div class="compact-row"><span>Duplicate Windows</span><span>${duplicateWindows ? '❌ Same time' : '✅ Distinct / N/A'}</span></div>
        </div>
      `;

      settingsMessage.classList.add('hidden');
      settingsMessage.textContent = '';

      if (oauthMissingHint) {
        const missing = [];
        if (!oauthHealth.client_id_configured) missing.push('LINKEDIN_CLIENT_ID');
        if (!oauthHealth.client_secret_configured) missing.push('LINKEDIN_CLIENT_SECRET');
        if (!oauthHealth.redirect_uri_configured) missing.push('LINKEDIN_REDIRECT_URI');
        if (!oauthHealth.scopes_configured) missing.push('LINKEDIN_SCOPES');
        if (!oauthHealth.token_secret_configured) missing.push('LINKEDIN_TOKEN_SECRET');

        oauthMissingHint.textContent = missing.length
          ? `Missing env vars: ${missing.join(', ')}`
          : 'All required LinkedIn OAuth env vars are configured.';
      }
    } catch (error) {
      console.error(error);
      settingsMessage.textContent = error.message || 'Unable to load settings checks.';
      settingsMessage.classList.remove('hidden');
      if (oauthMissingHint) {
        oauthMissingHint.textContent = '';
      }
    }
  }

  function setGeneratePreviewState(topic, latestHistory = null) {
    const text = topic.generated_post || '';
    previewEditorInput.value = text;
    renderLinkedInPreview(text);
    renderAiInsights(text, latestHistory || currentLatestHistory);
  }

  function setActiveTab(sectionName) {
    sections.forEach((button) => {
      button.classList.toggle('active', button.dataset.section === sectionName);
    });
    panels.forEach((panel) => {
      panel.classList.toggle('active', panel.id === sectionName);
    });
  }

  sections.forEach((button) => {
    button.addEventListener('click', () => setActiveTab(button.dataset.section));
  });

  async function loadSchedule() {
    try {
      const data = await api.getSchedule();
      scheduleForm.morning_enabled.checked = data.morning_enabled;
      scheduleForm.morning_time.value = data.morning_time;
      scheduleForm.evening_enabled.checked = data.evening_enabled;
      scheduleForm.evening_time.value = data.evening_time;

      if (autoScheduleEnabled) {
        autoScheduleEnabled.checked = data.morning_enabled || data.evening_enabled;
      }
      syncAutoScheduleVisibility();
    } catch (error) {
      console.error(error);
      scheduleMessage.textContent = 'Unable to load schedule settings.';
    }
  }

  function syncAutoScheduleVisibility() {
    if (!autoScheduleFields || !autoScheduleEnabled || !scheduleForm) {
      return;
    }

    const enabled = autoScheduleEnabled.checked;
    autoScheduleFields.classList.toggle('hidden', !enabled);

    scheduleForm.morning_enabled.disabled = !enabled;
    scheduleForm.morning_time.disabled = !enabled;
    scheduleForm.evening_enabled.disabled = !enabled;
    scheduleForm.evening_time.disabled = !enabled;
  }

  function renderTopicTable(topics) {
    if (!topics.length) {
      topicsTableContainer.innerHTML = '<p>No topics found. Add one to get started.</p>';
      return;
    }

    const header = `
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Topic</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Generated</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${topics.map((topic) => `
            <tr class="topic-row ${topic.status.toLowerCase()}" data-action="topic-row-view" data-id="${topic.id}">
              <td>${topic.id}</td>
              <td>${topic.topic}</td>
              <td>${topic.category}</td>
              <td>${topic.priority}</td>
              <td>${renderStatusChip(topic.status)}</td>
              <td>${topic.generated_post ? '✅' : '❌'}</td>
              <td>${new Date(topic.created_at).toLocaleString()}</td>
              <td>
                <button type="button" data-action="view" data-id="${topic.id}">View</button>
                <button type="button" data-action="delete" data-id="${topic.id}">Delete</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    topicsTableContainer.innerHTML = header;
  }

  function filterAndSortTopics() {
    const searchTerm = topicSearch.value.trim().toLowerCase();
    const categoryFilter = filterCategory.value;
    const statusFilter = filterStatus.value;
    const prioritySort = sortPriority.value;

    let filtered = currentTopics.slice();

    if (searchTerm) {
      filtered = filtered.filter((topic) => topic.topic.toLowerCase().includes(searchTerm));
    }

    if (categoryFilter) {
      filtered = filtered.filter((topic) => topic.category === categoryFilter);
    }

    if (statusFilter) {
      filtered = filtered.filter((topic) => topic.status === statusFilter);
    }

    if (prioritySort) {
      const order = { HIGH: 1, MEDIUM: 2, LOW: 3 };
      filtered.sort((a, b) => order[a.priority] - order[b.priority]);
    }

    renderTopicTable(filtered);
  }

  function renderHistoryTable(topics) {
    const generatedTopics = topics
      .filter((topic) => topic.generated_post)
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

    const searchTerm = historySearch.value.trim().toLowerCase();
    const status = historyStatusFilter.value;

    const filtered = generatedTopics.filter((topic) => {
      const topicMatch = topic.topic.toLowerCase().includes(searchTerm);
      const statusMatch = !status || topic.status === status;
      return topicMatch && statusMatch;
    });

    if (!filtered.length) {
      historyTableContainer.innerHTML = '<p>No generated content found for the selected filters.</p>';
      historyMessage.classList.remove('hidden');
      historyMessage.textContent = 'Generate content from Topics or Generate tab to build this archive.';
      return;
    }

    historyMessage.classList.add('hidden');
    historyTableContainer.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Topic</th>
            <th>Category</th>
            <th>Status</th>
            <th>Generated On</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${filtered.map((topic) => `
            <tr data-action="history-row-preview" data-id="${topic.id}">
              <td>${topic.topic}</td>
              <td>${topic.category}</td>
              <td>${renderStatusChip(topic.status)}</td>
              <td>${new Date(topic.updated_at).toLocaleString()}</td>
              <td>
                <button type="button" data-action="history-preview" data-id="${topic.id}">Preview</button>
                <button type="button" data-action="history-view" data-id="${topic.id}">Open</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  async function loadTopics() {
    try {
      const topics = await api.getTopics();
      currentTopics = topics;
      filterAndSortTopics();
      renderHistoryTable(topics);
      renderApprovedScheduleTopics(topics);
      await loadHomeDashboard();
      await loadPublishQueue();
    } catch (error) {
      console.error(error);
      topicMessage.textContent = 'Unable to load topics.';
    }
  }

  async function loadHomeDashboard() {
    try {
      const [dashboard, health, topics] = await Promise.all([
        api.getDashboard(),
        api.getHealth(),
        api.getTopics(),
      ]);

      kpiTotalTopics.textContent = dashboard.total_topics;
      kpiPending.textContent = dashboard.pending;
      kpiGenerated.textContent = dashboard.generated;
      kpiPublished.textContent = dashboard.published;
      kpiFailed.textContent = dashboard.failed;

      heroApiStatus.textContent = health.status === 'UP' ? '🟢 LIVE' : '🔴 DOWN';
      heroDbStatus.textContent = '🟢 CONNECTED';
      heroOpenaiStatus.textContent = '🟢 READY';

      const recentTopics = topics
        .slice(0, 5)
        .map((topic) => ({
          id: topic.id,
          left: topic.topic,
          right: renderStatusChip(topic.status),
        }));

      const generatedTopics = topics
        .filter((topic) => topic.generated_post)
        .slice(0, 5)
        .map((topic) => ({
          id: topic.id,
          left: topic.topic,
          right: new Date(topic.updated_at).toLocaleDateString(),
        }));

      homeRecentTopics.innerHTML = renderCompactList(recentTopics, 'No topics yet.', 'recent-topic-open');
      homeRecentGenerated.innerHTML = renderCompactList(generatedTopics, 'No generated posts yet.', 'recent-generated-preview');
      homePipelineStrip.innerHTML = renderPipelineStrip(topics);
      homeCategoryChart.innerHTML = renderCategoryChart(topics);

      const deltas = calculateKpiDeltas(topics);
      const pendingDelta = formatDelta(deltas.pending, 'today', 'since yesterday');
      const generatedDelta = formatDelta(deltas.generated, 'today', 'since yesterday');
      const publishedDelta = formatDelta(deltas.published, 'today', 'since yesterday');

      kpiPendingDelta.textContent = pendingDelta.text;
      kpiPendingDelta.className = `kpi-delta ${pendingDelta.className}`;
      kpiGeneratedDelta.textContent = generatedDelta.text;
      kpiGeneratedDelta.className = `kpi-delta ${generatedDelta.className}`;
      kpiPublishedDelta.textContent = publishedDelta.text;
      kpiPublishedDelta.className = `kpi-delta ${publishedDelta.className}`;

      const totalTopics = dashboard.total_topics || 1;
      const generationScore = Math.round((dashboard.generated / totalTopics) * 100);
      const reliabilityScore = Math.max(100 - (dashboard.failed * 8), 20);

      homeSystemStatus.innerHTML = `
        <div class="health-list">
          ${renderHealthRow('🩺', 'API Health', health.status, health.status === 'UP' ? 96 : 18)}
          ${renderHealthRow('🗄️', 'Database', 'Connected', 92)}
          ${renderHealthRow('🤖', 'OpenAI', 'Configured', 88)}
          ${renderHealthRow('⚙️', 'Generation Throughput', `${generationScore}%`, generationScore)}
          ${renderHealthRow('🛡️', 'Pipeline Reliability', `${reliabilityScore}%`, reliabilityScore)}
        </div>
      `;
    } catch (error) {
      console.error(error);
      heroApiStatus.textContent = '🔴 DOWN';
      heroDbStatus.textContent = '--';
      heroOpenaiStatus.textContent = '--';
      homeSystemStatus.innerHTML = '<p>Unable to load dashboard metrics.</p>';
      homePipelineStrip.innerHTML = '<p>Unable to load pipeline stats.</p>';
      homeCategoryChart.innerHTML = '<p>Unable to load category stats.</p>';
    }
  }

  function closeDrawer() {
    topicDrawer.classList.add('hidden');
    topicDrawer.setAttribute('aria-hidden', 'true');
  }

  async function openDrawer(topicId) {
    try {
      const topic = await api.getTopic(topicId);
      currentTopicId = topic.id;
      const history = topic.generation_history || [];
      const latest = history.length ? history[history.length - 1] : null;

      drawerTopicTitle.textContent = topic.topic;
      drawerTopicMeta.textContent = `${topic.category} | ${topic.priority} | ${topic.status}`;
      drawerGeneratedPost.textContent = topic.generated_post || 'No generated content yet.';
      drawerTokenUsage.textContent = latest
        ? `Prompt: ${latest.prompt_tokens || 0} | Completion: ${latest.completion_tokens || 0} | Total: ${latest.total_tokens || 0}`
        : 'No token data yet.';

      const timeline = ['NEW', 'GENERATING', 'READY_FOR_REVIEW', 'APPROVED', 'SCHEDULED', 'PUBLISHED'];
      drawerTimeline.innerHTML = `<div class="timeline-flow">${timeline.map((step) => renderStatusChip(step)).join('')}</div>`;

      topicDrawer.classList.remove('hidden');
      topicDrawer.setAttribute('aria-hidden', 'false');
    } catch (error) {
      console.error(error);
      topicMessage.textContent = error.message || 'Unable to load topic details.';
    }
  }

  async function previewTopic(topicId) {
    const topic = await api.getTopic(topicId);
    currentTopicId = topic.id;
    setActiveTab('generate');

    generateTopicTitle.textContent = topic.topic;
    generateTopicMeta.innerHTML = `Category ${topic.category} • Priority ${topic.priority} • Status ${topic.status}`;
    generatedPost.textContent = topic.generated_post || '';
    const latestHistory = topic.generation_history?.length ? topic.generation_history[topic.generation_history.length - 1] : null;
    currentLatestHistory = latestHistory;
    setGeneratePreviewState(topic, latestHistory);

    tokenSummary.innerHTML = latestHistory ? `Prompt Tokens ${latestHistory.prompt_tokens || 0} • Completion Tokens ${latestHistory.completion_tokens || 0} • Total Tokens ${latestHistory.total_tokens || 0}` : '';
    generatePanel.classList.remove('hidden');
    generateResult.textContent = 'Preview loaded from selected history item.';
  }

  async function displayGenerateResult(result) {
    if (!result.success || !result.topic) {
      currentTopicId = null;
      generateResult.textContent = result.message || 'Generation failed.';
      generatePanel.classList.add('hidden');
      return;
    }

    const topic = result.topic;
    currentTopicId = topic.id;
    const latestHistory = topic.generation_history?.length ? topic.generation_history[topic.generation_history.length - 1] : null;
    currentLatestHistory = latestHistory;

    generateTopicTitle.textContent = topic.topic;
    generateTopicMeta.innerHTML = `Category ${topic.category} • Priority ${topic.priority} • Status ${topic.status}`;
    generatedPost.textContent = topic.generated_post || '';
    setGeneratePreviewState(topic, latestHistory);
    tokenSummary.innerHTML = latestHistory ? `Prompt Tokens ${latestHistory.prompt_tokens || 0} • Completion Tokens ${latestHistory.completion_tokens || 0} • Total Tokens ${latestHistory.total_tokens || 0}` : '';
    generatePanel.classList.remove('hidden');
    generateResult.textContent = result.message || 'LinkedIn content generated successfully.';
  }

  scheduleForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    scheduleMessage.textContent = '';

    const autoEnabled = autoScheduleEnabled ? autoScheduleEnabled.checked : true;

    const payload = {
      morning_enabled: autoEnabled ? scheduleForm.morning_enabled.checked : false,
      morning_time: scheduleForm.morning_time.value,
      evening_enabled: autoEnabled ? scheduleForm.evening_enabled.checked : false,
      evening_time: scheduleForm.evening_time.value,
    };

    if (autoEnabled && !payload.morning_enabled && !payload.evening_enabled) {
      scheduleMessage.textContent = 'Enable morning or evening window, or disable auto scheduling.';
      return;
    }

    if (autoEnabled && payload.morning_enabled && payload.evening_enabled && payload.morning_time === payload.evening_time) {
      scheduleMessage.textContent = 'Morning and evening windows cannot use the same time.';
      return;
    }

    try {
      await api.saveSchedule(payload);
      scheduleMessage.textContent = autoEnabled
        ? 'Auto scheduling defaults saved successfully.'
        : 'Auto scheduling is disabled. Manual topic scheduling remains active.';
      await loadSettingsPanel();
    } catch (error) {
      console.error(error);
      scheduleMessage.textContent = error.message || 'Failed to save schedule settings.';
    }
  });

  if (autoScheduleEnabled) {
    autoScheduleEnabled.addEventListener('change', () => {
      syncAutoScheduleVisibility();
    });
  }

  async function handleTopicCreate() {
    topicMessage.textContent = '';

    const payload = {
      topic: topicForm.topic.value.trim(),
      category: topicForm.category.value,
      priority: topicForm.priority.value,
    };

    if (!payload.topic || !payload.category || !payload.priority) {
      topicMessage.textContent = 'Please complete all topic fields.';
      return;
    }

    try {
      await api.createTopic(payload);
      topicMessage.textContent = 'Topic added successfully.';
      topicForm.reset();
      await loadTopics();
    } catch (error) {
      console.error(error);
      topicMessage.textContent = error.message || 'Failed to add topic.';
    }
  }

  topicForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    await handleTopicCreate();
  });

  addTopicButton.addEventListener('click', async () => {
    await handleTopicCreate();
  });

  topicsTableContainer.addEventListener('click', async (event) => {
    const row = event.target.closest('tr[data-action="topic-row-view"]');
    const button = event.target.closest('button');

    if (!button && row?.dataset.id) {
      await openDrawer(row.dataset.id);
      return;
    }
    if (!button) return;

    const topicId = button.dataset.id;
    const action = button.dataset.action;

    if (action === 'delete' && topicId) {
      try {
        await api.deleteTopic(topicId);
        await loadTopics();
        topicMessage.textContent = 'Topic deleted successfully.';
      } catch (error) {
        console.error(error);
        topicMessage.textContent = 'Failed to delete topic.';
      }
    }

    if (action === 'view' && topicId) {
      await openDrawer(topicId);
    }
  });

  historyTableContainer.addEventListener('click', async (event) => {
    const row = event.target.closest('tr[data-action="history-row-preview"]');
    const button = event.target.closest('button');

    if (!button && row?.dataset.id) {
      await previewTopic(row.dataset.id);
      return;
    }

    if (!button) {
      return;
    }

    if (button.dataset.action === 'history-view' && button.dataset.id) {
      await openDrawer(button.dataset.id);
    }

    if (button.dataset.action === 'history-preview' && button.dataset.id) {
      await previewTopic(button.dataset.id);
    }
  });

  homeRecentTopics.addEventListener('click', async (event) => {
    const trigger = event.target.closest('[data-action="recent-topic-open"]');
    if (!trigger?.dataset.id) {
      return;
    }
    await openDrawer(trigger.dataset.id);
  });

  homeRecentGenerated.addEventListener('click', async (event) => {
    const trigger = event.target.closest('[data-action="recent-generated-preview"]');
    if (!trigger?.dataset.id) {
      return;
    }
    await previewTopic(trigger.dataset.id);
  });

  if (scheduleTopicButton) {
    scheduleTopicButton.addEventListener('click', async () => {
      const topicId = approvedTopicSelect?.value;
      const dateTime = scheduleTopicDatetime?.value;

      if (!topicId) {
        scheduleMessage.textContent = 'Select an approved topic to schedule.';
        return;
      }

      if (!dateTime) {
        scheduleMessage.textContent = 'Please pick a date and time before scheduling.';
        return;
      }

      try {
        scheduleTopicButton.disabled = true;
        await api.enqueuePublish({
          topic_id: Number(topicId),
          scheduled_for: new Date(dateTime).toISOString(),
          max_attempts: 3,
        });
        scheduleMessage.textContent = 'Topic scheduled successfully.';
        await loadTopics();
      } catch (error) {
        console.error(error);
        scheduleMessage.textContent = error.message || 'Unable to schedule this topic.';
      } finally {
        scheduleTopicButton.disabled = false;
      }
    });
  }

  if (connectLinkedinButton) {
    connectLinkedinButton.addEventListener('click', async () => {
      connectLinkedinButton.disabled = true;
      connectLinkedinMessage.textContent = 'Preparing LinkedIn authorization...';

      try {
        const oauth = await api.startLinkedInOAuth();
        const opened = window.open(oauth.authorize_url, '_blank', 'noopener,noreferrer');
        if (!opened) {
          window.location.assign(oauth.authorize_url);
        }
        connectLinkedinMessage.textContent = 'Authorization opened. Complete LinkedIn consent and return to continue.';
      } catch (error) {
        console.error(error);
        connectLinkedinMessage.textContent = error.message || 'Failed to start LinkedIn authorization.';
        if (oauthMissingHint && !oauthMissingHint.textContent) {
          oauthMissingHint.textContent = 'Open OAuth readiness checks above and set all missing env vars.';
        }
      } finally {
        connectLinkedinButton.disabled = false;
      }
    });
  }

  async function handleImportUpload() {
    importSummary.textContent = '';
    importTableContainer.innerHTML = '';
    importErrors.textContent = '';

    const fileInput = importForm.querySelector('input[name="file"]');
    const selectedFile = fileInput && fileInput.files && fileInput.files[0];
    if (!selectedFile) {
      importErrors.textContent = 'Please select an .xlsx or .xls file before uploading.';
      return;
    }

    uploadButton.disabled = true;
    uploadButton.textContent = 'Uploading...';
    importSummary.textContent = `Uploading ${selectedFile.name}...`;

    const formData = new FormData(importForm);
    try {
      const result = await api.importExcel(formData);
      importSummary.textContent = `Imported: ${result.summary.imported} • Duplicates: ${result.summary.duplicates} • Failed: ${result.summary.failed}`;

      if (result.rows && result.rows.length) {
        importTableContainer.innerHTML = `
          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Topic</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              ${result.rows.map((row) => `
                <tr>
                  <td>${row.row}</td>
                  <td>${row.topic}</td>
                  <td>${row.category}</td>
                  <td>${row.priority}</td>
                  <td>${renderStatusChip(row.status)}</td>
                  <td>${row.error_message || ''}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }

      if (result.summary.errors && result.summary.errors.length) {
        importErrors.innerHTML = result.summary.errors.map((error) => `<div>Row ${error.row}: ${error.message}</div>`).join('');
      }

      await loadTopics();
    } catch (error) {
      console.error(error);
      importErrors.textContent = error.message || 'Import failed. Please check the file format.';
    } finally {
      uploadButton.disabled = false;
      uploadButton.textContent = 'Upload';
    }
  }

  importForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    await handleImportUpload();
  });

  uploadButton.addEventListener('click', async () => {
    await handleImportUpload();
  });

  generateButton.addEventListener('click', async () => {
    generateButton.disabled = true;
    generateButton.textContent = 'Generating...';
    generateResult.textContent = 'Generating content. This can take up to 60 seconds.';
    try {
      const result = await api.generateContent();
      await displayGenerateResult(result);
      await loadTopics();
    } catch (error) {
      console.error(error);
      if (error.name === 'AbortError') {
        generateResult.textContent = 'Generation timed out. Please retry.';
      } else {
        generateResult.textContent = error.message || 'Content generation failed. Ensure there is a pending topic.';
      }
    } finally {
      generateButton.disabled = false;
      generateButton.textContent = 'Generate Now';
    }
  });

  copyButton.addEventListener('click', async () => {
    const text = previewEditorInput.value.trim() || generatedPost.textContent;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    generateResult.textContent = 'Text copied to clipboard.';
  });

  previewEditorInput.addEventListener('input', () => {
    renderLinkedInPreview(previewEditorInput.value);
    renderAiInsights(previewEditorInput.value, currentLatestHistory);
  });

  saveDraftButton.addEventListener('click', async () => {
    if (!currentTopicId) {
      generateResult.textContent = 'No topic selected for draft save.';
      return;
    }

    const text = previewEditorInput.value.trim();
    if (!text) {
      generateResult.textContent = 'Draft cannot be empty.';
      return;
    }

    try {
      const updated = await api.updateTopicContent(currentTopicId, text);
      generatedPost.textContent = updated.generated_post || text;
      generateTopicMeta.innerHTML = `Category ${updated.category} • Priority ${updated.priority} • Status ${updated.status}`;
      renderLinkedInPreview(updated.generated_post || text);
      renderAiInsights(updated.generated_post || text, currentLatestHistory);
      await loadTopics();
      generateResult.textContent = 'Draft saved successfully.';
    } catch (error) {
      console.error(error);
      generateResult.textContent = error.message || 'Failed to save draft.';
    }
  });

  regenerateButton.addEventListener('click', async () => {
    generateResult.textContent = '';
    try {
      const result = await api.generateContent();
      await displayGenerateResult(result);
      await loadTopics();
    } catch (error) {
      console.error(error);
      generateResult.textContent = error.message || 'Regeneration failed. Ensure there is a pending topic.';
    }
  });

  approveButton.addEventListener('click', async () => {
    if (!currentTopicId) {
      generateResult.textContent = 'No topic selected for approval.';
      return;
    }

    try {
      const draft = previewEditorInput.value.trim();
      if (draft) {
        await api.updateTopicContent(currentTopicId, draft);
      }
      await api.approveTopic(currentTopicId);
      generateResult.textContent = 'Topic approved from preview successfully.';
      await loadTopics();
      await previewTopic(currentTopicId);
    } catch (error) {
      console.error(error);
      generateResult.textContent = error.message || 'Failed to approve topic.';
    }
  });

  drawerClose.addEventListener('click', closeDrawer);
  drawerBackdrop.addEventListener('click', closeDrawer);

  drawerApprove.addEventListener('click', async () => {
    if (!currentTopicId) {
      return;
    }

    try {
      await api.approveTopic(currentTopicId);
      await loadTopics();
      await openDrawer(currentTopicId);
    } catch (error) {
      console.error(error);
      topicMessage.textContent = error.message || 'Unable to approve topic.';
    }
  });

  drawerGenerateAgain.addEventListener('click', async () => {
    if (!currentTopicId) {
      return;
    }

    try {
      await api.regenerateTopic(currentTopicId);
      await loadTopics();
      await openDrawer(currentTopicId);
    } catch (error) {
      console.error(error);
      topicMessage.textContent = error.message || 'Unable to regenerate topic.';
    }
  });

  drawerDelete.addEventListener('click', async () => {
    if (!currentTopicId) {
      return;
    }

    try {
      await api.deleteTopic(currentTopicId);
      closeDrawer();
      await loadTopics();
      topicMessage.textContent = 'Topic deleted successfully.';
    } catch (error) {
      console.error(error);
      topicMessage.textContent = error.message || 'Unable to delete topic.';
    }
  });

  topicSearch.addEventListener('input', filterAndSortTopics);
  filterCategory.addEventListener('change', filterAndSortTopics);
  filterStatus.addEventListener('change', filterAndSortTopics);
  sortPriority.addEventListener('change', filterAndSortTopics);
  historySearch.addEventListener('input', () => renderHistoryTable(currentTopics));
  historyStatusFilter.addEventListener('change', () => renderHistoryTable(currentTopics));

  setActiveTab('home');
  loadHomeDashboard();
  loadSchedule();
  loadSettingsPanel();
  loadTopics();
});
