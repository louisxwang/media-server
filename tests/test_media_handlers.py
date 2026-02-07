"""Tests for media_handlers module."""
import pytest
from pathlib import Path

from src.media_server.media_handlers import (
    get_media_preview,
    delete_media,
    rename_media_file,
    move_items,
)


class TestGetMediaPreview:
    """Test media preview path retrieval."""
    
    def test_get_media_preview_exists(self, tmp_path):
        """Test get_media_preview when preview exists."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        preview_dir = media_dir / "previews"
        preview_dir.mkdir()
        
        original = media_dir / "video.mp4"
        original.write_text("video")
        
        preview = preview_dir / "video preview.mp4"
        preview.write_text("preview")
        
        result = get_media_preview(str(original), check_exist=True)
        assert "preview" in result
    
    def test_get_media_preview_not_exists(self, tmp_path):
        """Test get_media_preview when preview doesn't exist."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        original = media_dir / "video.mp4"
        original.write_text("video")
        
        result = get_media_preview(str(original), check_exist=True)
        assert "video.mp4" in result
    
    def test_get_media_preview_no_check(self, tmp_path):
        """Test get_media_preview with check_exist=False."""
        original = tmp_path / "video.mp4"
        original.write_text("video")
        
        result = get_media_preview(str(original), check_exist=False)
        assert "preview" in result


class TestDeleteMedia:
    """Test media deletion functionality."""
    
    def test_delete_media_to_trash(self, tmp_path):
        """Test deleting media to trash."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        trash_dir = static_dir / "deleted"
        trash_dir.mkdir()
        
        media_file = static_dir / "photo.jpg"
        media_file.write_text("image")
        
        success, error = delete_media(
            "/static/photo.jpg",
            "static",
            str(static_dir),
            str(trash_dir),
        )
        
        assert success
        assert not media_file.exists()
        assert (trash_dir / "photo.jpg").exists()
    
    def test_delete_media_permanent(self, tmp_path):
        """Test permanently deleting media from trash."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        trash_dir = static_dir / "deleted"
        trash_dir.mkdir()
        
        media_file = trash_dir / "photo.jpg"
        media_file.write_text("image")
        
        success, error = delete_media(
            "/static/deleted/photo.jpg",
            "static",
            str(static_dir),
            str(trash_dir),
        )
        
        assert success
        assert not media_file.exists()
    
    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting nonexistent file."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        trash_dir = static_dir / "deleted"
        trash_dir.mkdir()
        
        success, error = delete_media(
            "/static/nonexistent.jpg",
            "static",
            str(static_dir),
            str(trash_dir),
        )
        
        assert not success
        assert "does not exist" in error
    
    def test_delete_invalid_prefix(self, tmp_path):
        """Test deleting file with invalid media URL prefix."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        trash_dir = static_dir / "deleted"
        trash_dir.mkdir()
        
        success, error = delete_media(
            "/invalid/photo.jpg",
            "static",
            str(static_dir),
            str(trash_dir),
        )
        
        assert not success
        assert "not under media folder" in error


class TestRenameMediaFile:
    """Test media file renaming."""
    
    def test_rename_media_file(self, tmp_path):
        """Test renaming a media file."""
        media_file = tmp_path / "old_name.jpg"
        media_file.write_text("image")
        
        success, error, new_path, new_name = rename_media_file(
            str(media_file),
            "new_name",
            {},  # tags
            {},  # clips
            "static",
            str(tmp_path),
        )
        
        assert success
        assert new_name == "new_name.jpg"
        assert not media_file.exists()
        assert Path(new_path).exists()
    
    def test_rename_preserves_extension(self, tmp_path):
        """Test rename preserves file extension."""
        media_file = tmp_path / "photo.jpg"
        media_file.write_text("image")
        
        success, error, new_path, new_name = rename_media_file(
            str(media_file),
            "picture",
            {},
            {},
            "static",
            str(tmp_path),
        )
        
        assert success
        assert new_name == "picture.jpg"
    
    def test_rename_with_tags_update(self, tmp_path):
        """Test rename updates tag references."""
        media_file = tmp_path / "photo.jpg"
        media_file.write_text("image")
        
        tags = {"nature": {"photo.jpg"}}
        
        success, error, new_path, new_name = rename_media_file(
            str(media_file),
            "landscape",
            tags,
            {},
            "static",
            str(tmp_path),
        )
        
        assert success
        assert "landscape.jpg" in tags["nature"]
        assert "photo.jpg" not in tags["nature"]


class TestMoveItems:
    """Test moving media items."""
    
    def test_move_item_to_directory(self, tmp_path):
        """Test moving an item to destination directory."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        dest_dir = static_dir / "folder"
        dest_dir.mkdir()
        
        media_file = static_dir / "photo.jpg"
        media_file.write_text("image")
        
        success, error = move_items(
            ["/static/photo.jpg"],
            "folder",
            str(static_dir),
            "static",
        )
        
        assert success
        assert (dest_dir / "photo.jpg").exists()
        assert not media_file.exists()
    
    def test_move_creates_destination(self, tmp_path):
        """Test move creates destination directory if it doesn't exist."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        
        media_file = static_dir / "photo.jpg"
        media_file.write_text("image")
        
        success, error = move_items(
            ["/static/photo.jpg"],
            "new_folder",
            str(static_dir),
            "static",
        )
        
        assert success
        assert (static_dir / "new_folder" / "photo.jpg").exists()
    
    def test_move_multiple_items(self, tmp_path):
        """Test moving multiple items."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        dest_dir = static_dir / "folder"
        dest_dir.mkdir()
        
        (static_dir / "photo1.jpg").write_text("img1")
        (static_dir / "photo2.jpg").write_text("img2")
        
        success, error = move_items(
            ["/static/photo1.jpg", "/static/photo2.jpg"],
            "folder",
            str(static_dir),
            "static",
        )
        
        assert success
        assert (dest_dir / "photo1.jpg").exists()
        assert (dest_dir / "photo2.jpg").exists()
