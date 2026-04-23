from contextlib import AbstractContextManager


class TransactionScope:
    def __init__(self, env) -> None:
        self._env = env

    def savepoint(self) -> AbstractContextManager[None]:
        return self._env.cr.savepoint()

    def commit(self) -> None:
        self._env.cr.commit()
