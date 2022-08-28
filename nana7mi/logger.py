import logging


class Logger:
    # 日志
    __logger = logging.getLogger('Nana7mi')
    __logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", '%H:%M:%S'))
    __logger.addHandler(handler)

    def info(self, msg: str, id: str = ''):
        self.__logger.info(f'[{id}] {msg}' if id else msg)

    def error(self, msg: str, id: str = ''):
        self.__logger.error(f'[{id}] {msg}' if id else msg)

    def debug(self, msg: str, id: str = ''):
        self.__logger.debug(f'[{id}] {msg}' if id else msg)

log = Logger()