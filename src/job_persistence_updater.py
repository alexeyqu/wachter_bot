"""
This is a very specific implementation of Updater with job persistence, which doesn't actually store jobs.
"""

from datetime import datetime
import json
import os
from telegram.ext import Updater
from typing import Callable

from src.handlers.group.group_handler import (
    delete_message,
    on_kick_timeout,
    on_notify_timeout,
)
from src.logging import tg_logger


JOBS_JSON = "jobs.json"


class JobPersistenceUpdater(Updater):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_jobs()

    def _signal_handler(self, signum, frame) -> None:
        self._store_jobs()
        super()._signal_handler(signum, frame)

    def _store_jobs(self):
        try:
            jobs = []
            for job in self.job_queue.jobs():
                jobs.append(
                    {
                        "name": job.name,
                        "when": datetime.timestamp(job.next_t) if job.next_t else None,
                        "context": {
                            "chat_id": job.context.get("chat_id"),
                            "user_id": job.context.get("user_id"),
                            "message_id": job.context.get("message_id"),
                            "creation_time": job.context.get("creation_time"),
                            "timeout": datetime.timestamp(job.context.get("timeout"))
                            if job.context.get("timeout")
                            else None,
                        },
                    }
                )

            with open(JOBS_JSON, "w") as file:
                json.dump(jobs, file)
            tg_logger.info(f"Stored {len(jobs)} jobs")
        except Exception as e:
            tg_logger.exception(f"Failed to store jobs", exc_info=e)

    def _load_jobs(self):
        try:
            if not os.path.exists(JOBS_JSON):
                return
            with open(JOBS_JSON, "r") as file:
                jobs = json.load(file)
                for job in jobs:
                    self.job_queue.run_once(
                        _get_callback(job["name"]),
                        datetime.fromtimestamp(job["when"]),
                        context={
                            "chat_id": job["context"].get("chat_id"),
                            "user_id": job["context"].get("user_id"),
                            "message_id": job["context"].get("message_id"),
                            "creation_time": job["context"].get("creation_time"),
                            "timeout": datetime.fromtimestamp(
                                job["context"].get("timeout")
                            )
                            if job["context"].get("timeout")
                            else None,
                        },
                    )
                tg_logger.info(f"Loaded {len(jobs)} jobs")
        except Exception as e:
            tg_logger.exception(f"Failed to load jobs", exc_info=e)


def _get_callback(name: str) -> Callable:
    def blank_fn(*args, **kwargs):
        pass

    if name == "delete_message":
        return delete_message
    if name == "on_kick_timeout":
        return on_kick_timeout
    if name == "on_notify_timeout":
        return on_notify_timeout
    return blank_fn
