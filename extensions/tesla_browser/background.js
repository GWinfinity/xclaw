/**
 * xClaw Tesla AI - Background Service Worker
 *
 * Handles extension icon clicks and keeps the backend URL available.
 */

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ xclawBackendUrl: 'http://localhost:8080' });
});

chrome.action.onClicked.addListener(async (tab) => {
  const { xclawBackendUrl } = await chrome.storage.sync.get(['xclawBackendUrl']);
  chrome.tabs.create({ url: `${xclawBackendUrl}/dashboard/` });
});
