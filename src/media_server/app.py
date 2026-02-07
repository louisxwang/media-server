import os
import subprocess

from flask import Flask, jsonify, redirect, render_template, request, url_for

from src.media_server.browse import (
    filter_hidden_media,
    get_all_media_files,
    get_all_video_files,
    prepare_media_page,
    search_media_files,
)
from src.media_server.config import fs_to_url, get_paths, url_to_fs
from src.media_server.media_handlers import (
    delete_media,
    move_items,
    rename_media_file,
)
from src.media_server.models import MediaState, get_pinyin
from src.media_server.tag_handlers import merge_tags, update_tag_global_variables

# Initialize paths and state
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PATHS = get_paths(ROOT)
STATE = MediaState(ROOT)

# Configure Flask app
app = Flask(
    __name__,
    template_folder=PATHS['templates_dir'],
    static_folder=PATHS['static_dir'],
)
@app.route('/')
@app.route('/browse/<path:subpath>')
def Home(subpath=''):
    """Browse media by directory."""
    full_path = os.path.join(PATHS['static_dir'], subpath)
    print(f"Browsing: {full_path}")
    
    page_data = prepare_media_page(
        full_path,
        subpath,
        STATE.sorted_tags,
        STATE.tags,
        STATE.hidden_tags,
        PATHS['static_dir'],
        PATHS['media_url'],
        'Home',
    )
    
    if page_data is None:
        return redirect(url_for('Home'))
    
    return render_template(
        'index.html',
        tags=STATE.sorted_tags,
        directories=page_data['directories'],
        medias=page_data['media_paths'],
        previews=page_data['preview_paths'],
        breadcrumb_paths=page_data['breadcrumb_paths'],
        subpath=subpath,
        endpoint='Home',
        media_tags=page_data['media_tags'],
        last_used_tags=STATE.last_used_tags,
    )

@app.route('/search_media/<path:subpath>')
def search_media(subpath=''):
    """Search media files by keywords."""
    keywords = request.args.get('keywords', '').split('_')
    subpath = subpath.strip()
    full_path = os.path.join(PATHS['static_dir'], subpath)
    
    if not os.path.isdir(full_path):
        return redirect(url_for('Home'))
    
    results = search_media_files(
        full_path,
        keywords,
        STATE.all_media_files,
    )
    
    return page_for_medias(results, tagname='search')

@app.route('/all_media')
def all_media(subpath=''):
    """Get random sample of all media files."""
    full_path = os.path.join(PATHS['static_dir'], subpath)
    
    if not os.path.isdir(full_path):
        return redirect(url_for('Home'))
    
    import random
    media_files = get_all_media_files(full_path, STATE.all_media_files)
    media_files = filter_hidden_media(media_files, STATE.tags, STATE.hidden_tags)
    
    if len(media_files) > 99:
        media_files = random.choices(media_files, k=99)
    
    return page_for_medias([os.path.basename(f) for f in media_files], tagname='all_media')
    
@app.route('/all_videos')
def all_videos(subpath=''):
    """Browse all video files."""
    import random
    full_path = os.path.join(PATHS['static_dir'], subpath)
    
    if not os.path.isdir(full_path):
        return redirect(url_for('Home'))
    
    media_files = get_all_video_files(full_path, STATE.all_media_files, STATE.all_video_files)
    
    if len(media_files) > 99:
        media_files = random.choices(media_files, k=99)
    
    media_files = filter_hidden_media(media_files, STATE.tags, STATE.hidden_tags)
    # Convert filesystem paths to URL paths and compute previews
    media_paths = [fs_to_url(f, PATHS['static_dir'], PATHS['media_url']) for f in media_files]
    media_tags = [
        " ".join([
            tag for tag, _ in STATE.sorted_tags
            if tag in STATE.tags and os.path.basename(f) in STATE.tags[tag]
        ])
        for f in media_files
    ]
    preview_paths = []
    for f in media_files:
        basename = os.path.basename(f)
        b_no_ext, ext = os.path.splitext(basename)
        preview_fs = os.path.join(os.path.dirname(f), 'previews', f'{b_no_ext} preview{ext}').replace('\\', '/')
        if not os.path.isfile(preview_fs):
            preview_fs = f
        preview_paths.append(fs_to_url(preview_fs, PATHS['static_dir'], PATHS['media_url']))
    breadcrumb_paths = subpath.split('/') if subpath else []
    
    return render_template(
        'index.html',
        tags=STATE.sorted_tags,
        directories=[],
        medias=media_paths,
        previews=preview_paths,
        breadcrumb_paths=breadcrumb_paths,
        subpath=subpath,
        endpoint='Home',
        media_tags=media_tags,
        last_used_tags=STATE.last_used_tags,
    )

@app.route('/delete_multiple', methods=['POST'])
def delete_multiple():
    """Delete selected items."""
    data = request.get_json()
    items = [s.strip('/') for s in data.get('items', [])]
    endpoint = data.get('endpoint', '')
    
    success = True
    try:
        if endpoint == 'Tags':
            # Delete tags
            for tag in items:
                STATE.tags.pop(tag, None)
            STATE.save_tags()
        else:
            # Delete media files
            for item in items:
                success_item, error = delete_media(
                    item,
                    PATHS['media_url'],
                    PATHS['static_dir'],
                    PATHS['trash_dir'],
                )
                if not success_item:
                    print(f"Error deleting {item}: {error}")
                    success = False
    except Exception as e:
        print(f"Error in delete_multiple: {e}")
        success = False
    
    return jsonify(success=success)

@app.route('/delete', methods=['POST'])
def delete():
    """Delete a single media file."""
    data = request.get_json()
    media_path = data.get('path', '')
    
    if not media_path:
        return jsonify({'success': False, 'error': 'No path provided'})
    
    success, error = delete_media(
        media_path,
        PATHS['media_url'],
        PATHS['static_dir'],
        PATHS['trash_dir'],
    )
    
    return jsonify({'success': success, 'error': error if not success else ''})
    
@app.route('/rename', methods=['POST'])
def rename():
    """Rename a media file."""
    data = request.get_json()
    media_path = data.get('path', '')
    new_name = data.get('new_name', '')
    
    if not media_path or not new_name:
        return jsonify({'success': False, 'error': 'Path or new name not provided'})
    
    try:
        media_path_str = media_path.lstrip('/')
        
        # Validate URL prefix
        if not media_path_str.startswith(PATHS['media_url']):
            return jsonify({'success': False, 'error': 'File not under media folder'})
        
        fs_media = url_to_fs(media_path_str, PATHS['static_dir'], PATHS['media_url'])
        
        if not os.path.exists(fs_media):
            return jsonify({'success': False, 'error': 'File does not exist'})
        
        success, error, new_path, new_filename = rename_media_file(
            fs_media,
            new_name,
            STATE.tags,
            STATE.clips_data,
            PATHS['media_url'],
            PATHS['static_dir'],
        )
        
        if success:
            STATE.save_tags()
            STATE.save_clips()
            return jsonify({
                'success': True,
                'new_path': fs_to_url(new_path, PATHS['static_dir'], PATHS['media_url']),
                'new_pinyin': get_pinyin(new_filename),
            })
        else:
            return jsonify({'success': False, 'error': error})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/rename_multiple', methods=['POST'])
def rename_multiple():
    """Batch rename media or merge tags."""
    data = request.get_json()
    items = [s.strip('/') for s in data.get('items', [])]
    endpoint = data.get('endpoint', '')
    new_name = data.get('new_name', '')
    
    success = True
    try:
        if endpoint == 'Tags':
            # Merge tags
            merge_tags(items, new_name, STATE.tags)
            STATE.update_sorted_tags()
            STATE.save_tags()
        else:
            # Rename media/folders
            for item in items:
                try:
                    fs_item = url_to_fs(item, PATHS['static_dir'], PATHS['media_url'])
                    if os.path.isfile(fs_item):
                        # Rename file
                        dir_name, old_name = os.path.split(fs_item)
                        new_file_name = new_name.replace('#', old_name)
                        rename_media_file(
                            fs_item,
                            new_file_name,
                            STATE.tags,
                            STATE.clips_data,
                            PATHS['media_url'],
                            PATHS['static_dir'],
                        )
                    elif os.path.isdir(fs_item):
                        # Rename directory
                        new_path = os.path.join(os.path.dirname(fs_item), new_name)
                        os.rename(fs_item, new_path)
                except Exception as e:
                    print(f"Error renaming {item}: {e}")
                    success = False
            
            STATE.save_tags()
            STATE.save_clips()
    
    except Exception as e:
        print(f"Error in rename_multiple: {e}")
        success = False
    
    return jsonify(success=success)

@app.route('/cut_multiple', methods=['POST'])
def cut_multiple():
    """Cut media files to clipboard."""
    data = request.get_json()
    items = [s.strip('/') for s in data.get('items', [])]
    STATE.medias_in_clipboard = items
    return jsonify(success=True)


@app.route('/paste_multiple', methods=['POST'])
def paste_multiple():
    """Paste media files from clipboard."""
    data = request.get_json()
    destination = data.get('destination', '').strip('/')
    
    success, error = move_items(
        STATE.medias_in_clipboard,
        destination,
        PATHS['static_dir'],
        PATHS['media_url'],
    )
    
    STATE.medias_in_clipboard = []
    return jsonify(success=success)

@app.route('/video_clip_marker')
def mark_video_clips():
    """Show video clip marker interface."""
    video_file = request.args.get('video')
    return render_template('video_clip_marker.html', video_file=video_file)


@app.route('/settings', methods=['GET'])
def settings_page():
    """Show settings page."""
    return render_template('settings.html')


@app.route('/save_settings', methods=['POST'])
def save_settings():
    """Save user settings."""
    settings_dict = request.get_json()
    return render_template('settings.html')

@app.route('/save_clips', methods=['POST'])
def save_clips():
    """Save video clip data."""
    video = request.args.get('video')
    print("Saving clips for:", video)
    STATE.clips_data[video] = request.json
    STATE.save_clips()
    return jsonify({"status": "success"})


@app.route('/load_clips', methods=['GET'])
def load_clips():
    """Load video clip data."""
    video = request.args.get('video')
    return jsonify(STATE.clips_data.get(video, []))


@app.route('/clips')
def clips():
    """Show all saved clips."""
    new_dict = {
        '/' + '/'.join(name.split('/')[1:]): clips
        for name, clips in STATE.clips_data.items()
    }
    return render_template('clips.html', clips=new_dict)

def get_video_resolution(file: str) -> tuple[int, int]:
    """Get video resolution using ffprobe."""
    cmd = (
        f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height '
        f'-of csv=p=0  "{file}"'
    )
    output = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    ).stdout
    
    if output:
        try:
            w, h = [int(n) for n in output.strip().split()[0].split(',')]
            return w, h
        except (ValueError, IndexError):
            return 0, 0
    
    return 0, 0


@app.route('/gen_clips', methods=['POST'])
def gen_clips():
    """Generate video clips from timestamps."""
    video = request.args.get('video', '')[1:]
    basename, extension = os.path.splitext(video)
    
    try:
        timestamps = request.json.get('clips', [])
        resolution = int(request.json.get('resolution', 1))
        gen_preview = bool(request.json.get('gen_preview', False))
        
        res_cmd = ['-c', 'copy']
        if resolution != 1:
            w, h = get_video_resolution(video)
            if w == 0:
                w = h = resolution
            elif w > h:
                r = resolution / h
                w = int(w * r) // 2 * 2
                h = resolution
            else:
                r = resolution / w
                h = int(h * r) // 2 * 2
                w = resolution
            res_cmd = ['-vf', f'scale={w}:{h}']
        
        temp_file_contents = ""
        for t in timestamps:
            start, stop = t['start'], t['stop']
            output = f"{basename}_{start}_{stop}{extension}"
            temp_file_contents += f"file '{output}'\n"
            
            cmd = ['ffmpeg', '-v', 'error', '-y', '-i', video] + res_cmd + [
                '-ss', str(start), '-to', str(stop), output
            ]
            subprocess.run(cmd)
        
        if not gen_preview:
            print('Clips generated successfully')
            return jsonify({"status": "success"})
        
        # Generate preview
        with open('clips_files_tempo.txt', 'w', encoding='utf-8') as f:
            f.write(temp_file_contents)
        
        folder = os.path.dirname(video)
        basename_file = os.path.basename(video)
        basename_file, extension = os.path.splitext(basename_file)
        preview_path = os.path.join(folder, 'previews', f'{basename_file} preview{extension}')
        
        if not os.path.exists(os.path.join(folder, 'previews')):
            os.makedirs(os.path.join(folder, 'previews/'))
        
        cmd = [
            'ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0',
            '-i', 'clips_files_tempo.txt', preview_path
        ]
        subprocess.run(cmd)
        
        print('Preview generated successfully')
        return jsonify({"status": "success"})
    
    except Exception as e:
        print(f"Error generating clips: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get_tags', methods=['POST'])
def get_tags():
    """Get tags for a media file."""
    media = request.json.get('media', '')
    tag_list = [
        [tag, media in STATE.tags.get(tag, set())]
        for tag, _ in STATE.sorted_tags
    ]
    return jsonify(tag_list)


@app.route('/save_tags', methods=['POST'])
def save_tags():
    """Save tags for one or more media files."""
    tag_list = request.json.get('tags', [])
    medias = request.json.get('media', [])
    
    if not isinstance(medias, list):
        medias = [medias]
    
    changed = False
    for media in medias:
        media = media.split('/')[-1]
        media_changed = update_tag_global_variables(
            media,
            tag_list,
            STATE.tags,
            STATE.last_used_tags,
            allow_remove=False,
        )
        changed = changed or media_changed
    
    STATE.update_sorted_tags()
    if changed:
        STATE.save_tags()
    
    return jsonify({"status": "success"})

def page_for_medias(medias: list, tagname: str = '') -> str:
    """Render HTML page for given media names."""
    media_exts = ('.jpg', '.jpeg', '.png', '.webm', '.webp', '.mp4', '.gif', '.ogg')
    path_dict = {}
    
    for root, dirs, files in os.walk(PATHS['static_dir']):
        if PATHS['trash_dir'] not in root:
            for file in files:
                if file.lower().endswith(media_exts):
                    path_dict[file] = root.replace('\\', '/')
    
    # Filter existing media
    media_files = [
        media for media in medias
        if media in path_dict and os.path.isfile(
            os.path.join(path_dict[media], media)
        )
    ]
    
    # Apply hidden tags filter
    if tagname != 'hidden':
        media_files = [
            f for f in media_files
            if not any(f in STATE.tags.get(t, set()) for t in STATE.hidden_tags if t != tagname)
        ]
    
    # Sort by pinyin
    from src.hanzi_sort.hanzi_sort import pinyin_order
    media_files = sorted(media_files, key=pinyin_order)
    
    # Prepare media data
    media_tags = [
        [tag for tag, _ in STATE.sorted_tags if media in STATE.tags.get(tag, set())]
        for media in media_files
    ]
    
    # Convert filesystem paths to URL paths using fs_to_url
    media_paths = []
    preview_paths = []
    for file in media_files:
        fs_file = os.path.join(path_dict[file], file).replace('\\', '/')
        media_paths.append(fs_to_url(fs_file, PATHS['static_dir'], PATHS['media_url']))

        # compute preview file path and convert to URL
        basename_no_ext, extension = os.path.splitext(file)
        preview_fs = os.path.join(path_dict[file], 'previews', f'{basename_no_ext} preview{extension}').replace('\\', '/')
        if not os.path.isfile(preview_fs):
            preview_fs = fs_file
        preview_paths.append(fs_to_url(preview_fs, PATHS['static_dir'], PATHS['media_url']))
    
    return render_template(
        'index.html',
        tags=STATE.sorted_tags,
        directories=[],
        medias=media_paths,
        previews=preview_paths,
        breadcrumb_paths=[tagname],
        subpath='',
        endpoint='Tags',
        media_tags=media_tags,
        last_used_tags=STATE.last_used_tags,
    )


@app.route('/tags')
@app.route('/tags/<subpath>')
def Tags(subpath=''):
    """Get all medias with a given tag, or list all tags."""
    tagname = subpath
    
    if tagname and tagname in STATE.tags:
        return page_for_medias(STATE.tags[tagname], tagname)
    else:
        STATE.update_sorted_tags()
        return render_template(
            'index.html',
            tags=STATE.sorted_tags,
            directories=[],
            medias=[],
            previews=[],
            breadcrumb_paths=[],
            subpath='',
            endpoint='Tags',
            media_tags=[],
            last_used_tags=STATE.last_used_tags,
        )


@app.route('/filter_media_with_tags')
def filter_media_with_tags():
    """Filter media by multiple tags with AND/OR/HIDE operations."""
    op = request.args.get('op', 'and')
    selected_tags = request.args.get('tags', '').split('_')
    
    if op == 'hide':
        # Toggle hidden tags
        STATE.hidden_tags = STATE.hidden_tags ^ set(selected_tags)
        STATE.save_tags()
        return Tags()
    
    # Calculate intersection or union
    medias = set()
    if op == 'and':
        medias = STATE.tags.get(selected_tags[0], set()).copy()
        for tag in selected_tags[1:]:
            medias = medias.intersection(STATE.tags.get(tag, set()))
        print('AND filter applied')
    elif op == 'or':
        for tag in selected_tags:
            medias = medias.union(STATE.tags.get(tag, set()))
        print('OR filter applied')
    
    print(f'{len(medias)} medias in filter result')
    tagname = f'{op}({",".join(selected_tags)})'
    return page_for_medias(medias, tagname=tagname)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
