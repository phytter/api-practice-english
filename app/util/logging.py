from logging import Logger, getLogger


def get_logger(name: str) -> Logger:
    return getLogger(name)
