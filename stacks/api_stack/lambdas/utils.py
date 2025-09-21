import time
import random
import logging
from botocore import exceptions

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def rate_limit_exp_backoff(backoff_delay=2, retries=5):
    def decorator(func):
        def wrapper(*args, **kwargs):

            current_attempt = 0
            current_backoff_delay = backoff_delay
            while current_attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions.ClientError as error:
                    error_code = error.response["Error"]["Code"]
                    if error_code in [
                        "ProvisionedThroughputExceededException",
                        "LimitExceededException",
                        "RequestLimitExceeded",
                        "ThrottlingException",
                        "RequestThrottled"
                    ]:
                        LOGGER.info("Rate limit exceeded; backing off and retrying ...")
                        current_attempt += 1
                        if current_attempt >= retries:
                            raise error
                        LOGGER.info(
                            f"Failed to execute '{func.__name__}'. Retrying in {current_backoff_delay} seconds ..."
                        )
                        time.sleep(current_backoff_delay)
                        current_backoff_delay *= 2 * random.random()
                    else:
                        raise

        return wrapper

    return decorator
