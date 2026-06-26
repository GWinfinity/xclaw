/**
 * xClaw Tesla AI - Popup Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const backendInput = document.getElementById('backend-url');
  const saveBtn = document.getElementById('save-url');
  const statusText = document.getElementById('status-text');
  const openDashboardBtn = document.getElementById('open-dashboard');
  const openOptionsBtn = document.getElementById('open-options');

  // Load saved backend URL
  chrome.storage.sync.get(['xclawBackendUrl'], (result) => {
    const url = result.xclawBackendUrl || 'http://localhost:8080';
    backendInput.value = url;
    checkBackend(url);
  });

  function setStatus(text, color) {
    statusText.textContent = text;
    statusText.style.color = color || '#111';
  }

  async function checkBackend(url) {
    setStatus('Checking...', '#888');
    try {
      const response = await fetch(`${url}/api/health`, { method: 'GET' });
      if (response.ok) {
        setStatus('Connected', '#0a0');
      } else {
        setStatus('Unreachable', '#c00');
      }
    } catch (error) {
      setStatus('Unreachable', '#c00');
    }
  }

  saveBtn.addEventListener('click', () => {
    const url = backendInput.value.trim() || 'http://localhost:8080';
    chrome.storage.sync.set({ xclawBackendUrl: url }, () => {
      checkBackend(url);
    });
  });

  openDashboardBtn.addEventListener('click', () => {
    const url = backendInput.value.trim() || 'http://localhost:8080';
    chrome.tabs.create({ url: `${url}/dashboard/` });
  });

  openOptionsBtn.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
});
