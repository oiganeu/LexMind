"""Tests for the Import Queue framework (TASK-0027).

Covers:
    - ImportRequest entity, RequestStatus FSM, RequestPriority
    - ImportQueueService: submit / dequeue / cancel / mark_* / pending_ids / size
    - ChecksumDedup strategy
    - ImportQueuePlugin lifecycle
    - Domain event emission (and no-op when bus is None)
"""

from __future__ import annotations

import pytest

from lexmind.import_queue import (
    ImportQueuePlugin,
    ImportQueueService,
    ImportRequest,
    RequestPriority,
    RequestStatus,
)
from lexmind.import_queue import import_queue_exceptions as exc
from lexmind.import_queue.dedup_strategy import ChecksumDedup
from lexmind.import_queue.queue_events import (
    DuplicateRejected,
    RequestCancelled,
    RequestCompleted,
    RequestDequeued,
    RequestEnqueued,
    RequestFailed,
)

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeEventBus:
    """Records published events."""

    def __init__(self) -> None:
        self.published: list[object] = []

    def publish(self, event: object) -> None:
        self.published.append(event)


class InMemoryQueueRepository:
    """In-memory ImportQueueRepository implementation for tests."""

    def __init__(self) -> None:
        self._store: dict[str, ImportRequest] = {}

    def create(self, request: ImportRequest) -> ImportRequest:
        self._store[request.request_id] = request
        return request

    def get_by_id(self, request_id: str) -> ImportRequest | None:
        return self._store.get(request_id)

    def update(self, request: ImportRequest) -> ImportRequest:
        self._store[request.request_id] = request
        return request

    def delete(self, request_id: str) -> None:
        self._store.pop(request_id, None)

    def list_pending(
        self, workspace_id: str | None = None, priority: int | None = None
    ) -> list[ImportRequest]:
        result = [
            r
            for r in self._store.values()
            if r.status == RequestStatus.PENDING
            and (workspace_id is None or r.workspace_id == workspace_id)
            and (priority is None or r.priority == priority)
        ]
        return result

    def count_pending(self) -> int:
        return sum(1 for r in self._store.values() if r.status == RequestStatus.PENDING)

    def get_queued(self, workspace_id: str) -> list[ImportRequest]:
        return [
            r
            for r in self._store.values()
            if r.workspace_id == workspace_id
            and r.status in (RequestStatus.PENDING, RequestStatus.DEQUEUED)
        ]


class NoDedup:
    """A dedup strategy that never flags duplicates."""

    def is_duplicate(self, request: ImportRequest) -> bool:
        return False


class AlwaysDedup:
    """A dedup strategy that always flags duplicates."""

    def is_duplicate(self, request: ImportRequest) -> bool:
        return True


# ---------------------------------------------------------------------------
# ImportRequest / FSM
# ---------------------------------------------------------------------------


class TestImportRequest:
    def test_default_state_is_pending(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        assert req.status is RequestStatus.PENDING
        assert req.priority is RequestPriority.NORMAL
        assert not req.is_terminal

    def test_empty_workspace_rejected(self) -> None:
        with pytest.raises(ValueError):
            ImportRequest(workspace_id="", location="storage://ws1/a.pdf")

    def test_retries_exceed_max_rejected(self) -> None:
        with pytest.raises(ValueError):
            ImportRequest(
                workspace_id="ws1",
                location="storage://ws1/a.pdf",
                retries=3,
                max_retries=3,
            )

    def test_transition_to_dequeued(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        req.transition_to(RequestStatus.DEQUEUED)
        assert req.status is RequestStatus.DEQUEUED

    def test_invalid_transition_raises(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        req.transition_to(RequestStatus.DEQUEUED)
        with pytest.raises(exc.InvalidRequestStateError):
            req.transition_to(RequestStatus.PENDING)

    def test_completed_is_terminal(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        req.transition_to(RequestStatus.DEQUEUED)
        req.transition_to(RequestStatus.PROCESSING)
        req.transition_to(RequestStatus.COMPLETED)
        assert req.is_terminal

    def test_can_retry_only_when_failed(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        req.transition_to(RequestStatus.DEQUEUED)
        req.transition_to(RequestStatus.FAILED)
        assert req.can_retry
        req.retry()
        assert req.status is RequestStatus.PENDING
        assert req.retries == 1

    def test_cannot_retry_when_completed(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        req.transition_to(RequestStatus.DEQUEUED)
        req.transition_to(RequestStatus.PROCESSING)
        req.transition_to(RequestStatus.COMPLETED)
        assert not req.can_retry

    def test_retry_when_not_retryable_raises(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        req.transition_to(RequestStatus.DEQUEUED)
        req.transition_to(RequestStatus.PROCESSING)
        req.transition_to(RequestStatus.COMPLETED)
        with pytest.raises(ValueError):
            req.retry()

    def test_to_job_payload_includes_request_id(self) -> None:
        req = ImportRequest(
            workspace_id="ws1",
            location="storage://ws1/a.pdf",
            payload={"k": "v"},
        )
        payload = req.to_job_payload()
        assert payload["request_id"] == req.request_id
        assert payload["workspace_id"] == "ws1"
        assert payload["location"] == "storage://ws1/a.pdf"
        assert payload["k"] == "v"


class TestRequestPriority:
    def test_weight_ordering(self) -> None:
        assert RequestPriority.LOW.weight < RequestPriority.NORMAL.weight
        assert RequestPriority.NORMAL.weight < RequestPriority.HIGH.weight
        assert RequestPriority.HIGH.weight < RequestPriority.CRITICAL.weight


# ---------------------------------------------------------------------------
# ImportQueueService
# ---------------------------------------------------------------------------


class TestImportQueueService:
    def _service(self, dedup=None, bus=None) -> ImportQueueService:
        return ImportQueueService(
            repository=InMemoryQueueRepository(),
            deduplication=dedup,
            event_bus=bus,
        )

    def test_submit_creates_pending(self) -> None:
        svc = self._service(dedup=NoDedup())
        req = svc.submit("ws1", "storage://ws1/a.pdf", priority=2)
        assert req.status is RequestStatus.PENDING
        assert req.priority == 2
        assert svc.size() == 1

    def test_submit_empty_workspace_raises(self) -> None:
        svc = self._service(dedup=NoDedup())
        with pytest.raises(ValueError):
            svc.submit("", "storage://ws1/a.pdf")

    def test_submit_empty_location_raises(self) -> None:
        svc = self._service(dedup=NoDedup())
        with pytest.raises(ValueError):
            svc.submit("ws1", "")

    def test_submit_emits_enqueued(self) -> None:
        bus = FakeEventBus()
        svc = self._service(dedup=NoDedup(), bus=bus)
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        assert any(
            isinstance(e, RequestEnqueued) and e.request_id == req.request_id
            for e in bus.published
        )

    def test_submit_duplicate_rejected(self) -> None:
        bus = FakeEventBus()
        svc = self._service(dedup=AlwaysDedup(), bus=bus)
        with pytest.raises(exc.DuplicateRequestError):
            svc.submit("ws1", "storage://ws1/a.pdf")
        assert any(isinstance(e, DuplicateRejected) for e in bus.published)
        assert svc.size() == 0

    def test_dequeue_returns_highest_priority(self) -> None:
        svc = self._service(dedup=NoDedup())
        svc.submit("ws1", "storage://ws1/low.pdf", priority=0)
        high = svc.submit("ws1", "storage://ws1/high.pdf", priority=3)
        svc.submit("ws1", "storage://ws1/mid.pdf", priority=1)
        first = svc.dequeue()
        assert first is not None
        assert first.request_id == high.request_id
        assert first.status is RequestStatus.DEQUEUED

    def test_dequeue_emits_dequeued(self) -> None:
        bus = FakeEventBus()
        svc = self._service(dedup=NoDedup(), bus=bus)
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        svc.dequeue()
        assert any(
            isinstance(e, RequestDequeued) and e.request_id == req.request_id
            for e in bus.published
        )

    def test_dequeue_empty_returns_none(self) -> None:
        svc = self._service(dedup=NoDedup())
        assert svc.dequeue() is None

    def test_get_job(self) -> None:
        svc = self._service(dedup=NoDedup())
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        fetched = svc.get_job(req.request_id)
        assert fetched is not None
        assert fetched.request_id == req.request_id

    def test_cancel_pending(self) -> None:
        bus = FakeEventBus()
        svc = self._service(dedup=NoDedup(), bus=bus)
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        assert svc.cancel(req.request_id) is True
        assert svc.get_job(req.request_id).status is RequestStatus.CANCELLED
        assert any(
            isinstance(e, RequestCancelled) and e.request_id == req.request_id
            for e in bus.published
        )

    def test_cancel_unknown_returns_false(self) -> None:
        svc = self._service(dedup=NoDedup())
        assert svc.cancel("nonexistent") is False

    def test_cancel_terminal_returns_false(self) -> None:
        svc = self._service(dedup=NoDedup())
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        svc.cancel(req.request_id)
        assert svc.cancel(req.request_id) is False

    def test_mark_completed(self) -> None:
        bus = FakeEventBus()
        svc = self._service(dedup=NoDedup(), bus=bus)
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        svc.dequeue()
        svc.mark_completed(req.request_id, document_id="doc-1", file_hash="abc")
        assert svc.get_job(req.request_id).status is RequestStatus.COMPLETED
        assert any(
            isinstance(e, RequestCompleted) and e.request_id == req.request_id
            for e in bus.published
        )

    def test_mark_failed(self) -> None:
        bus = FakeEventBus()
        svc = self._service(dedup=NoDedup(), bus=bus)
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        svc.dequeue()
        svc.mark_failed(req.request_id, error_message="boom")
        assert svc.get_job(req.request_id).status is RequestStatus.FAILED
        assert any(
            isinstance(e, RequestFailed) and e.request_id == req.request_id
            for e in bus.published
        )

    def test_pending_ids(self) -> None:
        svc = self._service(dedup=NoDedup())
        r1 = svc.submit("ws1", "storage://ws1/a.pdf")
        r2 = svc.submit("ws1", "storage://ws1/b.pdf")
        assert set(svc.pending_ids()) == {r1.request_id, r2.request_id}
        svc.dequeue()
        ids = svc.pending_ids()
        assert len(ids) == 1
        assert (r1.request_id in ids) != (r2.request_id in ids)

    def test_no_bus_noop(self) -> None:
        svc = self._service(dedup=NoDedup())
        req = svc.submit("ws1", "storage://ws1/a.pdf")
        svc.dequeue()
        svc.mark_completed(req.request_id)
        svc.cancel(req.request_id)  # already terminal -> False
        assert True  # no exception means no-op worked

    def test_mark_completed_unknown_noop(self) -> None:
        svc = self._service(dedup=NoDedup())
        svc.mark_completed("ghost")  # should not raise

    def test_mark_failed_unknown_noop(self) -> None:
        svc = self._service(dedup=NoDedup())
        svc.mark_failed("ghost")  # should not raise


# ---------------------------------------------------------------------------
# ChecksumDedup
# ---------------------------------------------------------------------------


class TestChecksumDedup:
    def test_not_duplicate_when_location_empty(self) -> None:
        dedup = ChecksumDedup(storage_manager=object())
        req = ImportRequest(workspace_id="ws1", location="")
        assert dedup.is_duplicate(req) is False

    def test_not_duplicate_when_storage_returns_none(self) -> None:
        class Storage:
            def get_by_location(self, ws, loc):
                return None

        dedup = ChecksumDedup(storage_manager=Storage())
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        assert dedup.is_duplicate(req) is False

    def test_duplicate_when_queued_twin_exists(self) -> None:
        class Storage:
            def get_by_location(self, ws, loc):
                return ImportRequest(
                    workspace_id=ws,
                    location=loc,
                    status=RequestStatus.PENDING,
                )

        dedup = ChecksumDedup(storage_manager=Storage())
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        assert dedup.is_duplicate(req) is True

    def test_not_duplicate_when_twin_completed(self) -> None:
        class Storage:
            def get_by_location(self, ws, loc):
                return ImportRequest(
                    workspace_id=ws,
                    location=loc,
                    status=RequestStatus.COMPLETED,
                )

        dedup = ChecksumDedup(storage_manager=Storage())
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        assert dedup.is_duplicate(req) is False

    def test_not_duplicate_when_storage_raises(self) -> None:
        class Storage:
            def get_by_location(self, ws, loc):
                raise RuntimeError("boom")

        dedup = ChecksumDedup(storage_manager=Storage())
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        assert dedup.is_duplicate(req) is False

    def test_same_request_id_not_duplicate(self) -> None:
        req = ImportRequest(workspace_id="ws1", location="storage://ws1/a.pdf")
        same = ImportRequest(
            workspace_id="ws1",
            location="storage://ws1/a.pdf",
            request_id=req.request_id,
            status=RequestStatus.PENDING,
        )

        class Storage:
            def get_by_location(self, ws, loc):
                return same

        dedup = ChecksumDedup(storage_manager=Storage())
        assert dedup.is_duplicate(req) is False


# ---------------------------------------------------------------------------
# ImportQueuePlugin
# ---------------------------------------------------------------------------


class TestImportQueuePlugin:
    def test_plugin_capability(self) -> None:
        svc = ImportQueueService(
            repository=InMemoryQueueRepository(), deduplication=NoDedup()
        )
        plugin = ImportQueuePlugin(service=svc)
        assert plugin.metadata.capabilities[0].value == "import_queue"

    def test_plugin_stop_cancels_pending(self) -> None:
        svc = ImportQueueService(
            repository=InMemoryQueueRepository(), deduplication=NoDedup()
        )
        svc.submit("ws1", "storage://ws1/a.pdf")
        plugin = ImportQueuePlugin(service=svc)
        plugin.initialize(context=None)
        plugin.stop()
        assert svc.size() == 0

    def test_plugin_exposes_service(self) -> None:
        svc = ImportQueueService(
            repository=InMemoryQueueRepository(), deduplication=NoDedup()
        )
        plugin = ImportQueuePlugin(service=svc)
        assert plugin.service is svc
