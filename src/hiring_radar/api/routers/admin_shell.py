from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-shell"])

_LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hiring Radar Admin Login</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; background: #f6f7fb; color: #111827; }
    .card { max-width: 420px; margin: 72px auto; background: white; border-radius: 20px; padding: 32px; box-shadow: 0 8px 30px rgba(15, 23, 42, 0.08); }
    h1 { margin: 0 0 8px; font-size: 28px; }
    p { color: #4b5563; margin-bottom: 24px; }
    label { display: block; font-weight: 600; margin-bottom: 8px; margin-top: 16px; }
    input { width: 100%; box-sizing: border-box; padding: 12px 14px; border-radius: 12px; border: 1px solid #d1d5db; }
    button { margin-top: 20px; width: 100%; padding: 12px 14px; border: none; border-radius: 12px; background: #111827; color: white; font-weight: 600; cursor: pointer; }
    .error { color: #b91c1c; min-height: 24px; margin-top: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Admin Login</h1>
    <p>Use the configured admin credentials to access the Hiring Radar panel foundation.</p>
    <form id="login-form">
      <label for="email">Email</label>
      <input id="email" name="email" type="email" required>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" required>
      <button type="submit">Sign in</button>
      <div class="error" id="error"></div>
    </form>
  </div>
  <script>
    const form = document.getElementById("login-form");
    const errorEl = document.getElementById("error");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorEl.textContent = "";

      const payload = {
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
      };

      const response = await fetch("/api/admin/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: "Login failed." }));
        errorEl.textContent = data.detail || "Login failed.";
        return;
      }

      window.location.href = "/admin/dashboard";
    });
  </script>
</body>
</html>
"""

_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hiring Radar Admin Dashboard</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; background: #f6f7fb; color: #111827; margin: 0; }
    .wrap { max-width: 1080px; margin: 0 auto; padding: 32px; }
    .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
    .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-bottom: 24px; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 8px 30px rgba(15, 23, 42, 0.08); }
    .label { color: #6b7280; font-size: 14px; margin-bottom: 8px; }
    .value { font-size: 28px; font-weight: 700; }
    button { padding: 10px 14px; border: none; border-radius: 12px; background: #111827; color: white; font-weight: 600; cursor: pointer; }
    pre { background: #0f172a; color: #e2e8f0; border-radius: 20px; padding: 20px; overflow: auto; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div>
        <h1 style="margin:0 0 6px">Hiring Radar Admin</h1>
        <div id="identity" style="color:#6b7280">Checking session…</div>
      </div>
      <button id="logout">Log out</button>
    </div>

    <div class="grid">
      <div class="card"><div class="label">Total Jobs</div><div class="value" id="total-jobs">-</div></div>
      <div class="card"><div class="label">Active Jobs</div><div class="value" id="active-jobs">-</div></div>
      <div class="card"><div class="label">Subscribers</div><div class="value" id="subscribers">-</div></div>
      <div class="card"><div class="label">Digest Filter Active</div><div class="value" id="digest-filter">-</div></div>
    </div>

    <div class="card">
      <h2 style="margin-top:0">Dashboard Summary Payload</h2>
      <pre id="summary">Loading…</pre>
    </div>
  </div>

  <script>
    async function loadDashboard() {
      const meResponse = await fetch("/api/admin/auth/me", { credentials: "same-origin" });
      if (!meResponse.ok) {
        window.location.href = "/admin/login";
        return;
      }

      const me = await meResponse.json();
      document.getElementById("identity").textContent = `Signed in as ${me.email}`;

      const summaryResponse = await fetch("/api/admin/dashboard/summary", {
        credentials: "same-origin",
      });
      if (!summaryResponse.ok) {
        document.getElementById("summary").textContent = "Failed to load summary.";
        return;
      }

      const summary = await summaryResponse.json();
      document.getElementById("total-jobs").textContent = summary.jobs.total_jobs;
      document.getElementById("active-jobs").textContent = summary.jobs.active_jobs;
      document.getElementById("subscribers").textContent = summary.subscribers.total_subscribers;
      document.getElementById("digest-filter").textContent =
        summary.digest_filter_policy.apply_keyword_filter_to_digest ? "On" : "Off";
      document.getElementById("summary").textContent = JSON.stringify(summary, null, 2);
    }

    document.getElementById("logout").addEventListener("click", async () => {
      await fetch("/api/admin/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });
      window.location.href = "/admin/login";
    });

    loadDashboard();
  </script>
</body>
</html>
"""


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page() -> HTMLResponse:
    return HTMLResponse(_LOGIN_HTML)


@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page() -> HTMLResponse:
    return HTMLResponse(_DASHBOARD_HTML)