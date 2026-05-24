from __future__ import annotations

import csv
import io
import json
import random
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse

# Ensure the project root is on the path so 'app' package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.actions.handlers import ActionHandler
from app.analytics.metrics import (
    attrition_by_age_group,
    build_kpis,
    department_attrition,
    education_attrition,
    gender_attrition,
    job_satisfaction_table,
)
from app.core.logger import ActionLogger
from app.data.sample_data import generate_employee_data

HOST = "0.0.0.0"
PORT = 8000
ROWS = 2000

LOGGER = ActionLogger(log_file=Path(__file__).resolve().parent / "logs" / "app_events.log")
HANDLER = ActionHandler(logger=LOGGER, failure_rate=0.2)
STATE_LOCK = Lock()
STATE: dict[str, Any] = {
    "data": generate_employee_data(rows=ROWS, seed=42),
}


def filter_rows(
    rows: list[dict[str, object]],
    education: str = "All",
    departments: list[str] | None = None,
    age_group: str = "All",
    gender: str = "All",
    job_role: str = "All",
) -> list[dict[str, object]]:
    selected_departments = departments or []
    filtered = rows
    if education != "All":
        filtered = [row for row in filtered if row["EducationField"] == education]
    if selected_departments:
        filtered = [row for row in filtered if str(row["Department"]) in selected_departments]
    if age_group != "All":
        def age_to_group(age):
            if age < 25: return "Under 25"
            if age < 35: return "25-34"
            if age < 45: return "35-44"
            if age < 55: return "45-54"
            return "Over 55"
        filtered = [row for row in filtered if age_to_group(int(row["Age"])) == age_group]
    if gender != "All":
        filtered = [row for row in filtered if row["Gender"] == gender]
    if job_role != "All":
        filtered = [row for row in filtered if row["JobRole"] == job_role]
    return filtered


def to_dashboard_payload(rows: list[dict[str, object]]) -> dict[str, Any]:
    return {
        "kpis": build_kpis(rows),
        "departmentAttrition": department_attrition(rows),
        "ageGroupAttrition": attrition_by_age_group(rows),
        "educationAttrition": education_attrition(rows),
        "genderAttrition": gender_attrition(rows),
        "jobSatisfaction": job_satisfaction_table(rows),
    }


def to_csv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _action_context(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "education": payload.get("education", "All"),
        "departments": payload.get("departments", []),
        "failureRate": payload.get("failureRate", 0.2),
    }


def run_action(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action", "load_dashboard"))
    context = _action_context(payload)
    failure_rate = float(payload.get("failureRate", 0.2))
    HANDLER.failure_rate = max(0.0, min(1.0, failure_rate))

    def work() -> dict[str, Any]:
        education = str(payload.get("education", "All"))
        departments = payload.get("departments", [])
        age_group = str(payload.get("ageGroup", "All"))
        gender = str(payload.get("gender", "All"))
        job_role = str(payload.get("jobRole", "All"))
        if not isinstance(departments, list):
            departments = []

        if action == "refresh_data":
            with STATE_LOCK:
                STATE["data"] = generate_employee_data(rows=ROWS, seed=random.randint(1, 10_000))
            base_rows = STATE["data"]
            filtered = filter_rows(base_rows, education=education, departments=departments, age_group=age_group, gender=gender, job_role=job_role)
            return {"message": "Data refreshed", "dashboard": to_dashboard_payload(filtered)}

        with STATE_LOCK:
            base_rows = list(STATE["data"])

        filtered = filter_rows(base_rows, education=education, departments=departments, age_group=age_group, gender=gender, job_role=job_role)
        if action == "export_csv":
            return {
                "message": "CSV prepared",
                "csv": to_csv(filtered),
                "dashboard": to_dashboard_payload(filtered),
            }

        return {
            "message": "Dashboard loaded",
            "dashboard": to_dashboard_payload(filtered),
        }

    return HANDLER.run(action=action, context=context, work=work)


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return

        if parsed.path == "/api/meta":
            with STATE_LOCK:
                data = list(STATE["data"])
            education = sorted({str(row["EducationField"]) for row in data})
            departments = sorted({str(row["Department"]) for row in data})
            genders = sorted({str(row["Gender"]) for row in data})
            job_roles = sorted({str(row["JobRole"]) for row in data})
            # Age groups as in the dashboard
            age_groups = ["All", "Under 25", "25-34", "35-44", "45-54", "Over 55"]
            self._send_json({
                "education": ["All"] + education,
                "departments": departments,
                "genders": ["All"] + genders,
                "jobRoles": ["All"] + job_roles,
                "ageGroups": age_groups
            })
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/action":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(raw.decode("utf-8"))
            result = run_action(payload)
            self._send_json({"ok": True, **result})
        except Exception as exc:  # noqa: BLE001 - report deliberate random failures
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args: object) -> None:
        # Keep terminal output clean; action logs go to logs/app_events.log.
        return

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>HR Attrition Analytics Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    body { margin: 0; padding: 32px; font-family: Arial, sans-serif; background: #0f1c2e; color: #f2f5fb; }
    h1 { margin: 0 0 18px; font-size: 2.1rem; }
    .status { min-height: 32px; margin-bottom: 18px; color: #f0c36a; font-size: 18px; }

    /* Toolbar: single horizontal row */
    .toolbar {
      display: flex !important;
      flex-direction: row !important;
      flex-wrap: nowrap !important;
      align-items: flex-end;
      gap: 12px;
      padding: 14px 20px;
      margin-bottom: 24px;
      background: #1d2f4d;
      border-radius: 12px;
      overflow-x: auto;
    }
    .toolbar .filter-group {
      display: flex;
      flex-direction: column;
      flex: 1 1 0;
      min-width: 0;
    }
    .toolbar .filter-group label {
      font-size: 12px;
      color: #a7bfdc;
      margin-bottom: 4px;
      padding: 0;
      white-space: nowrap;
    }
    .toolbar .filter-group select {
      width: auto;
      min-width: 100px;
      padding: 8px 10px;
      font-size: 14px;
      border-radius: 6px;
      border: 1.5px solid #35527f;
      background: #12243d;
      color: #f2f5fb;
    }
    .toolbar button {
      width: auto;
      min-width: 100px;
      padding: 8px 14px;
      font-size: 14px;
      border-radius: 6px;
      border: 1.5px solid #35527f;
      background: #12243d;
      color: #f2f5fb;
      cursor: pointer;
      white-space: nowrap;
      flex: 0 0 auto;
    }

    /* KPIs and Grid */
    .kpis, .grid { display: grid; gap: 24px; margin-bottom: 24px; }
    .kpis { grid-template-columns: repeat(5, 1fr); }
    .grid { grid-template-columns: repeat(4, 1fr); }
    .card { background: #1d2f4d; border-radius: 12px; padding: 16px; display: flex; flex-direction: column; justify-content: stretch; align-items: stretch; }
    .card > canvas { flex: 1 1 auto; width: 100% !important; height: 260px !important; display: block; }

    /* General form elements (outside toolbar) */
    select, input, button { border-radius: 8px; border: 1.5px solid #35527f; background: #12243d; color: #f2f5fb; font-size: 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 17px; }
    th, td { border-bottom: 1.5px solid #35527f; padding: 10px 12px; text-align: left; }
    @media (max-width: 900px) {
      .toolbar { flex-wrap: wrap !important; }
      .kpis, .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <h1>HR Attrition Analytics Dashboard</h1>
  <div class="status" id="status">Ready</div>
  <div class="toolbar">
    <div class="filter-group">
      <label for="education">Education Field</label>
      <select id="education"></select>
    </div>
    <div class="filter-group">
      <label for="departments">Departments</label>
      <select id="departments" multiple size="2"></select>
    </div>
    <div class="filter-group">
      <label for="ageGroup">Age Group</label>
      <select id="ageGroup"></select>
    </div>
    <div class="filter-group">
      <label for="gender">Gender</label>
      <select id="gender"></select>
    </div>
    <div class="filter-group">
      <label for="jobRole">Job Role</label>
      <select id="jobRole"></select>
    </div>
    <button id="loadBtn">Load Dashboard</button>
    <button id="refreshBtn">Refresh Data</button>
    <button id="exportBtn">Export CSV</button>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="grid">
    <div class="card"><canvas id="deptChart"></canvas></div>
    <div class="card"><canvas id="ageChart"></canvas></div>
    <div class="card"><canvas id="eduChart"></canvas></div>
    <div class="card"><canvas id="genderChart"></canvas></div>
  </div>



  <script>
    let charts = {};

    function selectedDepartments() {
      const select = document.getElementById("departments");
      return Array.from(select.selectedOptions).map(o => o.value);
    }

    function payload(action) {
      return {
        action,
        education: document.getElementById("education").value || "All",
        departments: selectedDepartments(),
        ageGroup: document.getElementById("ageGroup").value || "All",
        gender: document.getElementById("gender").value || "All",
        jobRole: document.getElementById("jobRole").value || "All",
        failureRate: 0.1
      };
    }

    async function postAction(action) {
      const status = document.getElementById("status");
      status.textContent = `Running action: ${action}...`;
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload(action))
      });
      const data = await res.json();
      if (!data.ok) {
        status.textContent = `Action failed: ${data.error}`;
        return null;
      }
      status.textContent = data.message || "Done";
      renderDashboard(data.dashboard);
      return data;
    }

    function renderKPIs(kpis) {
      const root = document.getElementById("kpis");
      root.innerHTML = "";
      Object.keys(kpis).forEach(key => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `<div style="font-size:18px;color:#a7bfdc">${key}</div><div style="font-size:38px;font-weight:700">${kpis[key]}</div>`;
        root.appendChild(card);
      });
    }

    function upsertChart(id, config) {
      if (charts[id]) charts[id].destroy();
      config.options = config.options || {};
      config.options.responsive = true;
      config.options.maintainAspectRatio = false;
      charts[id] = new Chart(document.getElementById(id), config);
    }


    function renderDashboard(d) {
      renderKPIs(d.kpis);

      upsertChart("deptChart", {
        type: "pie",
        data: {
          labels: d.departmentAttrition.map(x => x.Department),
          datasets: [{ data: d.departmentAttrition.map(x => x.Count), backgroundColor: ["#ef6f6c", "#f3a847", "#5fa8d3"] }]
        },
        options: { plugins: { title: { display: true, text: "Department Attrition" }, legend: { labels: { color: "#f2f5fb" } } } }
      });

      upsertChart("ageChart", {
        type: "bar",
        data: {
          labels: d.ageGroupAttrition.map(x => x.AgeGroup),
          datasets: [{ label: "Count", data: d.ageGroupAttrition.map(x => x.Count), backgroundColor: "#f3a847" }]
        },
        options: { plugins: { title: { display: true, text: "Attrition by Age Group" } }, scales: { x: { ticks: { color: "#f2f5fb" } }, y: { ticks: { color: "#f2f5fb" } } } }
      });

      upsertChart("eduChart", {
        type: "bar",
        data: {
          labels: d.educationAttrition.map(x => x.EducationField),
          datasets: [{ label: "Count", data: d.educationAttrition.map(x => x.Count), backgroundColor: "#67b26f" }]
        },
        options: { indexAxis: "y", plugins: { title: { display: true, text: "Attrition by Education" } }, scales: { x: { ticks: { color: "#f2f5fb" } }, y: { ticks: { color: "#f2f5fb" } } } }
      });

      upsertChart("genderChart", {
        type: "bar",
        data: {
          labels: d.genderAttrition.map(x => x.Gender),
          datasets: [{ label: "Count", data: d.genderAttrition.map(x => x.Count), backgroundColor: ["#8ecae6", "#ffb703"] }]
        },
        options: { plugins: { title: { display: true, text: "Attrition by Gender" } }, scales: { x: { ticks: { color: "#f2f5fb" } }, y: { ticks: { color: "#f2f5fb" } } } }
      });
    }

    async function loadMeta() {
      const res = await fetch("/api/meta");
      const meta = await res.json();
      const education = document.getElementById("education");
      education.innerHTML = meta.education.map(v => `<option value="${v}">${v}</option>`).join("");

      const departments = document.getElementById("departments");
      departments.innerHTML = meta.departments.map(v => `<option value="${v}" selected>${v}</option>`).join("");
      const ageGroup = document.getElementById("ageGroup");
      ageGroup.innerHTML = meta.ageGroups.map(v => `<option value="${v}\">${v}</option>`).join("");
      const gender = document.getElementById("gender");
      gender.innerHTML = meta.genders.map(v => `<option value="${v}\">${v}</option>`).join("");
      const jobRole = document.getElementById("jobRole");
      jobRole.innerHTML = meta.jobRoles.map(v => `<option value="${v}\">${v}</option>`).join("");
    }

    // Auto-refresh dashboard on filter change
    ["education", "departments", "ageGroup", "gender", "jobRole"].forEach(id => {
      document.addEventListener("DOMContentLoaded", () => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener("change", () => postAction("load_dashboard"));
        }
      });
    });

    document.getElementById("loadBtn").addEventListener("click", () => postAction("load_dashboard"));
    document.getElementById("refreshBtn").addEventListener("click", () => postAction("refresh_data"));
    document.getElementById("exportBtn").addEventListener("click", async () => {
      const result = await postAction("export_csv");
      if (!result || !result.csv) return;
      const blob = new Blob([result.csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "attrition_export.csv";
      a.click();
      URL.revokeObjectURL(url);
    });

    (async () => {
      await loadMeta();
      await postAction("load_dashboard");
    })();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    LOGGER.log(action="initialize_data", status="success", context={"rows": ROWS})
    print(f"Serving dashboard on http://{HOST}:{PORT}")
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
