"""Tests for models module (MediaState)."""
import json
from pathlib import Path

from src.media_server.models import MediaState


class TestMediaStateInitialization:
    """Test MediaState initialization and database loading."""
    
    def test_init_creates_database_directory(self, tmp_path):
        """Test that init creates .database directory."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        # Create media directory
        (tmp_path / "media").mkdir()
        
        state = MediaState(str(tmp_path))
        
        db_dir = tmp_path / "media" / ".database"
        assert db_dir.exists()
    
    def test_init_creates_empty_pickle_files(self, tmp_path):
        """Test that init creates pickle files if they don't exist."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state = MediaState(str(tmp_path))
        
        db_dir = media_dir / ".database"
        assert (db_dir / "tags.pkl").exists()
        assert (db_dir / "clip_data.pkl").exists()
    
    def test_init_loads_existing_pickle_files(self, tmp_path):
        """Test that init loads existing pickle files."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        db_dir = media_dir / ".database"
        db_dir.mkdir()
        
        # Create initial state
        state1 = MediaState(str(tmp_path))
        state1.tags = {"nature": {"photo1.jpg"}}
        state1.save_tags()
        
        # Create new state and verify it loaded
        state2 = MediaState(str(tmp_path))
        assert state2.tags == {"nature": {"photo1.jpg"}}


class TestMediaStateTagOperations:
    """Test tag management in MediaState."""
    
    def test_add_tag_to_file(self, tmp_path):
        """Test adding a tag to a file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state = MediaState(str(tmp_path))
        if "nature" not in state.tags:
            state.tags["nature"] = set()
        state.tags["nature"].add("photo.jpg")
        
        assert "nature" in state.tags
        assert "photo.jpg" in state.tags["nature"]
    
    def test_remove_tag_from_file(self, tmp_path):
        """Test removing a tag from a file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state = MediaState(str(tmp_path))
        state.tags["nature"] = {"photo.jpg"}
        state.tags["nature"].discard("photo.jpg")
        
        assert "photo.jpg" not in state.tags.get("nature", set())
    
    def test_get_tags_by_file(self, tmp_path):
        """Test retrieving tags for a file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state = MediaState(str(tmp_path))
        state.tags["nature"] = {"photo.jpg"}
        state.tags["landscape"] = {"photo.jpg"}
        
        file_tags = {tag for tag, files in state.tags.items() if "photo.jpg" in files}
        assert file_tags == {"nature", "landscape"}


class TestMediaStateClipOperations:
    """Test clip data management in MediaState."""
    
    def test_add_clip(self, tmp_path):
        """Test adding a clip."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state = MediaState(str(tmp_path))
        if "video.mp4" not in state.clips_data:
            state.clips_data["video.mp4"] = []
        state.clips_data["video.mp4"].append({
            "start": 10.0,
            "end": 20.0,
            "name": "clip1"
        })
        
        assert "video.mp4" in state.clips_data
        assert any(c["name"] == "clip1" for c in state.clips_data["video.mp4"])
    
    def test_get_video_clips(self, tmp_path):
        """Test retrieving clips for a video."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state = MediaState(str(tmp_path))
        state.clips_data["video.mp4"] = [
            {"start": 10.0, "end": 20.0, "name": "clip1"},
            {"start": 30.0, "end": 40.0, "name": "clip2"},
        ]
        
        clips = state.clips_data.get("video.mp4", [])
        assert len(clips) == 2
        assert clips[0]["name"] == "clip1"
        assert clips[1]["name"] == "clip2"


class TestMediaStatePersistence:
    """Test saving and loading state."""
    
    def test_save_and_load_tags(self, tmp_path):
        """Test saving and loading tags."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state1 = MediaState(str(tmp_path))
        state1.tags["nature"] = {"photo.jpg"}
        state1.tags["landscape"] = {"photo.jpg"}
        state1.save_tags()
        
        state2 = MediaState(str(tmp_path))
        file_tags = {tag for tag, files in state2.tags.items() if "photo.jpg" in files}
        assert "nature" in file_tags
        assert "landscape" in file_tags
    
    def test_save_and_load_clips(self, tmp_path):
        """Test saving and loading clips."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "STATIC_PATH": str(tmp_path / "media"),
            "MEDIA_URL": "files"
        }))
        
        media_dir = tmp_path / "media"
        media_dir.mkdir()
        
        state1 = MediaState(str(tmp_path))
        state1.clips_data["video.mp4"] = [
            {"start": 10.0, "end": 20.0, "name": "clip1"}
        ]
        state1.save_clips()
        
        state2 = MediaState(str(tmp_path))
        clips = state2.clips_data.get("video.mp4", [])
        assert len(clips) == 1
        assert clips[0]["name"] == "clip1"


class TestMediaStateDefaults:
    """Test default initialization when no config exists."""
    
    def test_default_static_path(self, tmp_path):
        """Test default STATIC_PATH when config missing."""
        state = MediaState(str(tmp_path))
        
        # Should use workspace root with 'static' subfolder
        db_dir = Path(state.media_root) / ".database"
        assert db_dir.exists()
    
    def test_default_media_url(self, tmp_path):
        """Test default MEDIA_URL when config missing."""
        state = MediaState(str(tmp_path))
        
        # Default should be '/static'
        assert hasattr(state, 'media_root')
