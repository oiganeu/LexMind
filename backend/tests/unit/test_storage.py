"""Unit tests for the Storage Abstraction Layer (TASK-0016).

Covers:
    - URI parser and builder
    - Storage models and checksum
    - FilesystemStorageProvider (all operations)
    - StorageManager façade
    - Exception hierarchy
    - No-infrastructure-dependency guards
"""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest

from lexmind.storage.exceptions import (
    InvalidStorageURIError,
    StorageAlreadyExistsError,
    StorageChecksumError,
    StorageError,
    StorageNotFoundError,
    StoragePermissionDeniedError,
)
from lexmind.storage.filesystem import FilesystemStorageProvider
from lexmind.storage.manager import StorageManager
from lexmind.storage.models import StorageObject, StorageStat, compute_checksum
from lexmind.storage.types import StorageBackend
from lexmind.storage.uri import build_uri, join_uri, parse_uri

# ======================================================================
# URI Parser
# ======================================================================


class TestParseURI:
    """Tests for parse_uri()."""

    def test_parse_simple(self) -> None:
        uri = parse_uri("storage://workspace/path/to/file.pdf")
        assert uri.workspace == "workspace"
        assert uri.path == "path/to/file.pdf"
        assert uri.raw == "storage://workspace/path/to/file.pdf"

    def test_parse_root_only(self) -> None:
        uri = parse_uri("storage://myws/")
        assert uri.workspace == "myws"
        assert uri.path == ""

    def test_parse_no_trailing_slash(self) -> None:
        uri = parse_uri("storage://myws")
        assert uri.workspace == "myws"
        assert uri.path == ""

    def test_parse_empty_raises(self) -> None:
        with pytest.raises(InvalidStorageURIError):
            parse_uri("")

    def test_parse_no_scheme_raises(self) -> None:
        with pytest.raises(InvalidStorageURIError):
            parse_uri("ftp://workspace/path")

    def test_parse_no_workspace_raises(self) -> None:
        with pytest.raises(InvalidStorageURIError):
            parse_uri("storage:///path")

    def test_parse_deep_path(self) -> None:
        uri = parse_uri("storage://ws/a/b/c/d/e.txt")
        assert uri.path == "a/b/c/d/e.txt"


class TestStorageURI:
    """Tests for StorageURI dataclass methods."""

    def test_parent(self) -> None:
        uri = parse_uri("storage://ws/docs/contract.pdf")
        parent = uri.parent
        assert parent.path == "docs"
        assert parent.workspace == "ws"

    def test_name(self) -> None:
        uri = parse_uri("storage://ws/docs/contract.pdf")
        assert uri.name == "contract.pdf"

    def test_suffix(self) -> None:
        uri = parse_uri("storage://ws/docs/contract.pdf")
        assert uri.suffix == ".pdf"

    def test_child(self) -> None:
        uri = parse_uri("storage://ws/docs")
        child = uri.child("contract.pdf")
        assert child.path == "docs/contract.pdf"
        assert child.workspace == "ws"

    def test_str_roundtrip(self) -> None:
        uri = parse_uri("storage://ws/docs/file.txt")
        assert str(uri) == "storage://ws/docs/file.txt"


class TestBuildURI:
    """Tests for build_uri()."""

    def test_build_simple(self) -> None:
        result = build_uri("ws", "docs/file.pdf")
        assert result == "storage://ws/docs/file.pdf"

    def test_build_empty_path(self) -> None:
        result = build_uri("ws", "")
        assert result == "storage://ws/"


class TestJoinURI:
    """Tests for join_uri()."""

    def test_join_single_segment(self) -> None:
        result = join_uri("storage://ws/docs", "file.pdf")
        assert result == "storage://ws/docs/file.pdf"

    def test_join_multiple_segments(self) -> None:
        result = join_uri("storage://ws", "a", "b", "c.txt")
        assert result == "storage://ws/a/b/c.txt"


# ======================================================================
# Models
# ======================================================================


class TestStorageObject:
    """Tests for StorageObject model."""

    def test_properties(self) -> None:
        from datetime import datetime
        obj = StorageObject(
            uri="storage://ws/docs/file.pdf",
            size=1024,
            created=datetime(2025, 1, 1, tzinfo=UTC),
            modified=datetime(2025, 1, 2, tzinfo=UTC),
            checksum="abc123",
            backend=StorageBackend.FILESYSTEM,
        )
        assert obj.name == "file.pdf"
        assert obj.parent == "storage://ws/docs"
        assert obj.extension == ".pdf"
        assert not obj.is_root

    def test_is_root(self) -> None:
        from datetime import datetime
        obj = StorageObject(
            uri="/",
            size=0,
            created=datetime(2025, 1, 1, tzinfo=UTC),
            modified=datetime(2025, 1, 1, tzinfo=UTC),
            checksum="",
            backend=StorageBackend.FILESYSTEM,
        )
        assert obj.is_root


class TestComputeChecksum:
    """Tests for compute_checksum()."""

    def test_sha256(self) -> None:
        result = compute_checksum(b"hello world")
        assert len(result) == 64
        assert result == compute_checksum(b"hello world")

    def test_different_data(self) -> None:
        a = compute_checksum(b"aaa")
        b = compute_checksum(b"bbb")
        assert a != b

    def test_unsupported_algorithm(self) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            compute_checksum(b"test", algorithm="nonexistent")


class TestStorageStat:
    """Tests for StorageStat model."""

    def test_not_found(self) -> None:
        stat = StorageStat(exists=False)
        assert not stat.exists
        assert stat.size == 0


# ======================================================================
# FilesystemStorageProvider
# ======================================================================


@pytest.fixture()
def tmp_storage(tmp_path: Path) -> FilesystemStorageProvider:
    """Provide a FilesystemStorageProvider rooted in a temp directory."""
    return FilesystemStorageProvider(tmp_path / "storage")


class TestFSProviderInit:
    """Tests for provider initialisation."""

    def test_creates_root(self, tmp_path: Path) -> None:
        root = tmp_path / "new_root"
        FilesystemStorageProvider(root)
        assert root.exists()
        assert root.is_dir()

    def test_relative_root_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="absolute"):
            FilesystemStorageProvider(Path("relative/path"))


class TestFSProviderReadWrite:
    """Tests for read/write operations."""

    def test_write_read_bytes(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("docs/file.bin", b"\x00\x01\x02")
        data = tmp_storage.read_bytes("docs/file.bin")
        assert data == b"\x00\x01\x02"

    def test_write_read_text(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_text("docs/file.txt", "Hello, world!")
        text = tmp_storage.read_text("docs/file.txt")
        assert text == "Hello, world!"

    def test_write_creates_parents(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("a/b/c/d/file.bin", b"data")
        assert tmp_storage.exists("a/b/c/d/file.bin")

    def test_read_nonexistent_raises(self, tmp_storage: FilesystemStorageProvider) -> None:
        with pytest.raises(StorageNotFoundError):
            tmp_storage.read_bytes("nonexistent.bin")


class TestFSProviderDelete:
    """Tests for delete operations."""

    def test_delete_file(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("file.bin", b"data")
        tmp_storage.delete("file.bin")
        assert not tmp_storage.exists("file.bin")

    def test_delete_directory(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.mkdir("dir")
        tmp_storage.write_bytes("dir/a.bin", b"1")
        tmp_storage.write_bytes("dir/b.bin", b"2")
        tmp_storage.delete("dir")
        assert not tmp_storage.exists("dir")

    def test_delete_nonexistent_raises(self, tmp_storage: FilesystemStorageProvider) -> None:
        with pytest.raises(StorageNotFoundError):
            tmp_storage.delete("nonexistent.bin")


class TestFSProviderCopyMove:
    """Tests for copy and move operations."""

    def test_copy_file(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("src.bin", b"payload")
        tmp_storage.copy("src.bin", "dst.bin")
        assert tmp_storage.read_bytes("dst.bin") == b"payload"
        assert tmp_storage.read_bytes("src.bin") == b"payload"

    def test_move_file(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("src.bin", b"payload")
        tmp_storage.move("src.bin", "dst.bin")
        assert tmp_storage.read_bytes("dst.bin") == b"payload"
        assert not tmp_storage.exists("src.bin")

    def test_copy_nonexistent_raises(self, tmp_storage: FilesystemStorageProvider) -> None:
        with pytest.raises(StorageNotFoundError):
            tmp_storage.copy("nope.bin", "dst.bin")


class TestFSProviderDirectory:
    """Tests for directory operations."""

    def test_mkdir(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.mkdir("deep/nested/dir")
        tmp_storage.write_bytes("deep/nested/dir/file.bin", b"x")
        assert tmp_storage.exists("deep/nested/dir/file.bin")

    def test_list(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("dir/a.txt", b"a")
        tmp_storage.write_bytes("dir/b.txt", b"b")
        tmp_storage.mkdir("dir/sub")
        children = tmp_storage.list("dir")
        assert "a.txt" in children
        assert "b.txt" in children
        assert "sub" in children

    def test_list_nonexistent_raises(self, tmp_storage: FilesystemStorageProvider) -> None:
        with pytest.raises(StorageNotFoundError):
            tmp_storage.list("nope")

    def test_walk(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("root/a.txt", b"a")
        tmp_storage.write_bytes("root/sub/b.txt", b"b")
        dirs = []
        files = []
        for dirpath, _dirnames, filenames in tmp_storage.walk("root"):
            dirs.append(dirpath)
            files.extend(filenames)
        assert "a.txt" in files
        assert "b.txt" in files


class TestFSProviderStat:
    """Tests for stat operations."""

    def test_stat_exists(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("file.bin", b"data")
        stat = tmp_storage.stat("file.bin")
        assert stat.exists
        assert not stat.is_directory
        assert stat.size == 4

    def test_stat_dir(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.mkdir("dir")
        stat = tmp_storage.stat("dir")
        assert stat.exists
        assert stat.is_directory

    def test_stat_not_exists(self, tmp_storage: FilesystemStorageProvider) -> None:
        stat = tmp_storage.stat("nope")
        assert not stat.exists


class TestFSProviderChecksum:
    """Tests for checksum operations."""

    def test_checksum(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("file.bin", b"hello")
        cs = tmp_storage.checksum("file.bin")
        expected = compute_checksum(b"hello")
        assert cs == expected


class TestFSProviderOpen:
    """Tests for open operations."""

    def test_open_read(self, tmp_storage: FilesystemStorageProvider) -> None:
        tmp_storage.write_bytes("file.bin", b"content")
        with tmp_storage.open("file.bin", "rb") as f:
            assert f.read() == b"content"

    def test_open_write(self, tmp_storage: FilesystemStorageProvider) -> None:
        with tmp_storage.open("new.bin", "wb") as f:
            f.write(b"written")
        assert tmp_storage.read_bytes("new.bin") == b"written"


class TestFSProviderResolve:
    """Tests for resolve operations."""

    def test_resolve_returns_path(self, tmp_storage: FilesystemStorageProvider) -> None:
        resolved = tmp_storage.resolve("file.bin")
        assert isinstance(resolved, Path)
        assert resolved.is_absolute()


# ======================================================================
# StorageManager
# ======================================================================


@pytest.fixture()
def manager(tmp_path: Path) -> StorageManager:
    """Provide a StorageManager rooted in a temp directory."""
    provider = FilesystemStorageProvider(tmp_path / "mgr_storage")
    return StorageManager(provider)


class TestManagerSaveLoad:
    """Tests for save/load through the manager."""

    def test_save_load(self, manager: StorageManager) -> None:
        uri = "storage://ws/docs/file.bin"
        manager.save(uri, b"binary data")
        data = manager.load(uri)
        assert data == b"binary data"

    def test_save_load_text(self, manager: StorageManager) -> None:
        uri = "storage://ws/docs/file.txt"
        manager.save_text(uri, "Hello text")
        text = manager.load_text(uri)
        assert text == "Hello text"

    def test_load_nonexistent(self, manager: StorageManager) -> None:
        with pytest.raises(StorageNotFoundError):
            manager.load("storage://ws/nope.bin")


class TestManagerDelete:
    """Tests for delete through the manager."""

    def test_delete(self, manager: StorageManager) -> None:
        uri = "storage://ws/docs/file.bin"
        manager.save(uri, b"data")
        manager.delete(uri)
        assert not manager.exists(uri)


class TestManagerCopyMove:
    """Tests for copy/move through the manager."""

    def test_copy(self, manager: StorageManager) -> None:
        src = "storage://ws/src.bin"
        dst = "storage://ws/dst.bin"
        manager.save(src, b"copy me")
        manager.copy(src, dst)
        assert manager.load(dst) == b"copy me"

    def test_move(self, manager: StorageManager) -> None:
        src = "storage://ws/src.bin"
        dst = "storage://ws/dst.bin"
        manager.save(src, b"move me")
        manager.move(src, dst)
        assert manager.load(dst) == b"move me"
        assert not manager.exists(src)


class TestManagerChecksum:
    """Tests for checksum through the manager."""

    def test_checksum(self, manager: StorageManager) -> None:
        uri = "storage://ws/file.bin"
        manager.save(uri, b"check me")
        cs = manager.checksum(uri)
        expected = compute_checksum(b"check me")
        assert cs == expected


class TestManagerExists:
    """Tests for exists through the manager."""

    def test_exists(self, manager: StorageManager) -> None:
        uri = "storage://ws/file.bin"
        assert not manager.exists(uri)
        manager.save(uri, b"data")
        assert manager.exists(uri)


class TestManagerStat:
    """Tests for stat through the manager."""

    def test_stat(self, manager: StorageManager) -> None:
        uri = "storage://ws/file.bin"
        manager.save(uri, b"data")
        stat = manager.stat(uri)
        assert stat.exists
        assert stat.size == 4


class TestManagerList:
    """Tests for list through the manager."""

    def test_list(self, manager: StorageManager) -> None:
        manager.save("storage://ws/dir/a.bin", b"1")
        manager.save("storage://ws/dir/b.bin", b"2")
        children = manager.list("storage://ws/dir")
        assert "a.bin" in children
        assert "b.bin" in children


class TestManagerMkdir:
    """Tests for mkdir through the manager."""

    def test_mkdir(self, manager: StorageManager) -> None:
        manager.mkdir("storage://ws/deep/dir")
        manager.save("storage://ws/deep/dir/file.bin", b"x")
        assert manager.exists("storage://ws/deep/dir/file.bin")


class TestManagerWalk:
    """Tests for walk through the manager."""

    def test_walk(self, manager: StorageManager) -> None:
        manager.save("storage://ws/root/a.bin", b"1")
        manager.save("storage://ws/root/sub/b.bin", b"2")
        files = []
        for _dirpath, _dirnames, filenames in manager.walk("storage://ws/root"):
            files.extend(filenames)
        assert "a.bin" in files
        assert "b.bin" in files


class TestManagerBackend:
    """Tests for backend property."""

    def test_backend(self, manager: StorageManager) -> None:
        assert manager.backend == "filesystem"


# ======================================================================
# Exceptions
# ======================================================================


class TestExceptions:
    """Tests for exception hierarchy and messages."""

    def test_storage_error_is_lexmind_error(self) -> None:
        from lexmind.exceptions import LexMindError
        assert issubclass(StorageError, LexMindError)

    def test_not_found_message(self) -> None:
        exc = StorageNotFoundError("storage://ws/file.bin")
        assert "storage://ws/file.bin" in str(exc)
        assert exc.uri == "storage://ws/file.bin"

    def test_permission_denied_message(self) -> None:
        exc = StoragePermissionDeniedError("storage://ws/file.bin", "read")
        assert "read" in str(exc)
        assert exc.operation == "read"

    def test_already_exists_message(self) -> None:
        exc = StorageAlreadyExistsError("storage://ws/file.bin")
        assert exc.uri == "storage://ws/file.bin"

    def test_invalid_uri_message(self) -> None:
        exc = InvalidStorageURIError("bad", "no scheme")
        assert "no scheme" in str(exc)
        assert exc.reason == "no scheme"

    def test_checksum_error(self) -> None:
        exc = StorageChecksumError("u", "aaa", "bbb")
        assert exc.expected == "aaa"
        assert exc.actual == "bbb"


# ======================================================================
# No Infrastructure Dependencies
# ======================================================================


class TestNoInfrastructureDependencies:
    """Ensure the storage package has no infrastructure imports."""

    def test_no_sql_imports(self) -> None:
        """Storage must not depend on any SQL library."""
        import ast
        pkg_dir = Path(__file__).resolve().parent.parent / "lexmind" / "storage"
        for py_file in pkg_dir.glob("*.py"):
            content = py_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = node.module or ""
                    assert "sqlalchemy" not in mod.lower(), (
                        f"{py_file.name} imports SQL: {mod}"
                    )
                    assert "sqlite" not in mod.lower(), (
                        f"{py_file.name} imports sqlite: {mod}"
                    )

    def test_no_fastapi_imports(self) -> None:
        """Storage must not depend on FastAPI."""
        import ast
        pkg_dir = Path(__file__).resolve().parent.parent / "lexmind" / "storage"
        for py_file in pkg_dir.glob("*.py"):
            content = py_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = node.module or ""
                    assert "fastapi" not in mod.lower(), (
                        f"{py_file.name} imports FastAPI: {mod}"
                    )

    def test_no_os_path_imports(self) -> None:
        """Storage must not use os.path."""
        import ast
        pkg_dir = Path(__file__).resolve().parent.parent / "lexmind" / "storage"
        for py_file in pkg_dir.glob("*.py"):
            content = py_file.read_text()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name != "os.path", (
                            f"{py_file.name} imports os.path"
                        )

    def test_all_classes_have_docstrings(self) -> None:
        """Every public class must have a docstring."""
        import inspect

        import lexmind.storage as storage_pkg
        for name, obj in inspect.getmembers(storage_pkg):
            if inspect.isclass(obj) and obj.__module__.startswith("lexmind.storage"):
                assert obj.__doc__, f"{name} has no docstring"
