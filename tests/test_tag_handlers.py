"""Tests for tag_handlers module."""

from src.media_server.tag_handlers import (
    merge_tags,
    update_tag_global_variables,
)


class TestUpdateTagGlobalVariables:
    """Test tag update functionality."""
    
    def test_add_new_tag_to_media(self):
        """Test adding a new tag to media."""
        tags = {}
        last_used = []
        
        changed = update_tag_global_variables(
            'photo.jpg',
            ['nature'],
            tags,
            last_used,
        )
        
        assert changed
        assert 'photo.jpg' in tags['nature']
        assert 'nature' in last_used
    
    def test_add_existing_tag_to_media(self):
        """Test adding existing tag to media."""
        tags = {'nature': {'other.jpg'}}
        last_used = []
        
        changed = update_tag_global_variables(
            'photo.jpg',
            ['nature'],
            tags,
            last_used,
        )
        
        assert changed
        assert 'photo.jpg' in tags['nature']
        assert 'other.jpg' in tags['nature']
    
    def test_add_multiple_tags(self):
        """Test adding multiple tags to media."""
        tags = {}
        last_used = []
        
        changed = update_tag_global_variables(
            'photo.jpg',
            ['nature', 'outdoor', 'summer'],
            tags,
            last_used,
        )
        
        assert changed
        assert 'photo.jpg' in tags['nature']
        assert 'photo.jpg' in tags['outdoor']
        assert 'photo.jpg' in tags['summer']
        assert len(last_used) == 3
    
    def test_tag_already_on_media(self):
        """Test adding tag that media already has."""
        tags = {'nature': {'photo.jpg'}}
        last_used = []
        
        changed = update_tag_global_variables(
            'photo.jpg',
            ['nature'],
            tags,
            last_used,
        )
        
        assert not changed  # No change since tag already there
    
    def test_last_used_tags_limit(self):
        """Test that last_used_tags stays limited to 10."""
        tags = {}
        last_used = []
        
        # Add 12 different tags
        for i in range(12):
            update_tag_global_variables(
                f'photo_{i}.jpg',
                [f'tag_{i}'],
                tags,
                last_used,
            )
        
        assert len(last_used) == 10
        assert 'tag_0' not in last_used  # Oldest should be removed
        assert 'tag_11' in last_used  # Newest should be there
    
    def test_remove_tag_with_allow_remove(self):
        """Test removing tag with allow_remove=True."""
        tags = {'nature': {'photo.jpg'}, 'outdoor': {'photo.jpg'}}
        last_used = []
        
        changed = update_tag_global_variables(
            'photo.jpg',
            ['nature'],
            tags,
            last_used,
            allow_remove=True,
        )
        
        assert changed
        assert 'photo.jpg' in tags['nature']
        assert 'photo.jpg' not in tags['outdoor']
    
    def test_no_remove_without_allow_remove(self):
        """Test that tags aren't removed without allow_remove."""
        tags = {'nature': {'photo.jpg'}, 'outdoor': {'photo.jpg'}}
        last_used = []
        
        changed = update_tag_global_variables(
            'photo.jpg',
            ['nature'],
            tags,
            last_used,
            allow_remove=False,
        )
        
        # outdoor tag should remain even though not in new list
        assert 'photo.jpg' in tags['outdoor']


class TestMergeTags:
    """Test tag merging functionality."""
    
    def test_merge_two_tags(self):
        """Test merging two tags."""
        tags = {
            'tag1': {'photo1.jpg', 'photo2.jpg'},
            'tag2': {'photo3.jpg'},
        }
        
        merge_tags(['tag1', 'tag2'], 'merged', tags)
        
        assert 'merged' in tags
        assert tags['merged'] == {'photo1.jpg', 'photo2.jpg', 'photo3.jpg'}
        assert 'tag1' not in tags
        assert 'tag2' not in tags
    
    def test_merge_multiple_tags(self):
        """Test merging multiple tags."""
        tags = {
            'tag1': {'photo1.jpg'},
            'tag2': {'photo2.jpg'},
            'tag3': {'photo3.jpg'},
        }
        
        merge_tags(['tag1', 'tag2', 'tag3'], 'all', tags)
        
        assert tags['all'] == {'photo1.jpg', 'photo2.jpg', 'photo3.jpg'}
        assert 'tag1' not in tags
        assert 'tag2' not in tags
        assert 'tag3' not in tags
    
    def test_merge_into_existing_tag(self):
        """Test merging into an existing tag."""
        tags = {
            'tag1': {'photo1.jpg'},
            'tag2': {'photo2.jpg'},
            'merged': {'photo0.jpg'},
        }
        
        merge_tags(['tag1', 'tag2'], 'merged', tags)
        
        assert tags['merged'] == {'photo0.jpg', 'photo1.jpg', 'photo2.jpg'}
    
    def test_merge_with_overlapping_media(self):
        """Test merge with overlapping media in tags."""
        tags = {
            'tag1': {'photo1.jpg', 'common.jpg'},
            'tag2': {'photo2.jpg', 'common.jpg'},
        }
        
        merge_tags(['tag1', 'tag2'], 'merged', tags)
        
        # common.jpg should appear only once (it's a set)
        assert tags['merged'] == {'photo1.jpg', 'photo2.jpg', 'common.jpg'}
        assert len(tags['merged']) == 3
