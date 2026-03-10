from datetime import datetime, timezone
from threading import Lock


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RefreshTracker:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state = self._idle_state()
        self._previous_state: dict[str, object] | None = None

    def _idle_state(self) -> dict[str, object]:
        return {
            "status": "idle",
            "message": "No refresh has been started yet.",
            "started_at": None,
            "finished_at": None,
            "new_articles": 0,
            "processed_articles": 0,
            "failed_articles": 0,
        }

    def reset(self) -> None:
        with self._lock:
            self._state = self._idle_state()
            self._previous_state = None

    def try_start(self) -> bool:
        with self._lock:
            if self._state["status"] == "processing":
                return False

            self._previous_state = dict(self._state)
            self._state = {
                "status": "processing",
                "message": "Fetching and processing articles in the background.",
                "started_at": _utc_now(),
                "finished_at": None,
                "new_articles": 0,
                "processed_articles": 0,
                "failed_articles": 0,
            }
            return True

    def release_claim(self) -> None:
        with self._lock:
            if self._previous_state is None:
                self._state = self._idle_state()
                return

            self._state = self._previous_state
            self._previous_state = None

    def mark_completed(
        self,
        *,
        new_articles: int,
        processed_articles: int,
        failed_articles: int,
    ) -> None:
        with self._lock:
            started_at = self._state["started_at"] or _utc_now()
            self._previous_state = None
            self._state = {
                "status": "completed",
                "message": "Refresh completed.",
                "started_at": started_at,
                "finished_at": _utc_now(),
                "new_articles": new_articles,
                "processed_articles": processed_articles,
                "failed_articles": failed_articles,
            }

    def mark_failed(self, message: str) -> None:
        with self._lock:
            started_at = self._state["started_at"] or _utc_now()
            self._previous_state = None
            self._state = {
                "status": "failed",
                "message": message,
                "started_at": started_at,
                "finished_at": _utc_now(),
                "new_articles": 0,
                "processed_articles": 0,
                "failed_articles": 0,
            }

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return dict(self._state)


refresh_tracker = RefreshTracker()
