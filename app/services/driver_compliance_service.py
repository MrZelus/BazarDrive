from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.db import repository
from app.models.feed import (
    DRIVER_MAX_UNPAID_FINES,
    DRIVER_MIN_EXPERIENCE_YEARS,
    DRIVER_REQUIRED_CATEGORY,
    REQUIRED_DRIVER_DOCUMENT_TYPES,
)

EXPIRING_SOON_DAYS = 30


@dataclass
class ComplianceResult:
    status: str
    reason: str
    section_status: str
    eligibility_status: str
    missing_required_fields: list[str]
    ineligibility_reasons: list[str]
    missing_documents: list[str]
    expired_documents: list[str]
    expiring_documents: list[str]
    can_accept_orders: bool
    can_go_online: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "section_status": self.section_status,
            "eligibility_status": self.eligibility_status,
            "missing_required_fields": self.missing_required_fields,
            "ineligibility_reasons": self.ineligibility_reasons,
            "missing_documents": self.missing_documents,
            "expired_documents": self.expired_documents,
            "expiring_documents": self.expiring_documents,
            "can_accept_orders": self.can_accept_orders,
            "can_go_online": self.can_go_online,
        }


class DriverComplianceService:
    @staticmethod
    def evaluate(profile_id: str) -> ComplianceResult:
        profile = repository.get_driver_compliance_profile(profile_id)
        if not profile:
            result = ComplianceResult(
                status="profile_incomplete",
                reason="Профиль допуска водителя не заполнен",
                section_status="incomplete",
                eligibility_status="restricted",
                missing_required_fields=["profile"],
                ineligibility_reasons=["Профиль допуска водителя не заполнен"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        missing_required_fields = []
        for field_name in ("last_name", "first_name", "middle_name", "phone", "email", "employment_type"):
            if not str(profile.get(field_name) or "").strip():
                missing_required_fields.append(field_name)

        core_required_fields = {"last_name", "first_name", "phone"}
        if any(field in core_required_fields for field in missing_required_fields):
            result = ComplianceResult(
                status="profile_incomplete",
                reason="Не заполнены обязательные личные данные",
                section_status="incomplete",
                eligibility_status="restricted",
                missing_required_fields=missing_required_fields,
                ineligibility_reasons=["Не заполнены обязательные личные данные"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        category_value = str(profile.get("driver_license_category") or "").strip().upper()
        if DRIVER_REQUIRED_CATEGORY not in set(category_value):
            result = ComplianceResult(
                status="restricted",
                reason="Требуется водительское удостоверение категории B",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Требуется водительское удостоверение категории B"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        experience = int(profile.get("driving_experience_years") or 0)
        if experience < DRIVER_MIN_EXPERIENCE_YEARS:
            result = ComplianceResult(
                status="restricted",
                reason="Стаж вождения менее 3 лет",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Стаж вождения менее 3 лет"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        if int(profile.get("has_medical_contraindications") or 0) == 1:
            result = ComplianceResult(
                status="restricted",
                reason="Есть медицинские противопоказания",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Есть медицинские противопоказания"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        if int(profile.get("criminal_record_cleared") or 0) != 1:
            result = ComplianceResult(
                status="restricted",
                reason="Не пройдена проверка сведений о судимости",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Не пройдена проверка сведений о судимости"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        if int(profile.get("unpaid_fines_count") or 0) > DRIVER_MAX_UNPAID_FINES:
            result = ComplianceResult(
                status="restricted",
                reason="Более 3 неоплаченных штрафов",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Более 3 неоплаченных штрафов"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        employment_type = str(profile.get("employment_type") or "").strip()
        if employment_type == "individual_entrepreneur":
            if not profile.get("inn") or not profile.get("ogrnip") or not profile.get("activity_region"):
                result = ComplianceResult(
                    status="profile_incomplete",
                    reason="Не заполнены обязательные данные ИП",
                    section_status="incomplete",
                    eligibility_status="restricted",
                    missing_required_fields=["inn", "ogrnip", "activity_region"],
                    ineligibility_reasons=["Не заполнены обязательные данные ИП"],
                    missing_documents=[],
                    expired_documents=[],
                    expiring_documents=[],
                    can_accept_orders=False,
                    can_go_online=False,
                )
                repository.update_driver_compliance_status(profile_id, result.status, result.reason)
                return result

        if not profile.get("vehicle_make") or not profile.get("vehicle_model") or not profile.get("vehicle_license_plate"):
            result = ComplianceResult(
                status="profile_incomplete",
                reason="Не заполнены сведения об автомобиле",
                section_status="incomplete",
                eligibility_status="restricted",
                missing_required_fields=["vehicle_make", "vehicle_model", "vehicle_license_plate"],
                ineligibility_reasons=["Не заполнены сведения об автомобиле"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=[],
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        today = date.today()
        expiring_border = today + timedelta(days=EXPIRING_SOON_DAYS)

        missing_documents: list[str] = []
        expired_documents: list[str] = []
        expiring_documents: list[str] = []

        documents = {doc["type"]: doc for doc in repository.list_driver_documents(profile_id)}

        for doc_type in REQUIRED_DRIVER_DOCUMENT_TYPES:
            doc = documents.get(doc_type)
            if not doc:
                missing_documents.append(doc_type)
                continue

            status = str(doc.get("status") or "").strip()

            if status == "checking":
                result = ComplianceResult(
                    status="docs_under_review",
                    reason=f"Документ {doc_type} находится на проверке",
                    section_status="incomplete",
                    eligibility_status="restricted",
                    missing_required_fields=[],
                    ineligibility_reasons=[f"Документ {doc_type} находится на проверке"],
                    missing_documents=[],
                    expired_documents=[],
                    expiring_documents=[],
                    can_accept_orders=False,
                    can_go_online=False,
                )
                repository.update_driver_compliance_status(profile_id, result.status, result.reason)
                return result

            if status == "rejected":
                missing_documents.append(doc_type)
                continue

            valid_until = str(doc.get("valid_until") or "").strip()
            if valid_until:
                try:
                    valid_until_date = date.fromisoformat(valid_until[:10])
                    if valid_until_date < today:
                        expired_documents.append(doc_type)
                        continue
                    if valid_until_date <= expiring_border:
                        expiring_documents.append(doc_type)
                except ValueError:
                    pass

            if status not in {"approved"}:
                missing_documents.append(doc_type)

        if missing_documents:
            result = ComplianceResult(
                status="profile_incomplete",
                reason="Отсутствуют или не подтверждены обязательные документы",
                section_status="incomplete",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Отсутствуют или не подтверждены обязательные документы"],
                missing_documents=missing_documents,
                expired_documents=expired_documents,
                expiring_documents=expiring_documents,
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        if expired_documents:
            result = ComplianceResult(
                status="expired_documents",
                reason="Есть просроченные документы",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Есть просроченные документы"],
                missing_documents=[],
                expired_documents=expired_documents,
                expiring_documents=expiring_documents,
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        active_waybill = repository.get_active_waybill(profile_id)
        if not active_waybill:
            result = ComplianceResult(
                status="waybill_required",
                reason="Не открыт путевой лист на текущую смену",
                section_status="filled",
                eligibility_status="restricted",
                missing_required_fields=[],
                ineligibility_reasons=["Не открыт путевой лист на текущую смену"],
                missing_documents=[],
                expired_documents=[],
                expiring_documents=expiring_documents,
                can_accept_orders=False,
                can_go_online=False,
            )
            repository.update_driver_compliance_status(profile_id, result.status, result.reason)
            return result

        result = ComplianceResult(
            status="ready_for_orders",
            reason="Водитель допущен к заказам",
            section_status="filled",
            eligibility_status="eligible",
            missing_required_fields=[],
            ineligibility_reasons=[],
            missing_documents=[],
            expired_documents=[],
            expiring_documents=expiring_documents,
            can_accept_orders=True,
            can_go_online=True,
        )
        repository.update_driver_compliance_status(profile_id, result.status, result.reason)
        return result
