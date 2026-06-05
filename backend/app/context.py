from contextvars import ContextVar


current_seller_email: ContextVar[str | None] = ContextVar("current_seller_email", default=None)


def set_current_seller_email(email: str | None):
    return current_seller_email.set(email)


def reset_current_seller_email(token):
    current_seller_email.reset(token)


def get_current_seller_email() -> str | None:
    return current_seller_email.get()
