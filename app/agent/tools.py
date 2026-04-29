"""
Agent tools — functions the LangChain agent can call via Function Calling.

Each tool is a plain Python function decorated with @tool.  The agent
selects which tool to invoke based on the user's question and the
function docstrings (which act as tool descriptions for the LLM).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

# ──────────────────────────────────────────────
# Data path — resolved relative to this file
# ──────────────────────────────────────────────
_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "mock_data.json"


def _load_data() -> dict:
    """Load the mock payroll JSON file and return it as a dict."""
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════
#  Tool 1 — List all employees
# ═══════════════════════════════════════════════
@tool
def get_all_employees() -> str:
    """
    استرجاع قائمة جميع الموظفين مع بياناتهم الأساسية.
    Retrieve a list of all employees with their basic information
    including name, ID, department, job title, and status.
    Use this tool when the user asks for an employee list or directory.
    """
    data = _load_data()
    employees = data.get("employees", [])

    results = []
    for emp in employees:
        results.append({
            "id": emp["id"],
            "name_ar": emp["name_ar"],
            "name_en": emp["name_en"],
            "department": emp["department"],
            "job_title": emp["job_title"],
            "nationality": emp["nationality"],
            "status": emp["status"],
        })

    return json.dumps(results, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
#  Tool 2 — Get a single employee's details
# ═══════════════════════════════════════════════
@tool
def get_employee_by_id(employee_id: str) -> str:
    """
    استرجاع بيانات موظف محدد عن طريق رقمه (مثال: EMP-001).
    Retrieve full details of a specific employee by their ID (e.g. EMP-001).
    Includes personal info, salary breakdown, GOSI and Mudad status, and leave balance.
    Use this tool when the user asks about a specific employee.
    """
    data = _load_data()
    employees = data.get("employees", [])

    for emp in employees:
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(emp, ensure_ascii=False, indent=2)

    return json.dumps(
        {"error": f"لم يتم العثور على موظف بالرقم {employee_id}"},
        ensure_ascii=False,
    )


# ═══════════════════════════════════════════════
#  Tool 3 — Search employees by name
# ═══════════════════════════════════════════════
@tool
def search_employee_by_name(name: str) -> str:
    """
    البحث عن موظف بالاسم (عربي أو إنجليزي).
    Search for employees by name (Arabic or English, partial match supported).
    Use this tool when the user mentions an employee name.
    """
    data = _load_data()
    employees = data.get("employees", [])
    query = name.lower().strip()

    matches = [
        emp for emp in employees
        if query in emp["name_ar"].lower() or query in emp["name_en"].lower()
    ]

    if not matches:
        return json.dumps(
            {"error": f"لم يتم العثور على موظف بالاسم: {name}"},
            ensure_ascii=False,
        )

    return json.dumps(matches, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
#  Tool 4 — Get employee salary details
# ═══════════════════════════════════════════════
@tool
def get_employee_salary(employee_id: str) -> str:
    """
    استرجاع تفاصيل راتب موظف محدد (الأساسي، البدلات، الاستقطاعات، الصافي).
    Retrieve detailed salary breakdown for a specific employee by ID.
    Includes basic salary, allowances, GOSI deductions, and net pay.
    Use this tool when the user asks about salary, pay, or compensation.
    """
    data = _load_data()
    employees = data.get("employees", [])

    for emp in employees:
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(
                {
                    "employee_id": emp["id"],
                    "name_ar": emp["name_ar"],
                    "name_en": emp["name_en"],
                    "salary": emp["salary"],
                },
                ensure_ascii=False,
                indent=2,
            )

    return json.dumps(
        {"error": f"لم يتم العثور على موظف بالرقم {employee_id}"},
        ensure_ascii=False,
    )


# ═══════════════════════════════════════════════
#  Tool 5 — Monthly payroll summary
# ═══════════════════════════════════════════════
@tool
def get_payroll_summary() -> str:
    """
    استرجاع ملخص مسيّر الرواتب الشهري (إجمالي الرواتب، الاستقطاعات، حالة التحويل).
    Retrieve the monthly payroll summary including total salaries,
    GOSI contributions, WPS transfer status, and Mudad submission status.
    Use this tool when the user asks about the overall payroll, totals, or monthly report.
    """
    data = _load_data()
    summary = data.get("payroll_summary", {})
    company = data.get("company", {})

    return json.dumps(
        {"company": company, "payroll_summary": summary},
        ensure_ascii=False,
        indent=2,
    )


# ═══════════════════════════════════════════════
#  Tool 6 — Company information
# ═══════════════════════════════════════════════
@tool
def get_company_info() -> str:
    """
    استرجاع معلومات الشركة (الاسم، السجل التجاري، رقم التأمينات، معرّف مُدد).
    Retrieve company information including name, commercial registration,
    GOSI subscription number, and Mudad establishment ID.
    Use this tool when the user asks about the company or establishment details.
    """
    data = _load_data()
    company = data.get("company", {})
    return json.dumps(company, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
#  Tool 7 — Filter employees by department
# ═══════════════════════════════════════════════
@tool
def get_employees_by_department(department: str) -> str:
    """
    استرجاع قائمة الموظفين حسب القسم (مثال: الهندسة، المالية، الموارد البشرية).
    Retrieve employees filtered by department name (Arabic or English).
    Use this tool when the user asks about employees in a specific department.
    """
    data = _load_data()
    employees = data.get("employees", [])
    query = department.lower().strip()

    matches = [
        emp for emp in employees
        if query in emp["department"].lower()
        or query in emp.get("department_en", "").lower()
    ]

    if not matches:
        return json.dumps(
            {"error": f"لم يتم العثور على موظفين في قسم: {department}"},
            ensure_ascii=False,
        )

    results = []
    for emp in matches:
        results.append({
            "id": emp["id"],
            "name_ar": emp["name_ar"],
            "name_en": emp["name_en"],
            "job_title": emp["job_title"],
            "salary_net": emp["salary"]["net_salary"],
        })

    return json.dumps(results, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# Exported list used by the agent executor
# ──────────────────────────────────────────────
ALL_TOOLS = [
    get_all_employees,
    get_employee_by_id,
    search_employee_by_name,
    get_employee_salary,
    get_payroll_summary,
    get_company_info,
    get_employees_by_department,
]
