import threading
from collections.abc import Callable
from enum import Enum
from typing import Optional, Any
import time


class TaskRequest:
    def __init__(self, id: str, req: Any):
        self.id = id
        self.req = req

    def __repr__(self):
        return f"TaskRequest(id={self.id})"


class TaskStatus(Enum):
    UNINITIALIZED = -1
    IDLE = 0
    BUSY = 1


class TaskPayload:
    def __init__(self, task_core: Optional[dict[str, Any]] = None):
        self._lock = threading.Lock()
        self._env: Optional[object] = None
        self._exec: Optional[Callable[[object], None]] = None
        self._halt: Optional[Callable[[object], None]] = None
        self._status: TaskStatus = TaskStatus.UNINITIALIZED
        self._thread: Optional[threading.Thread] = None
        self._watchdog_interval: float = 0.1

        if task_core and self._validate_core(task_core):
            self._env = task_core["f_env"]
            self._exec = task_core["f_exec"]
            self._halt = task_core["f_halt"]
            self._status = TaskStatus.IDLE

    def _validate_core(self, core: dict[str, Any]) -> bool:
        return all(k in core and core[k] is not None for k in ("f_env", "f_exec", "f_halt"))

    def _run_task(self):
        with self._lock:
            if self._exec is None or self._env is None:
                return
            exec_thread = threading.Thread(target=self._exec, args=(self._env,))
            exec_thread.start()
            self._status = TaskStatus.BUSY

        while exec_thread.is_alive():
            time.sleep(self._watchdog_interval)

        exec_thread.join()
        with self._lock:
            self._status = TaskStatus.IDLE

    def start(self) -> bool:
        with self._lock:
            if self._status != TaskStatus.IDLE:
                return False
            self._thread = threading.Thread(target=self._run_task)
            self._thread.start()
            return True

    def stop(self):
        with self._lock:
            if self._status == TaskStatus.BUSY and self._halt and self._env:
                self._halt(self._env)
                if self._thread:
                    self._thread.join()
                self._status = TaskStatus.IDLE
                self._thread = None

    def load_task(self, task_core: Optional[dict[str, Any]]) -> bool:
        self.stop()
        with self._lock:
            if task_core and self._validate_core(task_core):
                self._env = task_core["f_env"]
                self._exec = task_core["f_exec"]
                self._halt = task_core["f_halt"]
                self._status = TaskStatus.IDLE
                return True
            return False

    def is_alive(self) -> bool:
        with self._lock:
            return self._status == TaskStatus.BUSY


class TaskTranslator:
    def __init__(self, translator: Optional[Callable[[TaskRequest], TaskPayload]]):
        self._translator = translator

    def gen_workload(self, request: TaskRequest) -> Optional[TaskPayload]:
        if self._translator:
            return self._translator(request)
        return None


class TaskQueue:
    def __init__(self):
        self._queue: dict[int, TaskPayload] = {}
        self._current_index: int = -1
        self._tail_index: int = 0
        self._translator: Optional[TaskTranslator] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._status: TaskStatus = TaskStatus.UNINITIALIZED
        self._lock = threading.Lock()

    def set_translator(self, translator: TaskTranslator):
        with self._lock:
            if translator and self._status == TaskStatus.UNINITIALIZED:
                self._translator = translator
                self._status = TaskStatus.IDLE

    def append(self, request: TaskRequest):
        with self._lock:
            if not self._translator:
                return
            task = self._translator.gen_workload(request)
            if task:
                self._queue[self._tail_index] = task
                self._tail_index += 1

    def cut_in(self, request: TaskRequest):
        with self._lock:
            if not self._translator:
                return
            task = self._translator.gen_workload(request)
            if task:
                for i in range(self._tail_index, self._current_index + 1, -1):
                    self._queue[i] = self._queue[i - 1]
                self._queue[self._current_index + 1] = task
                self._tail_index += 1

    def remove(self, task_id: int):
        with self._lock:
            self._queue.pop(task_id, None)

    def _listener(self):
        while True:
            with self._lock:
                if self._status != TaskStatus.BUSY:
                    break
                if self._current_index in self._queue:
                    task = self._queue[self._current_index]
                    if not task.is_alive():
                        task.start()
                elif self._current_index + 1 in self._queue:
                    self._current_index += 1
                else:
                    time.sleep(0.1)
                    continue
            time.sleep(0.1)

    def start(self) -> bool:
        with self._lock:
            if self._status != TaskStatus.IDLE:
                return False
            self._status = TaskStatus.BUSY
            self._listener_thread = threading.Thread(target=self._listener, daemon=True)
            self._listener_thread.start()
            return True

    def stop(self):
        with self._lock:
            if self._status != TaskStatus.BUSY:
                return
            self._status = TaskStatus.IDLE
        if self._listener_thread:
            self._listener_thread.join()
        with self._lock:
            for task in self._queue.values():
                task.stop()
            self._queue.clear()
            self._current_index = -1
            self._tail_index = 0
            self._listener_thread = None

    def is_alive(self) -> bool:
        with self._lock:
            return self._status == TaskStatus.BUSY

    def current_task(self) -> Optional[TaskPayload]:
        with self._lock:
            return self._queue.get(self._current_index)

    def queue_length(self) -> int:
        with self._lock:
            return len(self._queue)