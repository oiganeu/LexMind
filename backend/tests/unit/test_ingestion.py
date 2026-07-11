"""Tests for the document ingestion engine framework."""

from pathlib import Path

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ingestion.duplicate_detector import DuplicateDetector
from lexmind.ingestion.file_discovery import FileDiscovery
from lexmind.ingestion.ingestion_exceptions import (
    IngestionError,
    InvalidJobStateError,
    JobNotFoundError,
)
from lexmind.ingestion.ingestion_job import IngestionJob, JobState, can_transition
from lexmind.ingestion.ingestion_manager import IngestionManager
from lexmind.ingestion.ingestion_result import FileOutcome
from lexmind.ingestion.ingestion_session import IngestionSession
from lexmind.ingestion.ingestion_source import IngestionSource
from lexmind.ingestion.ingestion_statistics import IngestionStatistics
from lexmind.ingestion.mime_detector import FileCategory, MimeDetector
from lexmind.ingestion.path_validator import PathValidator


def _make_docs(root: Path) -> None:
    (root / "a.txt").write_text("alpha", encoding="utf-8")
    (root / "b.pdf").write_bytes(b"%PDF-1.4 minimal")
    (root / "c.txt").write_text("alpha", encoding="utf-8")  # duplicate of a.txt
    (root / "d.xyz").write_text("unsupported", encoding="utf-8")


def test_job_creation_defaults() -> None:
    job = IngestionJob(workspace_id="ws1", source="/docs")
    assert job.state == JobState.CREATED
    assert job.job_id
    assert job.is_terminal is False


def test_valid_state_transition() -> None:
    job = IngestionJob(workspace_id="ws1", source="/docs")
    job.transition_to(JobState.DISCOVERING)
    assert job.state == JobState.DISCOVERING
    assert job.start_time is not None


def test_invalid_state_transition() -> None:
    job = IngestionJob(workspace_id="ws1", source="/docs")
    with pytest.raises(InvalidJobStateError):
        job.transition_to(JobState.COMPLETED)


def test_can_transition_matrix() -> None:
    assert can_transition(JobState.CREATED, JobState.DISCOVERING) is True
    assert can_transition(JobState.COMPLETED, JobState.IMPORTING) is False


def test_discovery_recursive(tmp_path: Path) -> None:
    _make_docs(tmp_path)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "e.txt").write_text("beta", encoding="utf-8")
    discovery = FileDiscovery()
    found = list(discovery.discover(str(tmp_path), recursive=True))
    assert len(found) == 5


def test_discovery_non_recursive(tmp_path: Path) -> None:
    _make_docs(tmp_path)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "e.txt").write_text("beta", encoding="utf-8")
    discovery = FileDiscovery()
    found = list(discovery.discover(str(tmp_path), recursive=False))
    assert len(found) == 4


def test_mime_detection() -> None:
    detector = MimeDetector()
    mime, category = detector.detect(Path("x.pdf"))
    assert mime == "application/pdf"
    assert category == FileCategory.DOCUMENT
    assert detector.is_supported(Path("x.pdf")) is True
    assert detector.is_supported(Path("x.zip")) is False
    assert detector.is_known(Path("x.zip")) is True
    assert detector.is_known(Path("x.xyz")) is False


def test_path_validator_rejects_missing(tmp_path: Path) -> None:
    validator = PathValidator(allowed_root=tmp_path)
    with pytest.raises(IngestionError):
        validator.validate(tmp_path / "nope.txt")


def test_duplicate_detector() -> None:
    detector = DuplicateDetector()
    assert detector.check_and_register("abc") is False
    assert detector.check_and_register("abc") is True
    assert detector.count == 1


def test_statistics_average() -> None:
    stats = IngestionStatistics(imported=4, duration_seconds=8.0)
    assert stats.average_file_time == 2.0
    assert IngestionStatistics().average_file_time == 0.0


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    _make_docs(tmp_path)
    manager = IngestionManager()
    job = manager.create_job("ws1", "filesystem", str(tmp_path))
    result = manager.run(job, location=str(tmp_path))
    assert job.state == JobState.COMPLETED
    assert result.count(FileOutcome.IMPORTED) == 2
    assert result.count(FileOutcome.DUPLICATE) == 1
    assert result.count(FileOutcome.UNSUPPORTED) == 1


def test_manager_publishes_events(tmp_path: Path) -> None:
    _make_docs(tmp_path)
    bus = EventBus()
    received: list[str] = []
    bus.subscribe_fn("ingestion.import_started", lambda e: received.append(e.name))
    bus.subscribe_fn("ingestion.import_completed", lambda e: received.append(e.name))
    manager = IngestionManager(event_bus=bus)
    job = manager.create_job("ws1", "filesystem", str(tmp_path))
    manager.run(job, location=str(tmp_path))
    assert "ingestion.import_started" in received
    assert "ingestion.import_completed" in received


def test_cancel_job() -> None:
    manager = IngestionManager()
    job = manager.create_job("ws1", "filesystem", "/docs")
    manager.cancel_job(job.job_id)
    assert job.state == JobState.CANCELLED


def test_get_missing_job_raises() -> None:
    manager = IngestionManager()
    with pytest.raises(JobNotFoundError):
        manager.get_job("does-not-exist")


def test_run_unknown_source_raises() -> None:
    manager = IngestionManager()
    job = IngestionJob(workspace_id="ws1", source="/docs")
    with pytest.raises(IngestionError):
        manager.run(job, location="/docs", source="s3")


def test_create_job_unknown_source_raises() -> None:
    manager = IngestionManager()
    with pytest.raises(IngestionError):
        manager.create_job("ws1", "s3", "/docs")


def test_run_failure_marks_job_failed() -> None:
    class _FailingSource:
        name = "failing"

        def discover(self, location, recursive=True):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")
            yield  # pragma: no cover

        def open_bytes(self, path):  # type: ignore[no-untyped-def]
            return b""

    bus = EventBus()
    failed: list[str] = []
    bus.subscribe_fn("ingestion.import_failed", lambda e: failed.append(e.name))
    manager = IngestionManager(event_bus=bus)
    manager.register_source(_FailingSource())
    job = manager.create_job("ws1", "failing", "/docs")
    with pytest.raises(IngestionError):
        manager.run(job, location="/docs", source="failing")
    assert job.state == JobState.FAILED
    assert "ingestion.import_failed" in failed


def test_discovery_missing_location_raises() -> None:
    from lexmind.ingestion.ingestion_exceptions import DiscoveryError

    discovery = FileDiscovery()
    with pytest.raises(DiscoveryError):
        list(discovery.discover("/no/such/place"))


def test_discovery_single_file_and_open_bytes(tmp_path: Path) -> None:
    target = tmp_path / "solo.txt"
    target.write_text("solo", encoding="utf-8")
    discovery = FileDiscovery()
    found = list(discovery.discover(str(target)))
    assert len(found) == 1
    assert discovery.open_bytes(found[0].path) == b"solo"


def test_path_validator_without_root(tmp_path: Path) -> None:
    target = tmp_path / "ok.txt"
    target.write_text("x", encoding="utf-8")
    resolved = PathValidator().validate(target)
    assert resolved == target.resolve()


def test_path_validator_outside_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    validator = PathValidator(allowed_root=allowed)
    with pytest.raises(IngestionError):
        validator.validate(outside)


def test_path_validator_within_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    inside = allowed / "in.txt"
    inside.write_text("x", encoding="utf-8")
    validator = PathValidator(allowed_root=allowed)
    assert validator.validate(inside) == inside.resolve()


def test_path_validator_root_itself(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    validator = PathValidator(allowed_root=allowed)
    assert validator.validate(allowed) == allowed.resolve()


def test_duplicate_detector_helpers() -> None:
    detector = DuplicateDetector()
    assert detector.is_duplicate("k") is False
    detector.register("k")
    assert detector.is_duplicate("k") is True
    detector.reset()
    assert detector.count == 0


def test_statistics_recorders() -> None:
    stats = IngestionStatistics()
    stats.record_imported()
    stats.record_skipped()
    stats.record_duplicate()
    stats.record_unsupported()
    stats.record_error()
    assert (stats.imported, stats.skipped, stats.duplicates) == (1, 1, 1)
    assert (stats.unsupported, stats.errors) == (1, 1)


def test_session_lifecycle() -> None:
    session = IngestionSession(workspace_id="ws1")
    assert session.is_complete is False
    job = IngestionJob(workspace_id="ws1", source="/docs")
    session.add_job(job)
    assert session.pending_jobs == [job]
    assert session.is_complete is False
    job.transition_to(JobState.CANCELLED)
    assert session.is_complete is True
    assert session.pending_jobs == []


def test_pipeline_rejects_outside_root(tmp_path: Path) -> None:
    _make_docs(tmp_path)
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    manager = IngestionManager(path_validator=PathValidator(allowed_root=allowed))
    job = manager.create_job("ws1", "filesystem", str(tmp_path))
    result = manager.run(job, location=str(tmp_path))
    assert result.count(FileOutcome.REJECTED) >= 1
    assert job.files_failed >= 1


def test_cancelled_job_stops_pipeline(tmp_path: Path) -> None:
    _make_docs(tmp_path)
    from lexmind.ingestion import ingestion_events as events
    from lexmind.ingestion.ingestion_context import IngestionContext
    from lexmind.ingestion.ingestion_pipeline import IngestionPipeline

    job = IngestionJob(workspace_id="ws1", source=str(tmp_path))
    source = FileDiscovery()
    assert isinstance(source, IngestionSource)
    context = IngestionContext(job=job, source=source, location=str(tmp_path))

    def _cancel_on_progress(name: str, payload: dict) -> None:
        if name == events.IMPORT_PROGRESS and not job.is_terminal:
            job.transition_to(JobState.CANCELLED)

    result = IngestionPipeline(emit=_cancel_on_progress).process(context)
    assert job.state == JobState.CANCELLED
    assert result.count(FileOutcome.IMPORTED) <= 1
