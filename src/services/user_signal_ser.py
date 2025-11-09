from abc import ABC, abstractmethod
from enum import Enum

from src.core.logger import logger
from src.services import authentication, utils


class UserSignalEventType(Enum):
    ON_REGISTRATION = "ON_REGISTRATION"
    ON_COMPLETE_REGISTRATION = "ON_COMPLETE_REGISTRATION"


class BaseUserSignal(ABC):
    @abstractmethod
    async def run(self, *args, **kwargs):
        raise NotImplemented


class OnWelcomeUserEvent(BaseUserSignal):
    async def run(self, *args, **kwargs):
        logger.info("Welcome to ...")

        user_id = kwargs.get("user_id")
        assert user_id, "requires user_id"


class OnIntroduction(BaseUserSignal):
    async def run(self, *args, **kwargs):
        logger.info("Introduction usage ...")

        user_id = kwargs.get("user_id")
        assert user_id, "requires user_id"


class OnRegisterConfirmEvent(BaseUserSignal):
    async def run(self, **kwargs):
        logger.info("Please click the link below to verify your registration")
        user_id = kwargs.get("user_id")

        assert user_id, "requires user_id"

        token = await authentication.create_confirm_token(user_id)
        url = utils.build_url(
            query_params=dict(token=token),
            url="auth/registration/confirmation",
        )
        logger.info(url)


class UserSignalHandler:
    event = {
        UserSignalEventType.ON_REGISTRATION.value: [
            OnRegisterConfirmEvent,
        ],
        UserSignalEventType.ON_COMPLETE_REGISTRATION.value: [
            OnWelcomeUserEvent,
            OnIntroduction,
        ],
    }

    async def run(self, event: UserSignalEventType, *args, **kwargs):
        hooks = self.event[event.value]

        for hook in hooks:
            handler: BaseUserSignal = hook()
            await handler.run(**kwargs)
