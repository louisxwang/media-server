"""Media file operations handlers."""
import os
import shutil

from src.media_server.config import fs_to_url, url_to_fs


def get_media_preview(file_path: str, check_exist: bool = True) -> str:
    """Get preview file path for a media file."""
    folder = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    basename_no_ext, extension = os.path.splitext(basename)
    
    preview_path = os.path.join(folder, 'previews', f'{basename_no_ext} preview{extension}')
    
    if check_exist and not os.path.isfile(preview_path):
        preview_path = file_path

    # Return filesystem path (normalized with forward slashes); caller should convert to URL
    return preview_path.replace('\\', '/')


def delete_media(
    media_path: str,
    media_url: str,
    static_dir: str,
    trash_dir: str,
) -> tuple[bool, str]:
    """Delete a media file (move to trash or permanently delete if in trash)."""
    try:
        media_path = media_path.lstrip('/')
        
        # Validate URL prefix
        if not media_path.startswith(media_url):
            return False, 'File not under media folder'
        
        # Convert to filesystem path
        fs_media = url_to_fs(media_path, static_dir, media_url)
        if not os.path.exists(fs_media):
            return False, 'File does not exist'
        
        # Check if in trash
        trash_path = os.path.abspath(trash_dir)
        media_abs_path = os.path.abspath(fs_media)
        
        try:
            common_path = os.path.commonpath([media_abs_path, trash_path])
            in_trash = common_path == trash_path
        except ValueError:
            in_trash = False
        
        if not in_trash:
            # Move to trash
            destination = os.path.join(trash_dir, os.path.basename(fs_media))
            shutil.move(fs_media, destination)
            print("Media moved to recycle bin")
        else:
            # Permanently delete
            os.remove(fs_media)
            print("Media permanently deleted")
        
        return True, 'Success'
    
    except Exception as e:
        return False, str(e)


def rename_media_file(
    media_path: str,
    new_filename: str,
    tags_state: dict,
    clips_data: dict,
    media_url: str,
    static_dir: str,
) -> tuple[bool, str, str, str]:
    """Rename a media file and update metadata."""
    try:
        directory, old_filename = os.path.split(media_path)
        extension = os.path.splitext(old_filename)[1]
        
        if not new_filename.endswith(extension):
            new_filename += extension
        
        new_path = os.path.join(directory, new_filename)
        
        # Rename the file
        os.rename(media_path, new_path)
        
        # Rename preview if it exists
        old_preview = get_media_preview(media_path, check_exist=False).lstrip('/')
        if os.path.isfile(old_preview):
            new_preview = get_media_preview(new_path, check_exist=False).lstrip('/')
            os.rename(old_preview, new_preview)
        
        # Update tags
        changed_tags = []
        for tag_name, medias in tags_state.items():
            if old_filename in medias:
                medias.remove(old_filename)
                medias.add(new_filename)
                changed_tags.append(tag_name)
        
        # Update clips data
        old_url = fs_to_url(media_path, static_dir, media_url)
        new_url = fs_to_url(new_path, static_dir, media_url)
        
        if old_url in clips_data:
            clips_data[new_url] = clips_data.pop(old_url)
        
        return True, 'Success', new_path, new_filename
    
    except Exception as e:
        return False, str(e), '', ''


def move_items(
    items: list[str],
    destination: str,
    static_dir: str,
    media_url: str,
) -> tuple[bool, str]:
    """Move media files to destination."""
    try:
        dest_dir = os.path.join(static_dir, destination)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        for item in items:
            fs_item = url_to_fs(item, static_dir, media_url)
            if os.path.exists(fs_item):
                shutil.move(fs_item, os.path.join(dest_dir, os.path.basename(fs_item)))
        
        return True, 'Success'
    
    except Exception as e:
        return False, str(e)
