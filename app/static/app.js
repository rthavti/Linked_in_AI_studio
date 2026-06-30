const sections = document.querySelectorAll('nav button');
const panels = document.querySelectorAll('.panel');
const scheduleForm = document.getElementById('schedule-form');
const topicForm = document.getElementById('topic-form');
const importForm = document.getElementById('import-form');
const generateButton = document.getElementById('generate-button');
const scheduleMessage = document.getElementById('schedule-message');
const topicMessage = document.getElementById('topic-message');
const importResult = document.getElementById('import-result');
const generateResult = document.getElementById('generate-result');
const topicsList = document.getElementById('topics-list');

const api = {
  getSchedule: () => fetch('/schedule/settings').then((res) => res.json()),
  saveSchedule: (payload) => fetch('/schedule/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then((res) => res.json()),
  getTopics: () => fetch('/topics/').then((res) => res.json()),
  createTopic: (payload) => fetch('/topics/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then((res) => res.json()),
  deleteTopic: (id) => fetch(`/topics/${id}`, { method: 'DELETE' }),
  generateContent: () => fetch('/content/generate', { method: 'POST' }).then((res) => res.json()),
  importExcel: (formData) => fetch('/ingest/upload', { method: 'POST', body: formData }).then((res) => res.json()),
};

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
  } catch (error) {
    scheduleMessage.textContent = 'Unable to load schedule settings.';
  }
}

async function loadTopics() {
  try {
    const topics = await api.getTopics();
    topicsList.innerHTML = '';

    if (topics.length === 0) {
      topicsList.innerHTML = '<p>No topics found. Add one to get started.</p>';
      return;
    }

    topics.forEach((topic) => {
      const item = document.createElement('div');
      item.className = 'topic-item';
      item.innerHTML = `
        <div><strong>${topic.topic}</strong></div>
        <div>Category: ${topic.category}</div>
        <div>Priority: ${topic.priority}</div>
        <div>Status: ${topic.status}</div>
        <div class="topic-actions">
          <button data-action="delete" data-id="${topic.id}">Delete</button>
        </div>
      `;
      topicsList.appendChild(item);
    });
  } catch (error) {
    topicMessage.textContent = 'Unable to load topics.';
  }
}

scheduleForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  scheduleMessage.textContent = '';

  const payload = {
    morning_enabled: scheduleForm.morning_enabled.checked,
    morning_time: scheduleForm.morning_time.value,
    evening_enabled: scheduleForm.evening_enabled.checked,
    evening_time: scheduleForm.evening_time.value,
  };

  try {
    await api.saveSchedule(payload);
    scheduleMessage.textContent = 'Schedule settings saved successfully.';
  } catch (error) {
    scheduleMessage.textContent = 'Failed to save schedule settings.';
  }
});

topicForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  topicMessage.textContent = '';

  const formData = new FormData(topicForm);
  const payload = {
    topic: formData.get('topic'),
    category: formData.get('category'),
    priority: formData.get('priority'),
  };

  try {
    await api.createTopic(payload);
    topicMessage.textContent = 'Topic added successfully.';
    topicForm.reset();
    await loadTopics();
  } catch (error) {
    topicMessage.textContent = 'Failed to add topic.';
  }
});

topicsList.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;

  const topicId = button.dataset.id;
  if (button.dataset.action === 'delete' && topicId) {
    try {
      await api.deleteTopic(topicId);
      await loadTopics();
      topicMessage.textContent = 'Topic deleted successfully.';
    } catch (error) {
      topicMessage.textContent = 'Failed to delete topic.';
    }
  }
});

importForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  importResult.textContent = '';

  const formData = new FormData(importForm);
  try {
    const result = await api.importExcel(formData);
    importResult.textContent = JSON.stringify(result, null, 2);
    await loadTopics();
  } catch (error) {
    importResult.textContent = 'Import failed. Please check the file format.';
  }
});

generateButton.addEventListener('click', async () => {
  generateResult.textContent = '';
  try {
    const result = await api.generateContent();
    generateResult.textContent = result.message || 'Content generation request succeeded.';
    await loadTopics();
  } catch (error) {
    generateResult.textContent = 'Content generation failed. Ensure there is a pending topic.';
  }
});

setActiveTab('schedule');
loadSchedule();
loadTopics();
