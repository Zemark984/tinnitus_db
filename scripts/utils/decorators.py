import time
from .logging import log
from ..utils.exceptions import NCBIAPITemporaryBlock
from .config import args

def retry_on_fail(max_retries=None, delay=None):
    """Декоратор для повторных попыток с обработкой специфических ошибок NCBI"""
    if max_retries is None:
        max_retries = args.ncbi_max_retries
    if delay is None:
        delay = args.ncbi_retry_delay

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except NCBIAPITemporaryBlock as e:
                    wait_time = delay * (2 ** attempt)
                    log(f"NCBI block detected: {str(e)}. Waiting {wait_time} seconds before retry {attempt+1}/{max_retries}")
                    time.sleep(wait_time)
                except Exception as e:
                    last_exception = e
                    log(f"Retry {attempt+1}/{max_retries} for {func.__name__}: {str(e)}")
                    time.sleep(delay * (2 ** attempt))

            if last_exception:
                raise Exception(f"Failed after {max_retries} retries: {str(last_exception)}")
            else:
                raise Exception(f"Failed after {max_retries} retries due to NCBI blocking")
        return wrapper
    return decorator
