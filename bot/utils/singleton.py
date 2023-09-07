import threading


class Singleton(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                cls._instances[cls] =  super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    