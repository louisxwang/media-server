# Refactored Code Structure

## Architecture Overview

```
src/media_server/
├── __init__.py
├── app.py                 # Flask app + route handlers (400 lines)
├── config.py              # Configuration & path management (60 lines)
├── models.py              # State management & persistence (150 lines)
├── media_handlers.py      # File operations (130 lines)
├── tag_handlers.py        # Tag operations (50 lines)
└── browse.py              # Browse & search utilities (140 lines)
```

## Module Dependencies

```
┌─────────────────────────────────────┐
│        app.py (Flask Routes)        │
│    Entry point - orchestrates all   │
└──────────┬──────────────────────────┘
           │
        ┌──┴───────────────────┬──────────────┬──────────────┐
        │                      │              │              │
   ┌────v─────┐      ┌────────v──┐    ┌─────v──┐    ┌──────v───┐
   │ config.py│      │ models.py │    │browse.py│    │media_    │
   │  Paths & │      │  State &  │    │Browse & │    │handlers  │
   │  Config  │      │Persistence│    │Search   │    │ File Ops │
   └──────────┘      └────────────┘    └─────────┘    └──────────┘
                            │
                      ┌─────v─────────┐
                      │tag_handlers.py│
                      │Tag Operations │
                      └───────────────┘
```

## Data Flow Example: Browse Media

```
GET /browse/<path>
    ↓
Home() route in app.py
    ↓
prepare_media_page() from browse.py
    ├→ Uses: config.py (PATHS)
    ├→ Uses: models.py (STATE.sorted_tags, STATE.tags, STATE.hidden_tags)
    └→ Returns: prepared data dict
    ↓
render_template('index.html', **prepared_data)
```

## Data Flow Example: Add Tags

```
POST /save_tags
    ↓
save_tags() route in app.py
    ├→ update_tag_global_variables() from tag_handlers.py
    │   ├→ Updates STATE.tags
    │   └→ Updates STATE.last_used_tags
    ├→ STATE.update_sorted_tags()
    └→ STATE.save_tags() (persist to disk)
    ↓
return jsonify({"status": "success"})
```

## Data Flow Example: Delete Media

```
POST /delete
    ↓
delete() route in app.py
    ├→ url_to_fs() from config.py (convert URL to filesystem path)
    └→ delete_media() from media_handlers.py
        ├→ Check if file in trash
        ├→ If not: move to trash_dir
        └→ If yes: permanently delete
    ↓
return jsonify({"success": True/False, ...})
```

## State Initialization Flow

```
app.py module loads
    ↓
ROOT = calculate root path
PATHS = get_paths(ROOT)  ← config.py
    │
    ├→ Calculates: root, static_dir, media_url, templates_dir, trash_dir
    ├→ Creates: trash_dir if missing
    └→ Returns: paths dict
    ↓
STATE = MediaState(ROOT)  ← models.py
    ├→ Loads tags from tags.pkl
    ├→ Loads clips from clip_data.pkl
    ├→ Sorts tags
    └→ Ready to use
    ↓
app = Flask(...)
    └→ Configured with PATHS
    ↓
Routes registered
    └→ All use PATHS and STATE
```

## Module Responsibilities at a Glance

### config.py
```python
get_paths(root) → dict
  └─ Returns all paths needed by app

url_to_fs(url_path, static_dir, media_url) → filesystem_path
  └─ Converts /static/folder/file → /absolute/fs/path

fs_to_url(fs_path, static_dir, media_url) → url_path
  └─ Reverse: converts filesystem path to URL
```

### models.py
```python
class MediaState:
  .tags: dict[str, set[str]]         # tag_name → media_filenames
  .sorted_tags: list[(str, str)]     # [(tag, pinyin), ...]
  .hidden_tags: set[str]             # hidden tag names
  .clips_data: dict                  # video → clips
  .all_media_files: list[str]        # cache of all media
  .all_video_files: list[str]        # cache of all videos
  
  .save_tags()                       # persist tags to disk
  .save_clips()                      # persist clips to disk
  .update_sorted_tags()              # refresh sorting
  .clear_media_cache()               # clear file caches

get_pinyin(word: str) → str
  └─ Convert Chinese text to pinyin representation
```

### media_handlers.py
```python
get_media_preview(file_path, check_exist) → preview_url
  └─ Get preview file path for media

delete_media(path, media_url, static_dir, trash_dir) → (success, error)
  └─ Delete media or move to trash

rename_media_file(path, new_name, tags, clips, ...) → (success, error, new_path, new_filename)
  └─ Rename and update all metadata

move_items(items, destination, static_dir, media_url) → (success, error)
  └─ Batch move media to destination
```

### tag_handlers.py
```python
update_tag_global_variables(media, tag_list, tags, last_used, allow_remove) → bool
  └─ Add/remove tags for media, returns if changed

merge_tags(source_tags, dest_tag, tags) → None
  └─ Merge multiple tags into one
```

### browse.py
```python
get_all_media_files(path, cache) → list[str]
  └─ Find all media files recursively

get_all_video_files(path, all_media, cache) → list[str]
  └─ Get video files from media list

search_media_files(path, keywords, cache) → list[str]
  └─ Search by filename and pinyin

filter_hidden_media(media_list, tags, hidden_tags) → list[str]
  └─ Filter out hidden media

prepare_media_page(...) → dict
  └─ Prepare data for template rendering
```

### app.py (Routes)
```
GET  /                          → Home()
GET  /browse/<path>             → Home(subpath)
GET  /search_media/<path>       → search_media()
GET  /all_media                 → all_media()
GET  /all_videos                → all_videos()
GET  /tags                      → Tags()
GET  /tags/<tag>                → Tags(subpath)
GET  /clips                     → clips()
GET  /video_clip_marker         → mark_video_clips()
GET  /settings                  → settings_page()

POST /delete                    → delete()
POST /delete_multiple           → delete_multiple()
POST /rename                    → rename()
POST /rename_multiple           → rename_multiple()
POST /cut_multiple              → cut_multiple()
POST /paste_multiple            → paste_multiple()
POST /get_tags                  → get_tags()
POST /save_tags                 → save_tags()
POST /save_clips                → save_clips()
POST /load_clips                → load_clips()
POST /gen_clips                 → gen_clips()
POST /save_settings             → save_settings()
POST /filter_media_with_tags    → filter_media_with_tags()
```

## Adding New Features

### Example: Add user preferences module

```python
# New file: src/media_server/preferences.py
class UserPreferences:
    def __init__(self, root_path):
        self.prefs_file = Path(root_path) / 'preferences.json'
        self.load()
    
    def load(self):
        # Load from file
        pass
    
    def save(self):
        # Save to file
        pass

# In app.py
from src.media_server.preferences import UserPreferences

PREFS = UserPreferences(ROOT)

@app.route('/preferences')
def get_preferences():
    return jsonify(PREFS.__dict__)
```

### Example: Add logging module

```python
# New file: src/media_server/logger.py
import logging

def setup_logging(root_path):
    logger = logging.getLogger('media_server')
    handler = logging.FileHandler(Path(root_path) / 'app.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# In app.py
from src.media_server.logger import setup_logging

LOGGER = setup_logging(ROOT)

# Use in routes
LOGGER.info(f"Browsing directory: {subpath}")
```

## Testing Strategy

```python
# tests/test_media_handlers.py
from src.media_server.media_handlers import delete_media

def test_delete_media_to_trash(tmp_path):
    # Create test file
    test_file = tmp_path / "test.jpg"
    test_file.write_text("dummy")
    
    # Test delete
    success, error = delete_media(
        str(test_file), 
        'static', 
        str(tmp_path), 
        str(tmp_path / 'trash')
    )
    
    assert success
    assert test_file not in list(tmp_path.glob('*.jpg'))

# tests/test_tag_handlers.py
from src.media_server.tag_handlers import update_tag_global_variables

def test_add_tag_to_media():
    tags = {}
    last_used = []
    
    changed = update_tag_global_variables(
        'photo.jpg',
        ['favorite'],
        tags,
        last_used
    )
    
    assert changed
    assert 'photo.jpg' in tags['favorite']
```

## Performance Considerations

### Media File Caching
- `get_all_media_files()` caches results in `STATE.all_media_files`
- Call `STATE.clear_media_cache()` after add/delete operations
- Speeds up repeated searches significantly

### Tag Sorting
- Tags sorted once on startup using `pinyin_order`
- Resort when tags added/removed via `STATE.update_sorted_tags()`
- Minimal performance impact since tag list is typically small (<1000)

### Lazy Loading
- Media files only loaded on-demand during browse/search
- Full scan only when needed (search/all_media)
- Browse operations fast (only reads directory)

