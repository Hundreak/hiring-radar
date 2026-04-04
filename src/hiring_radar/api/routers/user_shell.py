from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["user-shell"])

_THEME_AND_BASE_STYLES = """
:root {
  --bg: #f6f8fb;
  --bg-accent: radial-gradient(circle at top left, rgba(96, 165, 250, 0.14), transparent 35%), radial-gradient(circle at bottom right, rgba(168, 85, 247, 0.10), transparent 30%), #f6f8fb;
  --surface: rgba(255, 255, 255, 0.88);
  --surface-strong: #ffffff;
  --surface-soft: #eef2ff;
  --border: rgba(15, 23, 42, 0.08);
  --text: #0f172a;
  --text-muted: #475569;
  --primary: #2563eb;
  --primary-strong: #1d4ed8;
  --success-bg: #dcfce7;
  --success-text: #166534;
  --warning-bg: #fef3c7;
  --warning-text: #92400e;
  --danger-bg: #fee2e2;
  --danger-text: #991b1b;
  --shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
}

[data-theme="dark"] {
  --bg: #0b1120;
  --bg-accent: radial-gradient(circle at top left, rgba(59, 130, 246, 0.16), transparent 35%), radial-gradient(circle at bottom right, rgba(168, 85, 247, 0.14), transparent 30%), #0b1120;
  --surface: rgba(15, 23, 42, 0.78);
  --surface-strong: #111827;
  --surface-soft: #172036;
  --border: rgba(148, 163, 184, 0.14);
  --text: #e5eefb;
  --text-muted: #94a3b8;
  --primary: #60a5fa;
  --primary-strong: #3b82f6;
  --success-bg: rgba(22, 101, 52, 0.22);
  --success-text: #86efac;
  --warning-bg: rgba(146, 64, 14, 0.26);
  --warning-text: #fcd34d;
  --danger-bg: rgba(153, 27, 27, 0.24);
  --danger-text: #fca5a5;
  --shadow: 0 18px 45px rgba(2, 6, 23, 0.42);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg-accent);
  color: var(--text);
}
a { color: var(--primary); text-decoration: none; }
button {
  border: none;
  border-radius: 14px;
  padding: 12px 16px;
  font-weight: 700;
  cursor: pointer;
  background: var(--primary);
  color: white;
  transition: transform 0.16s ease, opacity 0.16s ease;
}
button:hover { transform: translateY(-1px); opacity: 0.96; }
button.secondary {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
}
button.ghost {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
}
input, textarea {
  width: 100%;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--surface-strong);
  color: var(--text);
  padding: 12px 14px;
  outline: none;
}
input::placeholder, textarea::placeholder { color: var(--text-muted); }
label { display: block; font-weight: 700; margin-bottom: 8px; }
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.badge.success { background: var(--success-bg); color: var(--success-text); }
.badge.warning { background: var(--warning-bg); color: var(--warning-text); }
.badge.danger { background: var(--danger-bg); color: var(--danger-text); }
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.theme-toggle {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  backdrop-filter: blur(14px);
  box-shadow: var(--shadow);
}
.theme-toggle button {
  padding: 8px 12px;
  border-radius: 999px;
}
.shell {
  min-height: 100vh;
  padding: 28px;
}
.hero-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
}
.hero-side {
  padding: 48px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.hero-copy h1 {
  font-size: clamp(40px, 5vw, 64px);
  line-height: 1.02;
  margin: 0 0 16px;
}
.hero-copy p {
  max-width: 620px;
  font-size: 18px;
  line-height: 1.7;
  color: var(--text-muted);
}
.hero-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 28px;
}
.mini-card, .card {
  background: var(--surface);
  border: 1px solid var(--border);
  backdrop-filter: blur(16px);
  box-shadow: var(--shadow);
}
.mini-card {
  border-radius: 24px;
  padding: 18px;
}
.mini-label {
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 10px;
}
.mini-value {
  font-size: 28px;
  font-weight: 800;
}
.panel-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 36px;
}
.auth-card {
  width: 100%;
  max-width: 460px;
  border-radius: 28px;
  padding: 28px;
}
.auth-card h2 {
  margin: 0 0 8px;
  font-size: 28px;
}
.auth-card p {
  color: var(--text-muted);
  line-height: 1.6;
}
.form-row {
  margin-bottom: 16px;
}
.muted {
  color: var(--text-muted);
}
.status {
  min-height: 24px;
  margin-top: 10px;
  font-size: 14px;
}
.status.ok { color: var(--success-text); }
.status.error { color: var(--danger-text); }
.app-wrap {
  max-width: 1120px;
  margin: 0 auto;
}
.app-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}
.card {
  border-radius: 24px;
  padding: 22px;
}
.card h2 {
  margin-top: 0;
  margin-bottom: 14px;
  font-size: 20px;
}
.kpi {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.kpi-box {
  border-radius: 18px;
  background: var(--surface-soft);
  padding: 16px;
  border: 1px solid var(--border);
}
.kpi-box .kpi-label {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 8px;
}
.kpi-box .kpi-value {
  font-size: 22px;
  font-weight: 800;
}
.form-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 20px;
}
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}
.toggle-row:last-child { border-bottom: none; }
.toggle-copy strong { display: block; margin-bottom: 4px; }
.toggle-copy span { color: var(--text-muted); font-size: 14px; }
.switch {
  position: relative;
  width: 56px;
  height: 32px;
  background: #cbd5e1;
  border-radius: 999px;
  transition: background 0.2s ease;
  border: 1px solid var(--border);
}
.switch.on { background: var(--primary); }
.switch::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: white;
  transition: transform 0.2s ease;
}
.switch.on::after { transform: translateX(24px); }
.policy-list {
  display: grid;
  gap: 12px;
}
.policy-item {
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 16px;
}
.policy-item .title {
  font-weight: 800;
  margin-bottom: 8px;
}
.policy-item .meta {
  color: var(--text-muted);
  line-height: 1.6;
}
.footer-note {
  margin-top: 18px;
  color: var(--text-muted);
  font-size: 13px;
}
@media (max-width: 960px) {
  .hero-shell { grid-template-columns: 1fr; }
  .app-grid { grid-template-columns: 1fr; }
  .shell { padding: 18px; }
  .hero-side, .panel-side { padding: 22px; }
}
"""

def _theme_script() -> str:
    return """
const THEME_STORAGE_KEY = "hiring_radar_theme";

function preferredTheme() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  const indicator = document.getElementById("theme-indicator");
  if (indicator) {
    indicator.textContent = theme === "dark" ? "Dark mode" : "Light mode";
  }
}

function setupThemeControls() {
  const lightButton = document.getElementById("theme-light");
  const darkButton = document.getElementById("theme-dark");

  if (lightButton) {
    lightButton.addEventListener("click", () => applyTheme("light"));
  }
  if (darkButton) {
    darkButton.addEventListener("click", () => applyTheme("dark"));
  }

  applyTheme(preferredTheme());
}
"""

def _theme_control_html() -> str:
    return """
<div class="theme-toggle">
  <span id="theme-indicator" class="muted">Theme</span>
  <button id="theme-light" class="secondary" type="button">Light</button>
  <button id="theme-dark" class="secondary" type="button">Dark</button>
</div>
"""

def _render_page(*, title: str, body_html: str, script: str) -> HTMLResponse:
    html = f"""
<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{_THEME_AND_BASE_STYLES}</style>
</head>
<body>
  {body_html}
  <script>
    {_theme_script()}

    async function ensureUserSession() {{
      const response = await fetch("/api/user/auth/me", {{ credentials: "same-origin" }});
      if (!response.ok) {{
        window.location.href = "/app/login";
        return null;
      }}
      return await response.json();
    }}

    async function logoutUser() {{
      await fetch("/api/user/auth/logout", {{
        method: "POST",
        credentials: "same-origin",
      }});
      window.location.href = "/app/login";
    }}

    {script}
    setupThemeControls();
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@router.get("/", response_class=RedirectResponse)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/app/login", status_code=302)


@router.get("/app/login", response_class=HTMLResponse)
def user_login_page() -> HTMLResponse:
    body = f"""
<div class="hero-shell">
  <section class="hero-side">
    <div>
      <div class="topbar">
        <div>
          <div style="font-weight:800; font-size:18px;">Hiring Radar</div>
          <div class="muted">Personal preferences panel</div>
        </div>
        {_theme_control_html()}
      </div>

      <div class="hero-copy">
        <h1>Control your job alerts in a clean, modern space.</h1>
        <p>
          Sign in with a secure email link, switch between light and dark mode,
          and manage your digest preferences without needing admin help.
        </p>
      </div>

      <div class="hero-grid">
        <div class="mini-card">
          <div class="mini-label">Secure access</div>
          <div class="mini-value">Magic Link</div>
          <div class="muted">Passwordless sign-in with short-lived tokens.</div>
        </div>
        <div class="mini-card">
          <div class="mini-label">Personal control</div>
          <div class="mini-value">Self-Service</div>
          <div class="muted">Update your profile and digest settings anytime.</div>
        </div>
        <div class="mini-card">
          <div class="mini-label">Readable UI</div>
          <div class="mini-value">Light / Dark</div>
          <div class="muted">Theme-aware surfaces and comfortable spacing.</div>
        </div>
        <div class="mini-card">
          <div class="mini-label">Transparent policy</div>
          <div class="mini-value">Filter Aware</div>
          <div class="muted">See how the global digest filter affects results.</div>
        </div>
      </div>
    </div>

    <div class="footer-note">
      Built to feel trustworthy, calm, and easy to use across light and dark themes.
    </div>
  </section>

  <section class="panel-side">
    <div class="auth-card card">
      <h2>Sign in to your dashboard</h2>
      <p>
        Enter your subscriber email. If your account is eligible, we will send a secure sign-in link.
      </p>

      <form id="magic-link-form">
        <div class="form-row">
          <label for="email">Email address</label>
          <input id="email" name="email" type="email" required placeholder="you@example.com">
        </div>
        <button type="submit" style="width:100%;">Send sign-in link</button>
        <div class="status" id="request-status"></div>
      </form>

      <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--border);">
        <strong>Already opened a sign-in link?</strong>
        <p class="muted" style="margin-bottom: 0;">
          If this page contains a token in the URL, login continues automatically.
        </p>
      </div>
    </div>
  </section>
</div>
"""
    script = """
async function requestMagicLink(email) {
  const response = await fetch("/api/user/auth/request-magic-link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ email }),
  });

  const data = await response.json().catch(() => ({
    message: "If that email is eligible, a sign-in link has been sent.",
  }));

  document.getElementById("request-status").className = "status ok";
  document.getElementById("request-status").textContent =
    data.message || "If that email is eligible, a sign-in link has been sent.";
}

async function consumeTokenIfPresent() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (!token) return;

  const statusEl = document.getElementById("request-status");
  statusEl.className = "status";
  statusEl.textContent = "Completing sign-in…";

  const response = await fetch("/api/user/auth/consume-magic-link", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ token }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "Sign-in failed." }));
    statusEl.className = "status error";
    statusEl.textContent = data.detail || "Sign-in failed.";
    return;
  }

  window.history.replaceState({}, document.title, "/app/login");
  window.location.href = "/app/preferences";
}

document.getElementById("magic-link-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = document.getElementById("email").value.trim();
  if (!email) return;
  await requestMagicLink(email);
});

consumeTokenIfPresent();
"""
    return _render_page(
        title="Hiring Radar Login",
        body_html=body,
        script=script,
    )


@router.get("/app/preferences", response_class=HTMLResponse)
def user_preferences_page() -> HTMLResponse:
    body = f"""
<div class="shell">
  <div class="app-wrap">
    <div class="topbar">
      <div>
        <div style="font-weight:800; font-size:24px;">Your Preferences</div>
        <div id="identity" class="muted">Checking session…</div>
      </div>
      <div style="display:flex; gap:12px; align-items:center;">
        {_theme_control_html()}
        <button class="ghost" onclick="logoutUser()">Log out</button>
      </div>
    </div>

    <div class="app-grid">
      <div class="card">
        <h2>Account overview</h2>
        <div class="kpi">
          <div class="kpi-box">
            <div class="kpi-label">Account status</div>
            <div class="kpi-value" id="kpi-account-status">-</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-label">Digest delivery</div>
            <div class="kpi-value" id="kpi-digest-status">-</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-label">Profile name</div>
            <div class="kpi-value" id="kpi-profile-name" style="font-size:16px;">-</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-label">Email</div>
            <div class="kpi-value" id="kpi-email" style="font-size:16px;">-</div>
          </div>
        </div>
        <div class="footer-note" id="profile-updated-at">Updated at: -</div>
      </div>

      <div class="card">
        <h2>Manage preferences</h2>
        <div class="form-row">
          <label for="full_name">Full name</label>
          <input id="full_name" type="text" placeholder="Your name">
        </div>

        <div class="toggle-row">
          <div class="toggle-copy">
            <strong>Account active</strong>
            <span>Pause all activity tied to your subscriber record.</span>
          </div>
          <button id="toggle-active" class="secondary" type="button">
            <span id="toggle-active-indicator" class="switch"></span>
          </button>
        </div>

        <div class="toggle-row">
          <div class="toggle-copy">
            <strong>Digest emails</strong>
            <span>Receive digest emails when your subscription is enabled.</span>
          </div>
          <button id="toggle-digest" class="secondary" type="button">
            <span id="toggle-digest-indicator" class="switch"></span>
          </button>
        </div>

        <div class="form-actions">
          <button type="button" onclick="savePreferences()">Save changes</button>
        </div>
        <div class="status" id="save-status"></div>
      </div>
    </div>

    <div class="card" style="margin-top: 20px;">
      <h2>Current filter policy</h2>
      <div class="policy-list">
        <div class="policy-item">
          <div class="title">Digest filter mode</div>
          <div class="meta" id="policy-digest-default">-</div>
        </div>
        <div class="policy-item">
          <div class="title">Include keywords</div>
          <div class="meta" id="policy-include">-</div>
        </div>
        <div class="policy-item">
          <div class="title">Exclude keywords</div>
          <div class="meta" id="policy-exclude">-</div>
        </div>
        <div class="policy-item">
          <div class="title">Active match fields</div>
          <div class="meta" id="policy-fields">-</div>
        </div>
      </div>
      <div class="footer-note">
        This policy is managed globally by the system administrator and shown here for transparency.
      </div>
    </div>
  </div>
</div>
"""
    script = """
let preferenceState = {
  id: null,
  is_active: true,
  digest_enabled: true,
};

function setSwitchVisual(elementId, isOn) {
  const node = document.getElementById(elementId);
  node.className = isOn ? "switch on" : "switch";
}

function paintProfile(profile) {
  preferenceState.id = profile.id;
  preferenceState.is_active = profile.is_active;
  preferenceState.digest_enabled = profile.digest_enabled;

  document.getElementById("identity").textContent = `Signed in as ${profile.email}`;
  document.getElementById("kpi-account-status").textContent =
    profile.is_active ? "Active" : "Paused";
  document.getElementById("kpi-digest-status").textContent =
    profile.digest_enabled ? "Enabled" : "Disabled";
  document.getElementById("kpi-profile-name").textContent = profile.full_name || "Not set";
  document.getElementById("kpi-email").textContent = profile.email;
  document.getElementById("profile-updated-at").textContent =
    `Updated at: ${profile.updated_at || "-"}`;
  document.getElementById("full_name").value = profile.full_name || "";

  setSwitchVisual("toggle-active-indicator", profile.is_active);
  setSwitchVisual("toggle-digest-indicator", profile.digest_enabled);
}

function paintPolicy(policy) {
  document.getElementById("policy-digest-default").textContent =
    policy.apply_keyword_filter_to_digest
      ? "The global keyword filter is applied to digests by default."
      : "Digests run without the global keyword filter by default.";

  document.getElementById("policy-include").textContent =
    policy.include_keywords.length ? policy.include_keywords.join(", ") : "No include keywords";
  document.getElementById("policy-exclude").textContent =
    policy.exclude_keywords.length ? policy.exclude_keywords.join(", ") : "No exclude keywords";
  document.getElementById("policy-fields").textContent =
    policy.active_fields.length ? policy.active_fields.join(", ") : "No active fields";
}

async function loadPreferences() {
  const me = await ensureUserSession();
  if (!me) return;

  const [profileResponse, policyResponse] = await Promise.all([
    fetch("/api/user/me", { credentials: "same-origin" }),
    fetch("/api/user/me/filter-policy", { credentials: "same-origin" }),
  ]);

  if (!profileResponse.ok) {
    document.getElementById("save-status").className = "status error";
    document.getElementById("save-status").textContent = "Failed to load profile.";
    return;
  }

  const profile = await profileResponse.json();
  paintProfile(profile);

  if (policyResponse.ok) {
    const policy = await policyResponse.json();
    paintPolicy(policy);
  }
}

async function savePreferences() {
  const payload = {
    full_name: document.getElementById("full_name").value.trim() || null,
    is_active: preferenceState.is_active,
    digest_enabled: preferenceState.digest_enabled,
  };

  const response = await fetch("/api/user/me/preferences", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "Save failed." }));
    document.getElementById("save-status").className = "status error";
    document.getElementById("save-status").textContent =
      data.detail || "Save failed.";
    return;
  }

  const profile = await response.json();
  paintProfile(profile);
  document.getElementById("save-status").className = "status ok";
  document.getElementById("save-status").textContent = "Preferences saved successfully.";
}

document.getElementById("toggle-active").addEventListener("click", () => {
  preferenceState.is_active = !preferenceState.is_active;
  setSwitchVisual("toggle-active-indicator", preferenceState.is_active);
  document.getElementById("kpi-account-status").textContent =
    preferenceState.is_active ? "Active" : "Paused";
});

document.getElementById("toggle-digest").addEventListener("click", () => {
  preferenceState.digest_enabled = !preferenceState.digest_enabled;
  setSwitchVisual("toggle-digest-indicator", preferenceState.digest_enabled);
  document.getElementById("kpi-digest-status").textContent =
    preferenceState.digest_enabled ? "Enabled" : "Disabled";
});

loadPreferences();
"""
    return _render_page(
        title="Hiring Radar Preferences",
        body_html=body,
        script=script,
    )