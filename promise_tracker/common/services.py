from typing import Generic, Optional

from promise_tracker.common.types import BaseModelType
from promise_tracker.users.models import BaseUser


class BaseService(Generic[BaseModelType]):
    def create_base(self, instance: BaseModelType, performed_by: Optional[BaseUser] = None) -> BaseModelType:
        instance.created_by = performed_by
        instance.updated_by = performed_by

        instance.full_clean()
        instance.save()

        return instance

    def edit_base(self, instance: BaseModelType, updated_by: Optional[BaseUser] = None) -> BaseModelType:
        instance.updated_by = updated_by

        instance.full_clean()
        instance.save()

        return instance
