"""Browse and search routes."""
import os

from natsort import natsorted

from src.media_server.media_handlers import get_media_preview
from src.media_server.models import get_pinyin


def get_all_media_files(path: str, media_files_cache: list) -> list:
    """Get all media files recursively from a path."""
    if media_files_cache:
        return media_files_cache
    
    print(f'Caching all media files from {path}...')
    media_exts = ('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.webp', '.ogg')
    
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith(media_exts):
                file_path = os.path.join(root, name)
                media_files_cache.append(file_path.replace('\\', '/'))
    
    print(f'Total {len(media_files_cache)} media files cached.')
    return media_files_cache


def get_all_video_files(path: str, all_media: list, video_files_cache: list) -> list:
    """Get all video files from a path."""
    if video_files_cache:
        return video_files_cache
    
    if not all_media:
        all_media = get_all_media_files(path, all_media)
    
    video_exts = ('.mp4', '.webm', '.ogg')
    video_files_cache = [
        f for f in all_media
        if f.lower().endswith(video_exts) and 'previews' not in f
    ]
    
    return video_files_cache


def search_media_files(
    search_path: str,
    keywords: list[str],
    all_media: list,
) -> list:
    """Search for media files by keyword."""
    all_files = get_all_media_files(search_path, all_media)
    
    results = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        filename_pinyin = get_pinyin(file_path).lower()
        
        # Check if any keyword matches
        if (any(kw.lower() in filename.lower() for kw in keywords) or
            any(kw.lower() in filename_pinyin for kw in keywords)):
            if not filename.endswith('preview.mp4'):
                results.append(filename)
    
    return results


def filter_hidden_media(
    media_list: list,
    tags_state: dict,
    hidden_tags: set,
) -> list:
    """Filter out media with hidden tags."""
    return [
        media for media in media_list
        if not any(media in tags_state.get(t, set()) for t in hidden_tags)
    ]


def prepare_media_page(
    directory_path: str,
    subpath: str,
    tags_sorted: list,
    tags_state: dict,
    hidden_tags: set,
    static_dir: str,
    media_url: str,
    endpoint: str,
) -> dict:
    """Prepare data for rendering media browse page."""
    if not os.path.isdir(directory_path):
        return None
    
    items = os.listdir(directory_path)
    directories = [d for d in items if os.path.isdir(os.path.join(directory_path, d))]
    
    # Get media files
    media_exts = ('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.webp', '.ogg')
    media_files = natsorted([
        f for f in items
        if f.lower().endswith(media_exts)
    ])
    
    # Filter hidden media
    media_files = filter_hidden_media(media_files, tags_state, hidden_tags)
    
    # Prepare URLs and metadata
    media_paths = [
        '/' + '/'.join([media_url, *subpath.split('/'), mf])
        for mf in media_files if subpath
    ] or [
        '/' + '/'.join([media_url, mf])
        for mf in media_files
    ]
    
    media_tags = [
        " ".join([tag for tag, _ in tags_sorted if tag in tags_state and mf in tags_state[tag]])
        for mf in media_files
    ]
    
    preview_paths = [
        get_media_preview(os.path.join(directory_path, mf))
        for mf in media_files
    ]
    
    breadcrumb_paths = subpath.split('/') if subpath else []
    
    return {
        'directories': directories,
        'media_paths': media_paths,
        'media_tags': media_tags,
        'preview_paths': preview_paths,
        'breadcrumb_paths': breadcrumb_paths,
    }
