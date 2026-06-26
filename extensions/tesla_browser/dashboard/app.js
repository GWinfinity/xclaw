/**
 * xClaw Tesla AI Dashboard
 *
 * Runs in the Tesla browser or any modern browser.
 * Connects to the xClaw backend API for vehicle state and chat.
 */

(function () {
  'use strict';

  const API_BASE = window.location.origin;
  const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const WS_URL = `${wsProto}//${window.location.host}/ws`;

  const els = {
    connStatus: document.getElementById('conn-status'),
    vName: document.getElementById('v-name'),
    vState: document.getElementById('v-state'),
    vBattery: document.getElementById('v-battery'),
    vRange: document.getElementById('v-range'),
    vClimate: document.getElementById('v-climate'),
    vLocked: document.getElementById('v-locked'),
    refreshBtn: document.getElementById('refresh-status'),
    chatHistory: document.getElementById('chat-history'),
    chatInput: document.getElementById('chat-input'),
    chatSend: document.getElementById('chat-send'),
    quickBtns: document.querySelectorAll('.quick-btn'),
  };

  let ws = null;

  async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`, { credentials: 'include' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function apiPost(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function setConnected(connected) {
    els.connStatus.textContent = connected ? 'Connected' : 'Disconnected';
    els.connStatus.classList.toggle('connected', connected);
    els.connStatus.classList.toggle('disconnected', !connected);
  }

  async function loadVehicleStatus() {
    try {
      const data = await apiGet('/api/vehicle');
      const fleet = data.fleet_api || {};
      els.vName.textContent = fleet.display_name || '-';
      els.vState.textContent = fleet.state || '-';
      els.vBattery.textContent =
        fleet.battery_level !== undefined ? `${fleet.battery_level}%` : '-';
      els.vRange.textContent =
        fleet.battery_range_miles !== undefined
          ? `${Math.round(fleet.battery_range_miles)} mi`
          : '-';
      els.vClimate.textContent =
        fleet.is_climate_on !== undefined
          ? fleet.is_climate_on
            ? 'On'
            : 'Off'
          : '-';
      els.vLocked.textContent =
        fleet.locked !== undefined ? (fleet.locked ? 'Yes' : 'No') : '-';
      setConnected(true);
    } catch (error) {
      console.error('Failed to load vehicle status:', error);
      setConnected(false);
    }
  }

  function appendMessage(role, text, meta) {
    const msg = document.createElement('div');
    msg.className = `message ${role}`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    msg.appendChild(bubble);

    if (meta) {
      const metaEl = document.createElement('div');
      metaEl.className = 'meta';
      metaEl.textContent = meta;
      msg.appendChild(metaEl);
    }

    els.chatHistory.appendChild(msg);
    els.chatHistory.scrollTop = els.chatHistory.scrollHeight;
  }

  async function sendMessage(text) {
    if (!text.trim()) return;

    appendMessage('user', text);
    els.chatInput.value = '';

    try {
      const data = await apiPost('/api/chat', { message: text });
      appendMessage('ai', data.content || 'No response', data.model || 'AI');

      // Refresh status if a command was executed
      if (data.executed_commands && data.executed_commands.length > 0) {
        await loadVehicleStatus();
      }
    } catch (error) {
      appendMessage('ai', `Error: ${error.message}`);
    }
  }

  function connectWebSocket() {
    try {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'vehicle_update') {
            loadVehicleStatus();
          } else if (data.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = () => {
        setConnected(false);
      };
    } catch (error) {
      console.error('WebSocket connect error:', error);
    }
  }

  // Event listeners
  els.refreshBtn.addEventListener('click', loadVehicleStatus);

  els.chatSend.addEventListener('click', () => {
    sendMessage(els.chatInput.value);
  });

  els.chatInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendMessage(els.chatInput.value);
    }
  });

  els.quickBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) sendMessage(prompt);
    });
  });

  // Initialize
  loadVehicleStatus();
  connectWebSocket();
})();
