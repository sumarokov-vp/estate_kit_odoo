import time


class TimeSleeper:
    def sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        time.sleep(seconds)
