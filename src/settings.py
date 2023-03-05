import sys
import os
# 第三方库
import sentry_sdk
# 项目库
from utils.config import config
from loguru import logger as log


SENTRY_DSN = config('SENTRY_DSN', mandatory=False)
sentry_sdk.init(SENTRY_DSN)

# Log
LOG_LEVEL = config('LOG_LEVEL')
# 初始化日志
log.remove()    # workaround: https://github.com/Delgan/loguru/issues/208
log_console_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: <8}</level> | <level>{message}</level>"
log.add(sys.stderr, level=LOG_LEVEL, format=log_console_format, colorize=False)
log.info(f'Log parameter. Level: {LOG_LEVEL}')
