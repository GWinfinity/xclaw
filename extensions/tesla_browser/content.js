/**
 * xClaw Tesla AI - Content Script
 *
 * Injects a floating AI assistant button on Tesla web pages
 * (e.g., Tesla account, ownership portal). When clicked, opens
 * the xClaw dashboard in a side panel or new tab.
 */

(function () {
  'use strict';

  const PANEL_ID = 'xclaw-tesla-panel';
  const BUTTON_ID = 'xclaw-tesla-button';

  function getBackendUrl() {
    return new Promise((resolve) => {
      if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.sync.get(['xclawBackendUrl'], (result) => {
          resolve(result.xclawBackendUrl || 'http://localhost:8080');
        });
      } else {
        resolve('http://localhost:8080');
      }
    });
  }

  function createButton() {
    if (document.getElementById(BUTTON_ID)) return;

    const btn = document.createElement('button');
    btn.id = BUTTON_ID;
    btn.title = 'Open xClaw AI';
    btn.innerHTML = 'X';
    document.body.appendChild(btn);

    btn.addEventListener('click', async () => {
      const backendUrl = await getBackendUrl();
      togglePanel(backendUrl);
    });
  }

  function togglePanel(backendUrl) {
    let panel = document.getElementById(PANEL_ID);
    if (panel) {
      panel.remove();
      return;
    }

    panel = document.createElement('div');
    panel.id = PANEL_ID;
    panel.innerHTML = `
      <div class="xclaw-header">
        <span>xClaw Tesla AI</span>
        <button id="xclaw-close">×</button>
      </div>
      <iframe src="${backendUrl}/dashboard/" frameborder="0"></iframe>
    `;
    document.body.appendChild(panel);

    document.getElementById('xclaw-close').addEventListener('click', () => {
      panel.remove();
    });
  }

  // Wait for the page to settle, then inject
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createButton);
  } else {
    createButton();
  }
})();
