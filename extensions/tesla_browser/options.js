/**
 * xClaw Tesla AI - Options Page Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const backendInput = document.getElementById('backend-url');
  const vinInput = document.getElementById('default-vin');
  const saveBtn = document.getElementById('save');
  const savedMsg = document.getElementById('saved-msg');

  chrome.storage.sync.get(['xclawBackendUrl', 'xclawDefaultVin'], (result) => {
    backendInput.value = result.xclawBackendUrl || 'http://localhost:8080';
    vinInput.value = result.xclawDefaultVin || '';
  });

  saveBtn.addEventListener('click', () => {
    const url = backendInput.value.trim() || 'http://localhost:8080';
    const vin = vinInput.value.trim().toUpperCase();

    chrome.storage.sync.set(
      {
        xclawBackendUrl: url,
        xclawDefaultVin: vin,
      },
      () => {
        savedMsg.style.display = 'block';
        setTimeout(() => {
          savedMsg.style.display = 'none';
        }, 2000);
      }
    );
  });
});
