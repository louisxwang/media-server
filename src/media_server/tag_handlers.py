"""Tag management operations."""


def update_tag_global_variables(
    media: str,
    tag_list: list[str],
    tags_state: dict,
    last_used_tags: list,
    allow_remove: bool = False,
) -> bool:
    """Update tags for a media file."""
    changed = False
    
    # Add new tags if they don't exist
    for tag in tag_list:
        if tag not in tags_state:
            tags_state[tag] = set()
            changed = True
    
    # Update tags for the media
    for tag, medias in tags_state.items():
        if tag in tag_list and media not in medias:
            # Add tag to media
            changed = True
            medias.add(media)
            
            # Update last_used_tags
            if tag in last_used_tags:
                last_used_tags.remove(tag)
            last_used_tags.append(tag)
            
            if len(last_used_tags) > 10:
                last_used_tags.pop(0)
        
        elif allow_remove and tag not in tag_list and media in medias:
            # Remove tag from media
            changed = True
            medias.remove(media)
    
    return changed


def merge_tags(
    source_tags: list[str],
    dest_tag: str,
    tags_state: dict,
) -> None:
    """Merge multiple tags into one."""
    medias = tags_state.get(dest_tag, set()).copy()
    
    for tag in source_tags:
        if tag in tags_state:
            medias |= tags_state[tag]
    
    # Remove source tags and set destination tag
    for tag in source_tags:
        tags_state.pop(tag, None)
    
    tags_state[dest_tag] = medias
