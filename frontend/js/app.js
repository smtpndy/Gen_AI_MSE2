// Smart API URL detection:
// - If served by FastAPI on port 8000 → use same origin
// - If opened via Live Server (5500), file://, or any other port → point to FastAPI on 8000
const API = (() => {
  const p = window.location.port;
  if (p === '8000' || p === '80' || p === '443' || p === '') {
    return window.location.origin + '/api';
  }
  // Dev server (VS Code Live Server :5500, Vite :5173, etc.) → backend is on :8000
  return window.location.protocol + '//' + window.location.hostname + ':8000/api';
})();

function getToken() { return localStorage.getItem('token'); }
function getUsername() { return localStorage.getItem('username'); }
function getRole() { return localStorage.getItem('role'); }

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  };
}

async function apiGet(path) {
  const r = await fetch(`${API}${path}`, { headers: authHeaders() });
  if (r.status === 401) { logout(); return null; }
  return r.json();
}

async function apiPost(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(body)
  });
  if (r.status === 401) { logout(); return null; }
  return { ok: r.ok, status: r.status, data: await r.json() };
}

async function apiDelete(path) {
  const r = await fetch(`${API}${path}`, { method: 'DELETE', headers: authHeaders() });
  if (r.status === 401) { logout(); return null; }
  return { ok: r.ok, data: await r.json() };
}

function logout() {
  localStorage.clear();
  window.location.href = '/';
}

function requireAuth() {
  if (!getToken()) { window.location.href = '/'; return false; }
  return true;
}

function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span><span>${msg}</span>`;
  document.body.appendChild(el);
  setTimeout(() => el.classList.add('show'), 10);
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 3500);
}

function formatDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTime(t) {
  if (!t) return '-';
  return t;
}

function buildNav(active) {
  const username = getUsername();
  return `
  <nav class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-icon-sm">👁️</div>
      <span>FaceAttend</span>
    </div>
    <div class="nav-links">
      <a href="/dashboard" class="nav-link ${active==='dashboard'?'active':''}">
        <span class="nav-icon">📊</span> Dashboard
      </a>
      <a href="/register" class="nav-link ${active==='register'?'active':''}">
        <span class="nav-icon">👤</span> Register Student
      </a>
      <a href="/students" class="nav-link ${active==='students'?'active':''}">
        <span class="nav-icon">🎓</span> Students
      </a>
      <a href="/attendance" class="nav-link ${active==='attendance'?'active':''}">
        <span class="nav-icon">📸</span> Live Attendance
      </a>
      <a href="/reports" class="nav-link ${active==='reports'?'active':''}">
        <span class="nav-icon">📋</span> Reports
      </a>
      <a href="/ai-query" class="nav-link ${active==='ai'?'active':''}">
        <span class="nav-icon">🤖</span> AI Query
      </a>
    </div>
    <div class="sidebar-footer">
      <div class="user-info">
        <div class="user-avatar">${username ? username[0].toUpperCase() : 'A'}</div>
        <div>
          <div class="user-name">${username || 'Admin'}</div>
          <div class="user-role">${getRole() || 'admin'}</div>
        </div>
      </div>
      <button class="logout-btn" onclick="logout()">⏻</button>
    </div>
  </nav>`;
}
