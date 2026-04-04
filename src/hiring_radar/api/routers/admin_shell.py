from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-shell"])

_BASE_STYLES = """
body { font-family: Inter, Arial, sans-serif; background: #f6f7fb; color: #111827; margin: 0; }
.layout { display: grid; grid-template-columns: 250px 1fr; min-height: 100vh; }
.sidebar { background: #0f172a; color: #e2e8f0; padding: 24px; }
.brand { font-size: 22px; font-weight: 700; margin-bottom: 24px; }
.nav a { display: block; color: #cbd5e1; text-decoration: none; padding: 10px 12px; border-radius: 12px; margin-bottom: 8px; }
.nav a:hover, .nav a.active { background: #1e293b; color: #ffffff; }
.content { padding: 32px; }
.card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 8px 30px rgba(15, 23, 42, 0.08); }
.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-bottom: 24px; }
.label { color: #6b7280; font-size: 14px; margin-bottom: 8px; }
.value { font-size: 28px; font-weight: 700; }
.topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
button { padding: 10px 14px; border: none; border-radius: 12px; background: #111827; color: white; font-weight: 600; cursor: pointer; }
button.secondary { background: #e5e7eb; color: #111827; }
button.small { padding: 8px 12px; font-size: 13px; }
.filters { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.filters input, .filters select, textarea { padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 12px; background: white; }
textarea { width: 100%; min-height: 120px; box-sizing: border-box; }
.table-wrap { overflow: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 12px 10px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
th { color: #6b7280; font-size: 13px; text-transform: uppercase; letter-spacing: 0.02em; }
.badge { display: inline-block; padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.badge.success { background: #dcfce7; color: #166534; }
.badge.warning { background: #fef3c7; color: #92400e; }
.badge.danger { background: #fee2e2; color: #991b1b; }
.meta { color: #6b7280; font-size: 14px; margin-bottom: 16px; }
.pager { display: flex; gap: 10px; align-items: center; margin-top: 16px; }
.login-page { background: #f6f7fb; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.login-card { width: 100%; max-width: 420px; background: white; border-radius: 20px; padding: 32px; box-shadow: 0 8px 30px rgba(15, 23, 42, 0.08); }
.login-card input { width: 100%; box-sizing: border-box; padding: 12px 14px; border-radius: 12px; border: 1px solid #d1d5db; margin-top: 8px; margin-bottom: 16px; }
.error { color: #b91c1c; min-height: 24px; margin-top: 12px; }
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
code.inline { background: #f3f4f6; padding: 2px 6px; border-radius: 8px; }
.form-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
.form-row { margin-bottom: 16px; }
.checkbox-row { display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }
.checkbox-row label { display: inline-flex; gap: 8px; align-items: center; font-weight: 600; }
.preview-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.preview-list { background: #f8fafc; border-radius: 16px; padding: 16px; min-height: 120px; }
.preview-item { border-bottom: 1px solid #e5e7eb; padding: 12px 0; }
.preview-item:last-child { border-bottom: none; }
.status-ok { color: #166534; }
.status-error { color: #991b1b; }
"""

def _admin_layout(*, title: str, active_nav: str, body_html: str, script: str) -> HTMLResponse:
    nav_items = [
        ("dashboard", "/admin/dashboard", "Dashboard"),
        ("jobs", "/admin/jobs", "Jobs"),
        ("crawl-runs", "/admin/crawl-runs", "Crawl Runs"),
        ("notification-runs", "/admin/notification-runs", "Notification Runs"),
        ("subscribers", "/admin/subscribers", "Subscribers"),
        ("settings", "/admin/settings", "Settings"),
    ]
    nav_html = "".join(
        f'<a href="{href}" class="{"active" if key == active_nav else ""}">{label}</a>'
        for key, href, label in nav_items
    )

    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{_BASE_STYLES}</style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">Hiring Radar Admin</div>
      <nav class="nav">{nav_html}</nav>
    </aside>
    <main class="content">
      {body_html}
    </main>
  </div>
  <script>
    async function ensureAdminSession() {{
      const response = await fetch("/api/admin/auth/me", {{ credentials: "same-origin" }});
      if (!response.ok) {{
        window.location.href = "/admin/login";
        return null;
      }}
      return await response.json();
    }}

    async function logoutAdmin() {{
      await fetch("/api/admin/auth/logout", {{
        method: "POST",
        credentials: "same-origin",
      }});
      window.location.href = "/admin/login";
    }}

    {script}
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page() -> HTMLResponse:
    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hiring Radar Admin Login</title>
  <style>{_BASE_STYLES}</style>
</head>
<body>
  <div class="login-page">
    <div class="login-card">
      <h1 style="margin:0 0 8px;">Admin Login</h1>
      <p style="color:#6b7280; margin-bottom:24px;">
        Sign in to access the Hiring Radar admin panel.
      </p>
      <form id="login-form">
        <label for="email" style="font-weight:600;">Email</label>
        <input id="email" name="email" type="email" required>
        <label for="password" style="font-weight:600;">Password</label>
        <input id="password" name="password" type="password" required>
        <button type="submit" style="width:100%;">Sign in</button>
        <div class="error" id="error"></div>
      </form>
    </div>
  </div>
  <script>
    const form = document.getElementById("login-form");
    const errorEl = document.getElementById("error");

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      errorEl.textContent = "";

      const payload = {{
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
      }};

      const response = await fetch("/api/admin/auth/login", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        credentials: "same-origin",
        body: JSON.stringify(payload),
      }});

      if (!response.ok) {{
        const data = await response.json().catch(() => ({{ detail: "Login failed." }}));
        errorEl.textContent = data.detail || "Login failed.";
        return;
      }}

      window.location.href = "/admin/dashboard";
    }});
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page() -> HTMLResponse:
    body = """
<div class="topbar">
  <div>
    <h1 style="margin:0 0 6px;">Dashboard</h1>
    <div id="identity" class="meta">Checking session…</div>
  </div>
  <button onclick="logoutAdmin()">Log out</button>
</div>

<div class="grid">
  <div class="card"><div class="label">Total Jobs</div><div class="value" id="total-jobs">-</div></div>
  <div class="card"><div class="label">Active Jobs</div><div class="value" id="active-jobs">-</div></div>
  <div class="card"><div class="label">Subscribers</div><div class="value" id="subscribers">-</div></div>
  <div class="card"><div class="label">Digest Filter</div><div class="value" id="digest-filter">-</div></div>
</div>

<div class="card">
  <h2 style="margin-top:0;">Summary Payload</h2>
  <pre id="summary" style="background:#0f172a;color:#e2e8f0;border-radius:20px;padding:20px;overflow:auto;">Loading…</pre>
</div>
"""
    script = """
async function loadDashboard() {
  const me = await ensureAdminSession();
  if (!me) return;

  document.getElementById("identity").textContent = `Signed in as ${me.email}`;

  const response = await fetch("/api/admin/dashboard/summary", {
    credentials: "same-origin",
  });
  if (!response.ok) {
    document.getElementById("summary").textContent = "Failed to load dashboard summary.";
    return;
  }

  const summary = await response.json();
  document.getElementById("total-jobs").textContent = summary.jobs.total_jobs;
  document.getElementById("active-jobs").textContent = summary.jobs.active_jobs;
  document.getElementById("subscribers").textContent = summary.subscribers.total_subscribers;
  document.getElementById("digest-filter").textContent =
    summary.digest_filter_policy.apply_keyword_filter_to_digest ? "On" : "Off";
  document.getElementById("summary").textContent = JSON.stringify(summary, null, 2);
}

loadDashboard();
"""
    return _admin_layout(
        title="Hiring Radar Admin Dashboard",
        active_nav="dashboard",
        body_html=body,
        script=script,
    )


@router.get("/admin/jobs", response_class=HTMLResponse)
def admin_jobs_page() -> HTMLResponse:
    body = """
<div class="topbar">
  <div>
    <h1 style="margin:0 0 6px;">Jobs</h1>
    <div id="identity" class="meta">Checking session…</div>
  </div>
  <button onclick="logoutAdmin()">Log out</button>
</div>

<div class="card">
  <div class="filters">
    <input id="q" placeholder="Search title, company, location, URL">
    <input id="source_name" placeholder="Source name">
    <input id="company_name" placeholder="Company name">
    <select id="is_active">
      <option value="">All statuses</option>
      <option value="true">Active</option>
      <option value="false">Inactive</option>
    </select>
    <select id="page_size">
      <option value="10">10 rows</option>
      <option value="25" selected>25 rows</option>
      <option value="50">50 rows</option>
    </select>
    <button onclick="loadJobs(1)">Apply Filters</button>
  </div>

  <div class="meta" id="jobs-meta">Loading…</div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Company</th>
          <th>Source</th>
          <th>Status</th>
          <th>First Seen</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody id="jobs-table-body"></tbody>
    </table>
  </div>

  <div class="pager">
    <button class="secondary" id="jobs-prev">Previous</button>
    <span id="jobs-page">Page -</span>
    <button class="secondary" id="jobs-next">Next</button>
  </div>
</div>
"""
    script = """
let jobsState = { page: 1, totalPages: 0 };

function jobsFilters() {
  const params = new URLSearchParams();
  const q = document.getElementById("q").value.trim();
  const sourceName = document.getElementById("source_name").value.trim();
  const companyName = document.getElementById("company_name").value.trim();
  const isActive = document.getElementById("is_active").value;
  const pageSize = document.getElementById("page_size").value;

  if (q) params.set("q", q);
  if (sourceName) params.set("source_name", sourceName);
  if (companyName) params.set("company_name", companyName);
  if (isActive) params.set("is_active", isActive);
  params.set("page_size", pageSize);

  return params;
}

async function loadJobs(page) {
  const me = await ensureAdminSession();
  if (!me) return;
  document.getElementById("identity").textContent = `Signed in as ${me.email}`;

  const params = jobsFilters();
  params.set("page", page);

  const response = await fetch(`/api/admin/jobs?${params.toString()}`, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    document.getElementById("jobs-meta").textContent = "Failed to load jobs.";
    return;
  }

  const data = await response.json();
  jobsState.page = data.page;
  jobsState.totalPages = data.total_pages;

  document.getElementById("jobs-meta").textContent =
    `Showing ${data.items.length} of ${data.total_items} jobs`;
  document.getElementById("jobs-page").textContent =
    `Page ${data.page} / ${data.total_pages || 1}`;

  const tbody = document.getElementById("jobs-table-body");
  tbody.innerHTML = "";
  for (const item of data.items) {
    const statusClass = item.is_active ? "success" : "warning";
    const statusLabel = item.is_active ? "Active" : "Inactive";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.id}</td>
      <td>${item.title}</td>
      <td>${item.company_name}</td>
      <td><code class="inline">${item.source_name}</code></td>
      <td><span class="badge ${statusClass}">${statusLabel}</span></td>
      <td>${item.first_seen_at || "-"}</td>
      <td><a href="${item.canonical_url}" target="_blank" rel="noreferrer">Open</a></td>
    `;
    tbody.appendChild(row);
  }

  document.getElementById("jobs-prev").disabled = data.page <= 1;
  document.getElementById("jobs-next").disabled =
    data.total_pages === 0 || data.page >= data.total_pages;
}

document.getElementById("jobs-prev").addEventListener("click", () => {
  if (jobsState.page > 1) loadJobs(jobsState.page - 1);
});

document.getElementById("jobs-next").addEventListener("click", () => {
  if (jobsState.page < jobsState.totalPages) loadJobs(jobsState.page + 1);
});

loadJobs(1);
"""
    return _admin_layout(
        title="Hiring Radar Admin Jobs",
        active_nav="jobs",
        body_html=body,
        script=script,
    )


@router.get("/admin/crawl-runs", response_class=HTMLResponse)
def admin_crawl_runs_page() -> HTMLResponse:
    body = """
<div class="topbar">
  <div>
    <h1 style="margin:0 0 6px;">Crawl Runs</h1>
    <div id="identity" class="meta">Checking session…</div>
  </div>
  <button onclick="logoutAdmin()">Log out</button>
</div>

<div class="card">
  <div class="filters">
    <input id="crawl_source_name" placeholder="Source name">
    <select id="crawl_success">
      <option value="">All outcomes</option>
      <option value="true">Success</option>
      <option value="false">Failed</option>
    </select>
    <select id="crawl_page_size">
      <option value="10">10 rows</option>
      <option value="25" selected>25 rows</option>
      <option value="50">50 rows</option>
    </select>
    <button onclick="loadCrawlRuns(1)">Apply Filters</button>
  </div>

  <div class="meta" id="crawl-meta">Loading…</div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Source</th>
          <th>Started</th>
          <th>Finished</th>
          <th>Outcome</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody id="crawl-table-body"></tbody>
    </table>
  </div>

  <div class="pager">
    <button class="secondary" id="crawl-prev">Previous</button>
    <span id="crawl-page">Page -</span>
    <button class="secondary" id="crawl-next">Next</button>
  </div>
</div>
"""
    script = """
let crawlState = { page: 1, totalPages: 0 };

function crawlFilters() {
  const params = new URLSearchParams();
  const sourceName = document.getElementById("crawl_source_name").value.trim();
  const success = document.getElementById("crawl_success").value;
  const pageSize = document.getElementById("crawl_page_size").value;

  if (sourceName) params.set("source_name", sourceName);
  if (success) params.set("success", success);
  params.set("page_size", pageSize);

  return params;
}

async function loadCrawlRuns(page) {
  const me = await ensureAdminSession();
  if (!me) return;
  document.getElementById("identity").textContent = `Signed in as ${me.email}`;

  const params = crawlFilters();
  params.set("page", page);

  const response = await fetch(`/api/admin/crawl-runs?${params.toString()}`, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    document.getElementById("crawl-meta").textContent = "Failed to load crawl runs.";
    return;
  }

  const data = await response.json();
  crawlState.page = data.page;
  crawlState.totalPages = data.total_pages;

  document.getElementById("crawl-meta").textContent =
    `Showing ${data.items.length} of ${data.total_items} crawl runs`;
  document.getElementById("crawl-page").textContent =
    `Page ${data.page} / ${data.total_pages || 1}`;

  const tbody = document.getElementById("crawl-table-body");
  tbody.innerHTML = "";
  for (const item of data.items) {
    const badgeClass = item.success === true ? "success" : item.success === false ? "danger" : "warning";
    const badgeLabel = item.success === true ? "Success" : item.success === false ? "Failed" : "Unknown";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.id}</td>
      <td><code class="inline">${item.source_name}</code></td>
      <td>${item.started_at}</td>
      <td>${item.finished_at || "-"}</td>
      <td><span class="badge ${badgeClass}">${badgeLabel}</span></td>
      <td>${item.notes || "-"}</td>
    `;
    tbody.appendChild(row);
  }

  document.getElementById("crawl-prev").disabled = data.page <= 1;
  document.getElementById("crawl-next").disabled =
    data.total_pages === 0 || data.page >= data.total_pages;
}

document.getElementById("crawl-prev").addEventListener("click", () => {
  if (crawlState.page > 1) loadCrawlRuns(crawlState.page - 1);
});

document.getElementById("crawl-next").addEventListener("click", () => {
  if (crawlState.page < crawlState.totalPages) loadCrawlRuns(crawlState.page + 1);
});

loadCrawlRuns(1);
"""
    return _admin_layout(
        title="Hiring Radar Admin Crawl Runs",
        active_nav="crawl-runs",
        body_html=body,
        script=script,
    )


@router.get("/admin/notification-runs", response_class=HTMLResponse)
def admin_notification_runs_page() -> HTMLResponse:
    body = """
<div class="topbar">
  <div>
    <h1 style="margin:0 0 6px;">Notification Runs</h1>
    <div id="identity" class="meta">Checking session…</div>
  </div>
  <button onclick="logoutAdmin()">Log out</button>
</div>

<div class="card">
  <div class="filters">
    <input id="notification_type" placeholder="Notification type">
    <input id="notification_status" placeholder="Status">
    <select id="notification_page_size">
      <option value="10">10 rows</option>
      <option value="25" selected>25 rows</option>
      <option value="50">50 rows</option>
    </select>
    <button onclick="loadNotificationRuns(1)">Apply Filters</button>
  </div>

  <div class="meta" id="notification-meta">Loading…</div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Type</th>
          <th>Status</th>
          <th>Started</th>
          <th>Recipients</th>
          <th>New Jobs</th>
          <th>Subject</th>
        </tr>
      </thead>
      <tbody id="notification-table-body"></tbody>
    </table>
  </div>

  <div class="pager">
    <button class="secondary" id="notification-prev">Previous</button>
    <span id="notification-page">Page -</span>
    <button class="secondary" id="notification-next">Next</button>
  </div>
</div>
"""
    script = """
let notificationState = { page: 1, totalPages: 0 };

function notificationFilters() {
  const params = new URLSearchParams();
  const notificationType = document.getElementById("notification_type").value.trim();
  const status = document.getElementById("notification_status").value.trim();
  const pageSize = document.getElementById("notification_page_size").value;

  if (notificationType) params.set("notification_type", notificationType);
  if (status) params.set("status", status);
  params.set("page_size", pageSize);

  return params;
}

async function loadNotificationRuns(page) {
  const me = await ensureAdminSession();
  if (!me) return;
  document.getElementById("identity").textContent = `Signed in as ${me.email}`;

  const params = notificationFilters();
  params.set("page", page);

  const response = await fetch(`/api/admin/notification-runs?${params.toString()}`, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    document.getElementById("notification-meta").textContent = "Failed to load notification runs.";
    return;
  }

  const data = await response.json();
  notificationState.page = data.page;
  notificationState.totalPages = data.total_pages;

  document.getElementById("notification-meta").textContent =
    `Showing ${data.items.length} of ${data.total_items} notification runs`;
  document.getElementById("notification-page").textContent =
    `Page ${data.page} / ${data.total_pages || 1}`;

  const tbody = document.getElementById("notification-table-body");
  tbody.innerHTML = "";
  for (const item of data.items) {
    const badgeClass = item.status === "sent" ? "success" : item.status === "failed" ? "danger" : "warning";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.id}</td>
      <td><code class="inline">${item.notification_type}</code></td>
      <td><span class="badge ${badgeClass}">${item.status}</span></td>
      <td>${item.started_at}</td>
      <td>${item.recipient_count}</td>
      <td>${item.new_jobs_count}</td>
      <td>${item.subject || "-"}</td>
    `;
    tbody.appendChild(row);
  }

  document.getElementById("notification-prev").disabled = data.page <= 1;
  document.getElementById("notification-next").disabled =
    data.total_pages === 0 || data.page >= data.total_pages;
}

document.getElementById("notification-prev").addEventListener("click", () => {
  if (notificationState.page > 1) loadNotificationRuns(notificationState.page - 1);
});

document.getElementById("notification-next").addEventListener("click", () => {
  if (notificationState.page < notificationState.totalPages) loadNotificationRuns(notificationState.page + 1);
});

loadNotificationRuns(1);
"""
    return _admin_layout(
        title="Hiring Radar Admin Notification Runs",
        active_nav="notification-runs",
        body_html=body,
        script=script,
    )


@router.get("/admin/subscribers", response_class=HTMLResponse)
def admin_subscribers_page() -> HTMLResponse:
    body = """
<div class="topbar">
  <div>
    <h1 style="margin:0 0 6px;">Subscribers</h1>
    <div id="identity" class="meta">Checking session…</div>
  </div>
  <button onclick="logoutAdmin()">Log out</button>
</div>

<div class="card">
  <div class="filters">
    <input id="subscriber_query" placeholder="Search email or full name">
    <select id="subscriber_is_active">
      <option value="">All active states</option>
      <option value="true">Active</option>
      <option value="false">Inactive</option>
    </select>
    <select id="subscriber_digest_enabled">
      <option value="">All digest states</option>
      <option value="true">Digest enabled</option>
      <option value="false">Digest disabled</option>
    </select>
    <select id="subscriber_page_size">
      <option value="10">10 rows</option>
      <option value="25" selected>25 rows</option>
      <option value="50">50 rows</option>
    </select>
    <button onclick="loadSubscribers(1)">Apply Filters</button>
  </div>

  <div class="meta" id="subscriber-meta">Loading…</div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Email</th>
          <th>Name</th>
          <th>Active</th>
          <th>Digest</th>
          <th>Updated</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="subscriber-table-body"></tbody>
    </table>
  </div>

  <div class="pager">
    <button class="secondary" id="subscriber-prev">Previous</button>
    <span id="subscriber-page">Page -</span>
    <button class="secondary" id="subscriber-next">Next</button>
  </div>
</div>
"""
    script = """
let subscriberState = { page: 1, totalPages: 0 };

function subscriberFilters() {
  const params = new URLSearchParams();
  const emailQuery = document.getElementById("subscriber_query").value.trim();
  const isActive = document.getElementById("subscriber_is_active").value;
  const digestEnabled = document.getElementById("subscriber_digest_enabled").value;
  const pageSize = document.getElementById("subscriber_page_size").value;

  if (emailQuery) params.set("email_query", emailQuery);
  if (isActive) params.set("is_active", isActive);
  if (digestEnabled) params.set("digest_enabled", digestEnabled);
  params.set("page_size", pageSize);

  return params;
}

async function patchSubscriber(subscriberId, payload) {
  const response = await fetch(`/api/admin/subscribers/${subscriberId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "Update failed." }));
    alert(data.detail || "Update failed.");
    return false;
  }

  return true;
}

async function toggleSubscriberActive(subscriberId, nextValue) {
  const ok = await patchSubscriber(subscriberId, { is_active: nextValue });
  if (ok) loadSubscribers(subscriberState.page);
}

async function toggleSubscriberDigest(subscriberId, nextValue) {
  const ok = await patchSubscriber(subscriberId, { digest_enabled: nextValue });
  if (ok) loadSubscribers(subscriberState.page);
}

async function editSubscriberName(subscriberId, currentName) {
  const nextName = window.prompt("Enter full name (leave empty to clear):", currentName || "");
  if (nextName === null) return;

  const ok = await patchSubscriber(subscriberId, {
    full_name: nextName.trim() ? nextName.trim() : null,
  });
  if (ok) loadSubscribers(subscriberState.page);
}

async function loadSubscribers(page) {
  const me = await ensureAdminSession();
  if (!me) return;
  document.getElementById("identity").textContent = `Signed in as ${me.email}`;

  const params = subscriberFilters();
  params.set("page", page);

  const response = await fetch(`/api/admin/subscribers?${params.toString()}`, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    document.getElementById("subscriber-meta").textContent = "Failed to load subscribers.";
    return;
  }

  const data = await response.json();
  subscriberState.page = data.page;
  subscriberState.totalPages = data.total_pages;

  document.getElementById("subscriber-meta").textContent =
    `Showing ${data.items.length} of ${data.total_items} subscribers`;
  document.getElementById("subscriber-page").textContent =
    `Page ${data.page} / ${data.total_pages || 1}`;

  const tbody = document.getElementById("subscriber-table-body");
  tbody.innerHTML = "";
  for (const item of data.items) {
    const activeBadge = item.is_active ? "success" : "warning";
    const digestBadge = item.digest_enabled ? "success" : "warning";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.id}</td>
      <td>${item.email}</td>
      <td>${item.full_name || "-"}</td>
      <td><span class="badge ${activeBadge}">${item.is_active ? "Active" : "Inactive"}</span></td>
      <td><span class="badge ${digestBadge}">${item.digest_enabled ? "Enabled" : "Disabled"}</span></td>
      <td>${item.updated_at || "-"}</td>
      <td>
        <div class="actions">
          <button class="small secondary" onclick='editSubscriberName(${item.id}, ${JSON.stringify(item.full_name)})'>Edit Name</button>
          <button class="small" onclick="toggleSubscriberActive(${item.id}, ${!item.is_active})">
            ${item.is_active ? "Disable" : "Enable"}
          </button>
          <button class="small" onclick="toggleSubscriberDigest(${item.id}, ${!item.digest_enabled})">
            ${item.digest_enabled ? "Disable Digest" : "Enable Digest"}
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  }

  document.getElementById("subscriber-prev").disabled = data.page <= 1;
  document.getElementById("subscriber-next").disabled =
    data.total_pages === 0 || data.page >= data.total_pages;
}

document.getElementById("subscriber-prev").addEventListener("click", () => {
  if (subscriberState.page > 1) loadSubscribers(subscriberState.page - 1);
});

document.getElementById("subscriber-next").addEventListener("click", () => {
  if (subscriberState.page < subscriberState.totalPages) loadSubscribers(subscriberState.page + 1);
});

loadSubscribers(1);
"""
    return _admin_layout(
        title="Hiring Radar Admin Subscribers",
        active_nav="subscribers",
        body_html=body,
        script=script,
    )


@router.get("/admin/settings", response_class=HTMLResponse)
def admin_settings_page() -> HTMLResponse:
    body = """
<div class="topbar">
  <div>
    <h1 style="margin:0 0 6px;">Settings</h1>
    <div id="identity" class="meta">Checking session…</div>
  </div>
  <button onclick="logoutAdmin()">Log out</button>
</div>

<div class="card" style="margin-bottom: 16px;">
  <div class="meta" id="settings-meta">Loading settings…</div>
  <div id="save-status" class="meta"></div>

  <div class="form-grid">
    <div>
      <div class="form-row">
        <label for="include_keywords"><strong>Include keywords</strong></label>
        <textarea id="include_keywords" placeholder="One keyword per line"></textarea>
      </div>

      <div class="form-row">
        <label for="exclude_keywords"><strong>Exclude keywords</strong></label>
        <textarea id="exclude_keywords" placeholder="One keyword per line"></textarea>
      </div>
    </div>

    <div>
      <div class="form-row">
        <strong>Match fields</strong>
        <div class="checkbox-row" style="margin-top: 10px;">
          <label><input type="checkbox" id="match_title"> Title</label>
          <label><input type="checkbox" id="match_location"> Location</label>
          <label><input type="checkbox" id="match_company_name"> Company name</label>
        </div>
      </div>

      <div class="form-row">
        <strong>Notification policy</strong>
        <div class="checkbox-row" style="margin-top: 10px;">
          <label>
            <input type="checkbox" id="apply_keyword_filter_to_digest">
            Apply keyword filter to digest by default
          </label>
        </div>
      </div>

      <div class="form-row">
        <strong>Preview options</strong>
        <div class="checkbox-row" style="margin-top: 10px;">
          <label><input type="checkbox" id="preview_active_only" checked> Active jobs only</label>
          <label>Sample limit <input type="number" id="preview_sample_limit" min="1" max="50" value="5" style="width: 90px;"></label>
        </div>
      </div>

      <div class="actions">
        <button onclick="previewSettings()">Preview Filter</button>
        <button class="secondary" onclick="saveSettings()">Save Settings</button>
      </div>
    </div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2 style="margin-top:0;">Preview Summary</h2>
    <div class="meta" id="preview-summary">No preview run yet.</div>
  </div>
  <div class="card">
    <h2 style="margin-top:0;">Current Settings</h2>
    <pre id="current-settings-json" style="background:#0f172a;color:#e2e8f0;border-radius:20px;padding:20px;overflow:auto;">Loading…</pre>
  </div>
</div>

<div class="preview-columns" style="margin-top: 16px;">
  <div class="card">
    <h2 style="margin-top:0;">Passed Samples</h2>
    <div id="preview-passed" class="preview-list">No preview run yet.</div>
  </div>
  <div class="card">
    <h2 style="margin-top:0;">Rejected Samples</h2>
    <div id="preview-rejected" class="preview-list">No preview run yet.</div>
  </div>
</div>
"""
    script = """
function splitKeywords(value) {
  return value
    .split(/\\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function settingsPayload() {
  return {
    keyword_filter: {
      include_keywords: splitKeywords(document.getElementById("include_keywords").value),
      exclude_keywords: splitKeywords(document.getElementById("exclude_keywords").value),
      match_title: document.getElementById("match_title").checked,
      match_location: document.getElementById("match_location").checked,
      match_company_name: document.getElementById("match_company_name").checked,
    },
    notifications: {
      apply_keyword_filter_to_digest:
        document.getElementById("apply_keyword_filter_to_digest").checked,
    },
  };
}

function previewPayload() {
  return {
    keyword_filter: settingsPayload().keyword_filter,
    active_only: document.getElementById("preview_active_only").checked,
    sample_limit: Number(document.getElementById("preview_sample_limit").value || "5"),
  };
}

function populateSettings(data) {
  document.getElementById("settings-meta").textContent =
    `Settings source: ${data.settings_path}`;

  document.getElementById("include_keywords").value =
    data.keyword_filter.include_keywords.join("\\n");
  document.getElementById("exclude_keywords").value =
    data.keyword_filter.exclude_keywords.join("\\n");
  document.getElementById("match_title").checked = data.keyword_filter.match_title;
  document.getElementById("match_location").checked = data.keyword_filter.match_location;
  document.getElementById("match_company_name").checked = data.keyword_filter.match_company_name;
  document.getElementById("apply_keyword_filter_to_digest").checked =
    data.notifications.apply_keyword_filter_to_digest;

  document.getElementById("current-settings-json").textContent =
    JSON.stringify(data, null, 2);
}

function renderPreviewList(containerId, samples) {
  const container = document.getElementById(containerId);

  if (!samples.length) {
    container.textContent = "No samples.";
    return;
  }

  container.innerHTML = "";
  for (const sample of samples) {
    const node = document.createElement("div");
    node.className = "preview-item";

    const includeMatches = sample.include_matches.length
      ? sample.include_matches.map((m) => `${m.field_name}:${m.keyword}`).join(", ")
      : "-";
    const excludeMatches = sample.exclude_matches.length
      ? sample.exclude_matches.map((m) => `${m.field_name}:${m.keyword}`).join(", ")
      : "-";

    node.innerHTML = `
      <div><strong>${sample.title}</strong></div>
      <div>${sample.company_name} | ${sample.location || "-"}</div>
      <div>include: ${includeMatches}</div>
      <div>exclude: ${excludeMatches}</div>
      <div><a href="${sample.canonical_url}" target="_blank" rel="noreferrer">Open</a></div>
    `;

    container.appendChild(node);
  }
}

async function loadSettings() {
  const me = await ensureAdminSession();
  if (!me) return;

  document.getElementById("identity").textContent = `Signed in as ${me.email}`;

  const response = await fetch("/api/admin/settings", {
    credentials: "same-origin",
  });
  if (!response.ok) {
    document.getElementById("settings-meta").textContent = "Failed to load settings.";
    return;
  }

  const data = await response.json();
  populateSettings(data);
}

async function previewSettings() {
  document.getElementById("save-status").textContent = "";

  const response = await fetch("/api/admin/settings/filter-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(previewPayload()),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "Preview failed." }));
    document.getElementById("preview-summary").innerHTML =
      `<span class="status-error">${data.detail || "Preview failed."}</span>`;
    return;
  }

  const data = await response.json();
  document.getElementById("preview-summary").innerHTML = `
    <div>Scope: <strong>${data.jobs_scope}</strong></div>
    <div>Total jobs: <strong>${data.total_jobs}</strong></div>
    <div>Passed: <strong>${data.passed_jobs}</strong></div>
    <div>Rejected: <strong>${data.rejected_jobs}</strong></div>
    <div>Filter enabled: <strong>${data.filter_enabled}</strong></div>
    <div>Active fields: <strong>${data.active_fields.join(", ") || "-"}</strong></div>
  `;

  renderPreviewList("preview-passed", data.passed_samples);
  renderPreviewList("preview-rejected", data.rejected_samples);
}

async function saveSettings() {
  const response = await fetch("/api/admin/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(settingsPayload()),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "Save failed." }));
    document.getElementById("save-status").innerHTML =
      `<span class="status-error">${data.detail || "Save failed."}</span>`;
    return;
  }

  const data = await response.json();
  document.getElementById("save-status").innerHTML =
    `<span class="status-ok">Settings saved successfully.</span>`;
  populateSettings(data);
}

loadSettings();
"""
    return _admin_layout(
        title="Hiring Radar Admin Settings",
        active_nav="settings",
        body_html=body,
        script=script,
    )