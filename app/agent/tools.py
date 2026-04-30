"""
Agent tools — functions the LangChain agents can call via Function Calling.

Split into two tool sets:
- HR_TOOLS:       Full access for HR/Admin agent
- EMPLOYEE_TOOLS: Scoped to a single employee for self-service agent
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool

# ──────────────────────────────────────────────
# Data path — resolved relative to this file
# ──────────────────────────────────────────────
_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "mock_data.json"


def _load_data() -> dict:
    """Load the mock payroll JSON file and return it as a dict."""
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════
#  HR / ADMIN TOOLS — Full access
# ═══════════════════════════════════════════════════════════════

@tool
def get_all_employees() -> str:
    """
    استرجاع قائمة جميع الموظفين مع بياناتهم الأساسية.
    Retrieve a list of all employees with basic info.
    Use when the user asks for an employee list or directory.
    """
    data = _load_data()
    results = []
    for emp in data.get("employees", []):
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


@tool
def get_employee_by_id(employee_id: str) -> str:
    """
    استرجاع بيانات موظف محدد عن طريق رقمه (مثال: EMP-001).
    Retrieve full details of a specific employee by ID.
    Use when the user asks about a specific employee.
    """
    data = _load_data()
    for emp in data.get("employees", []):
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(emp, ensure_ascii=False, indent=2)
    return json.dumps(
        {"error": f"لم يتم العثور على موظف بالرقم {employee_id}"},
        ensure_ascii=False,
    )


@tool
def search_employee_by_name(name: str) -> str:
    """
    البحث عن موظف بالاسم (عربي أو إنجليزي).
    Search employees by name (partial match).
    """
    data = _load_data()
    query = name.lower().strip()
    matches = [
        emp for emp in data.get("employees", [])
        if query in emp["name_ar"].lower() or query in emp["name_en"].lower()
    ]
    if not matches:
        return json.dumps(
            {"error": f"لم يتم العثور على موظف بالاسم: {name}"},
            ensure_ascii=False,
        )
    return json.dumps(matches, ensure_ascii=False, indent=2)


@tool
def get_employee_salary(employee_id: str) -> str:
    """
    استرجاع تفاصيل راتب موظف محدد (الأساسي، البدلات، الاستقطاعات، الصافي).
    Retrieve salary breakdown for a specific employee by ID.
    """
    data = _load_data()
    for emp in data.get("employees", []):
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


@tool
def get_payroll_summary() -> str:
    """
    استرجاع ملخص مسيّر الرواتب الشهري.
    Retrieve monthly payroll summary (totals, GOSI, WPS, Mudad status).
    """
    data = _load_data()
    return json.dumps(
        {
            "company": data.get("company", {}),
            "payroll_summary": data.get("payroll_summary", {}),
        },
        ensure_ascii=False,
        indent=2,
    )


@tool
def get_company_info() -> str:
    """
    استرجاع معلومات الشركة.
    Retrieve company info (name, CR, GOSI number, Mudad ID).
    """
    data = _load_data()
    return json.dumps(data.get("company", {}), ensure_ascii=False, indent=2)


@tool
def get_employees_by_department(department: str) -> str:
    """
    استرجاع قائمة الموظفين حسب القسم.
    Retrieve employees filtered by department name (Arabic or English).
    """
    data = _load_data()
    query = department.lower().strip()
    matches = [
        emp for emp in data.get("employees", [])
        if query in emp["department"].lower()
        or query in emp.get("department_en", "").lower()
    ]
    if not matches:
        return json.dumps(
            {"error": f"لم يتم العثور على موظفين في قسم: {department}"},
            ensure_ascii=False,
        )
    results = [
        {
            "id": emp["id"],
            "name_ar": emp["name_ar"],
            "name_en": emp["name_en"],
            "job_title": emp["job_title"],
            "salary_net": emp["salary"]["net_salary"],
        }
        for emp in matches
    ]
    return json.dumps(results, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  EMPLOYEE SELF-SERVICE TOOLS — Scoped to one employee
# ═══════════════════════════════════════════════════════════════

@tool
def get_my_info(employee_id: str) -> str:
    """
    استرجاع بياناتي الشخصية (الاسم، القسم، المسمى الوظيفي، تاريخ التعيين).
    Retrieve the current employee's personal information.
    The employee_id is provided automatically by the system.
    """
    data = _load_data()
    for emp in data.get("employees", []):
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(
                {
                    "id": emp["id"],
                    "name_ar": emp["name_ar"],
                    "name_en": emp["name_en"],
                    "nationality": emp["nationality"],
                    "department": emp["department"],
                    "job_title": emp["job_title"],
                    "hire_date": emp["hire_date"],
                    "contract_type": emp["contract_type"],
                    "status": emp["status"],
                },
                ensure_ascii=False,
                indent=2,
            )
    return json.dumps({"error": "لم يتم العثور على بياناتك"}, ensure_ascii=False)


@tool
def get_my_salary(employee_id: str) -> str:
    """
    استرجاع تفاصيل راتبي (الأساسي، البدلات، الاستقطاعات، الصافي).
    Retrieve the current employee's salary breakdown.
    The employee_id is provided automatically by the system.
    """
    data = _load_data()
    for emp in data.get("employees", []):
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(
                {
                    "name_ar": emp["name_ar"],
                    "salary": emp["salary"],
                },
                ensure_ascii=False,
                indent=2,
            )
    return json.dumps({"error": "لم يتم العثور على بيانات راتبك"}, ensure_ascii=False)


@tool
def get_my_leave_balance(employee_id: str) -> str:
    """
    استرجاع رصيد إجازاتي المتبقي.
    Retrieve the current employee's remaining vacation balance.
    The employee_id is provided automatically by the system.
    """
    data = _load_data()
    for emp in data.get("employees", []):
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(
                {
                    "name_ar": emp["name_ar"],
                    "vacation_balance_days": emp["vacation_balance_days"],
                    "hire_date": emp["hire_date"],
                },
                ensure_ascii=False,
                indent=2,
            )
    return json.dumps({"error": "لم يتم العثور على رصيد إجازاتك"}, ensure_ascii=False)


@tool
def get_my_gosi_status(employee_id: str) -> str:
    """
    استرجاع حالة تسجيلي في التأمينات الاجتماعية ونظام مُدد.
    Retrieve the current employee's GOSI and Mudad registration status.
    The employee_id is provided automatically by the system.
    """
    data = _load_data()
    for emp in data.get("employees", []):
        if emp["id"].upper() == employee_id.upper():
            return json.dumps(
                {
                    "name_ar": emp["name_ar"],
                    "gosi_status": emp["gosi_status"],
                    "mudad_status": emp["mudad_status"],
                    "gosi_employee_deduction": emp["salary"]["gosi_employee_deduction"],
                    "gosi_employer_contribution": emp["salary"]["gosi_employer_contribution"],
                },
                ensure_ascii=False,
                indent=2,
            )
    return json.dumps({"error": "لم يتم العثور على بيانات تأميناتك"}, ensure_ascii=False)


# ──────────────────────────────────────────────
# Exported tool lists
# ──────────────────────────────────────────────
HR_TOOLS = [
    get_all_employees,
    get_employee_by_id,
    search_employee_by_name,
    get_employee_salary,
    get_payroll_summary,
    get_company_info,
    get_employees_by_department,
]

EMPLOYEE_TOOLS = [
    get_my_info,
    get_my_salary,
    get_my_leave_balance,
    get_my_gosi_status,
]
