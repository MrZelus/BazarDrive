from __future__ import annotations

from app.models.driver_enums import EligibilityStatus, OrderStatus, ProfileStatus
from app.models.driver_error_codes import DriverErrorCode
from app.services.driver_contracts import PermissionCheckResult


class DriverPermissionsService:
    @staticmethod
    def _allow() -> PermissionCheckResult:
        return PermissionCheckResult(is_allowed=True)

    @staticmethod
    def _deny(error_code: DriverErrorCode, reason: str) -> PermissionCheckResult:
        return PermissionCheckResult(
            is_allowed=False,
            error_code=error_code.value,
            reason=reason,
        )

    @classmethod
    def can_edit_profile(
        cls,
        actor_id: str,
        owner_id: str,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        if is_admin:
            return cls._allow()
        if actor_id != owner_id:
            return cls._deny(
                DriverErrorCode.OWNERSHIP_REQUIRED,
                "Driver can edit only own profile",
            )
        return cls._allow()

    @classmethod
    def can_submit_profile_for_verification(
        cls,
        actor_id: str,
        owner_id: str,
        required_fields_complete: bool,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        ownership = cls.can_edit_profile(actor_id, owner_id, is_admin=is_admin)
        if not ownership.is_allowed:
            return ownership
        if not required_fields_complete:
            return cls._deny(
                DriverErrorCode.PERMISSION_DENIED,
                "Required fields are incomplete",
            )
        return cls._allow()

    @classmethod
    def can_upload_document(
        cls,
        actor_id: str,
        owner_id: str,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        return cls.can_edit_profile(actor_id, owner_id, is_admin=is_admin)

    @classmethod
    def can_open_trip_sheet(
        cls,
        actor_id: str,
        owner_id: str,
        eligibility_status: EligibilityStatus,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        ownership = cls.can_edit_profile(actor_id, owner_id, is_admin=is_admin)
        if not ownership.is_allowed:
            return ownership
        if eligibility_status == EligibilityStatus.BLOCKED:
            return cls._deny(
                DriverErrorCode.ELIGIBILITY_BLOCKED,
                "Eligibility is blocked",
            )
        return cls._allow()

    @classmethod
    def can_go_online(
        cls,
        actor_id: str,
        owner_id: str,
        eligibility_status: EligibilityStatus,
        profile_status: ProfileStatus,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        ownership = cls.can_edit_profile(actor_id, owner_id, is_admin=is_admin)
        if not ownership.is_allowed:
            return ownership
        if profile_status == ProfileStatus.BLOCKED:
            return cls._deny(
                DriverErrorCode.PROFILE_BLOCKED,
                "Blocked profile cannot go online",
            )
        if eligibility_status != EligibilityStatus.READY:
            return cls._deny(
                DriverErrorCode.DRIVER_NOT_ELIGIBLE,
                "Driver is not ready to go online",
            )
        return cls._allow()

    @classmethod
    def can_accept_order(
        cls,
        actor_id: str,
        owner_id: str,
        eligibility_status: EligibilityStatus,
        order_status: OrderStatus,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        if is_admin:
            return cls._allow()
        if actor_id != owner_id:
            return cls._deny(
                DriverErrorCode.OWNERSHIP_REQUIRED,
                "Driver can accept only own assigned scope/order flow",
            )
        if eligibility_status != EligibilityStatus.READY:
            return cls._deny(
                DriverErrorCode.DRIVER_NOT_ELIGIBLE,
                "Driver is not eligible to accept order",
            )
        if order_status != OrderStatus.CREATED:
            return cls._deny(
                DriverErrorCode.INVALID_ORDER_TRANSITION,
                "Only created order can be accepted",
            )
        return cls._allow()

    @classmethod
    def can_cancel_order(
        cls,
        actor_id: str,
        owner_id: str,
        order_status: OrderStatus,
        is_admin: bool = False,
    ) -> PermissionCheckResult:
        if is_admin:
            return cls._allow()
        if actor_id != owner_id:
            return cls._deny(
                DriverErrorCode.OWNERSHIP_REQUIRED,
                "Driver can cancel only own order",
            )
        if order_status in {OrderStatus.DONE, OrderStatus.CANCELED}:
            return cls._deny(
                DriverErrorCode.INVALID_ORDER_TRANSITION,
                "Finished or canceled order cannot be canceled again",
            )
        return cls._allow()
