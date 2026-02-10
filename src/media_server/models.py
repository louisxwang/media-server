"""Global state management for media server."""
import pickle
from pathlib import Path

from src.hanzi_sort.hanzi_sort import pinyin_index, pinyin_order


def _get_media_root(root_path: str) -> Path:
    """Get the media root directory from config.json."""
    import json
    config_path = Path(root_path) / 'config.json'
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f) or {}
                media_path = config.get('MEDIA_PATH')
                if media_path:
                    return Path(media_path)
        except Exception:
            pass
    
    # Fallback to root/static if config not found or MEDIA_PATH not set
    return Path(root_path) / 'static'


class MediaState:
    """Manages global state for media, tags, and clips."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.media_root = _get_media_root(str(self.root_path))
        self.db_dir = self.media_root / '.database'
        self.tags = {}
        self.sorted_tags = []
        self.hidden_tags = set()
        self.last_used_tags = []
        self.clips_data = {}
        self.all_media_files = []
        self.all_video_files = []
        self.medias_in_clipboard = []
        
        self._load_tags()
        self._load_clips()
        
        # Create pickle files if they don't exist
        if not (self.db_dir / 'tags.pkl').exists():
            self.save_tags()
        if not (self.db_dir / 'clip_data.pkl').exists():
            self.save_clips()
    
    def _load_tags(self):
        """Load tags from pickle file in .database subfolder."""
        tags_file = self.db_dir / 'tags.pkl'
        
        try:
            with open(tags_file, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    raw_tags = data
                    self.hidden_tags = set()
                    self.last_used_tags = []
                elif len(data) == 2:
                    raw_tags, self.hidden_tags = data
                    self.last_used_tags = []
                else:
                    raw_tags, self.hidden_tags, self.last_used_tags = data
                
                # Clean and load tags
                for tag, file_set in raw_tags.items():
                    if ' ' not in tag and len(file_set) > 0:
                        self.tags[tag] = set(
                            file_path.replace("\\", "/") for file_path in file_set
                        )
        except Exception as e:
            print(f"Can't load saved tags data: {e}")
            self.tags = {'best': set()}
        
        self.update_sorted_tags()
    
    def _load_clips(self):
        """Load clip data from pickle file in .database subfolder."""
        clips_file = self.db_dir / 'clip_data.pkl'
        
        try:
            with open(clips_file, 'rb') as f:
                self.clips_data = pickle.load(f)
        except Exception as e:
            print(f"Can't load saved clip data: {e}")
            self.clips_data = {}
    
    def save_tags(self):
        """Save tags to pickle file in .database subfolder."""
        # Ensure .database subfolder exists
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        tags_file = self.db_dir / 'tags.pkl'
        with open(tags_file, 'wb') as f:
            pickle.dump([self.tags, self.hidden_tags, self.last_used_tags], f)
        
        # Also save timestamped backup
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        backup_file = self.db_dir / f'tags_{date_str}.pkl'
        with open(backup_file, 'wb') as f:
            pickle.dump([self.tags, self.hidden_tags], f)
    
    def save_clips(self):
        """Save clip data to pickle file in .database subfolder."""
        # Ensure .database subfolder exists
        self.db_dir.mkdir(parents=True, exist_ok=True)
        clips_file = self.db_dir / 'clip_data.pkl'
        with open(clips_file, 'wb') as f:
            pickle.dump(self.clips_data, f)
    
    def update_sorted_tags(self):
        """Update sorted tag list."""
        sorted_tags = sorted(self.tags.keys(), key=pinyin_order)
        tags_pinyin = [get_pinyin(tag) for tag in sorted_tags]
        
        self.sorted_tags = [
            (tag, pinyin) for tag, pinyin in zip(sorted_tags, tags_pinyin)
            if len(self.tags[tag]) > 0 and tag.isalnum()
        ]
    
    def clear_media_cache(self):
        """Clear cached media file lists."""
        self.all_media_files = []
        self.all_video_files = []


def get_pinyin(word: str) -> str:
    """Get pinyin representation of a word."""
    # Special cases
    special_words = {
        '倔强': 'JJ',
        '调皮': 'TP',
        '特摄': 'TS',
    }
    
    if word in special_words:
        return special_words[word]
    
    pinyins = []
    for c in word:
        pinyin = pinyin_index.get(c)
        if pinyin is not None:
            pinyins.append(pinyin[0])
        else:
            pinyins.append(c)
    
    if len(pinyins) == 1 and pinyins[0] != word:
        return pinyins[0][:3]
    
    return ''.join(pinyins)
