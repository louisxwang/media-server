"""Tests for config module."""
import json
import pytest
from pathlib import Path

from src.media_server.config import load_config, get_paths, url_to_fs, fs_to_url


class TestLoadConfig:
    """Test configuration loading."""
    
    def test_load_config_default(self, tmp_path):
        """Test load_config when config.json doesn't exist."""
        config = load_config(str(tmp_path))
        assert config == {}
    
    def test_load_config_with_file(self, tmp_path):
        """Test load_config with valid config.json."""
        config_file = tmp_path / "config.json"
        config_data = {"STATIC_PATH": "/media", "MEDIA_URL": "files"}
        config_file.write_text(json.dumps(config_data))
        
        config = load_config(str(tmp_path))
        assert config == config_data
    
    def test_load_config_invalid_json(self, tmp_path):
        """Test load_config with invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json {")
        
        config = load_config(str(tmp_path))
        assert config == {}
    
    def test_load_config_empty_file(self, tmp_path):
        """Test load_config with empty config.json."""
        config_file = tmp_path / "config.json"
        config_file.write_text("null")
        
        config = load_config(str(tmp_path))
        assert config == {}


class TestGetPaths:
    """Test path calculation."""
    
    def test_get_paths_defaults(self, tmp_path):
        """Test get_paths with default configuration."""
        paths = get_paths(str(tmp_path))
        
        assert paths['root'] == str(tmp_path)
        assert paths['media_url'] == 'static'
        assert 'static' in paths['static_dir']
        assert 'templates' in paths['templates_dir']
        assert 'deleted' in paths['trash_dir']
    
    def test_get_paths_custom_config(self, tmp_path):
        """Test get_paths with custom config.json."""
        config_file = tmp_path / "config.json"
        media_path = tmp_path / "media"
        config_data = {
            "STATIC_PATH": str(media_path),
            "MEDIA_URL": "files"
        }
        config_file.write_text(json.dumps(config_data))
        
        paths = get_paths(str(tmp_path))
        
        assert str(media_path) in paths['static_dir']
        assert paths['media_url'] == 'files'
    
    def test_get_paths_creates_trash_dir(self, tmp_path):
        """Test that get_paths creates trash directory."""
        paths = get_paths(str(tmp_path))
        trash_dir = Path(paths['trash_dir'])
        
        assert trash_dir.exists()
        assert trash_dir.is_dir()


class TestUrlToFs:
    """Test URL to filesystem path conversion."""
    
    def test_url_to_fs_empty_path(self):
        """Test url_to_fs with empty path."""
        static_dir = "/media"
        result = url_to_fs("", static_dir, "static")
        assert result == static_dir
    
    def test_url_to_fs_media_url(self):
        """Test url_to_fs with media URL."""
        static_dir = "/media"
        result = url_to_fs("/static", static_dir, "static")
        assert result == static_dir
    
    def test_url_to_fs_with_subpath(self):
        """Test url_to_fs with subpath."""
        static_dir = "/media"
        result = url_to_fs("/static/photos/image.jpg", static_dir, "static")
        assert "photos/image.jpg" in result
        assert "/media" in result
    
    def test_url_to_fs_leading_slash(self):
        """Test url_to_fs strips leading slashes."""
        static_dir = "/media"
        result = url_to_fs("//static/file.jpg", static_dir, "static")
        assert "file.jpg" in result


class TestFsToUrl:
    """Test filesystem to URL path conversion."""
    
    def test_fs_to_url_root(self):
        """Test fs_to_url with root path."""
        static_dir = "/media"
        result = fs_to_url("/media", static_dir, "static")
        assert result == "/static"
    
    def test_fs_to_url_subpath(self):
        """Test fs_to_url with subpath."""
        static_dir = "/media"
        result = fs_to_url("/media/photos/image.jpg", static_dir, "static")
        assert "/static/photos/image.jpg" in result
    
    def test_fs_to_url_custom_media_url(self):
        """Test fs_to_url with custom media URL."""
        static_dir = "/media"
        result = fs_to_url("/media/file.jpg", static_dir, "files")
        assert "/files/file.jpg" in result
