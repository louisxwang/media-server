"""Configuration management for media server."""
import json
import os


def load_config(root_path: str) -> dict:
    """Load configuration from config.json."""
    config_path = os.path.join(root_path, 'config.json')
    config = {}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f) or {}
        except Exception as e:
            print(f"Error loading config: {e}")
    
    return config


def get_paths(root: str) -> dict:
    """Calculate all necessary paths for the application."""
    config = load_config(root)
    
    media_path = os.path.abspath(config.get('MEDIA_PATH', os.path.join(root, 'static')))
    asset_path = os.path.abspath(config.get('ASSET_PATH', os.path.join(root, 'assets')))
    templates_dir = os.path.join(root, 'templates')
    trash_dir = os.path.join(media_path, 'deleted')
    
    # Create trash directory if it doesn't exist
    if not os.path.exists(trash_dir):
        os.makedirs(trash_dir, exist_ok=True)
    
    return {
        'root': root,
        'media_path': media_path,
        'asset_path': asset_path,
        'templates_dir': templates_dir,
        'trash_dir': trash_dir,
    }


def url_to_fs(path: str, static_dir: str, media_url: str) -> str:
    """Convert a URL-like media path to filesystem path."""
    if not path:
        return static_dir
    
    p = path.lstrip('/')
    if p == media_url:
        return static_dir
    if p.startswith(media_url + '/'):
        rel = p[len(media_url) + 1:]
        return os.path.join(static_dir, rel)
    
    return os.path.abspath(p)


def fs_to_url(fs_path: str, static_dir: str, media_url: str) -> str:
    """Convert a filesystem path to a URL path."""
    try:
        rel = os.path.relpath(fs_path, static_dir).replace('\\', '/')
        if rel == '.':
            return '/' + media_url
        return '/' + '/'.join([media_url, rel])
    except Exception:
        return '/' + media_url + '/' + os.path.basename(fs_path)
