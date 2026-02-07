"""Regression test for tags page URL conversion bug.

This test ensures that the `/tags/<tag>` page yields media URLs
that use the configured `MEDIA_URL` prefix (e.g. `/static/...`) and
never embed absolute filesystem paths like `E:/...` in the rendered HTML.
"""
import importlib
import json

media_module = importlib.import_module('src.media_server.app')
media_app = media_module.app
from src.media_server.config import get_paths
from src.media_server.models import MediaState


def test_tags_page_uses_media_url_not_filesystem(tmp_path):
    # Project-root-like folder for this test
    project_root = tmp_path / "proj"
    project_root.mkdir()

    # Create a separate media folder and nested path
    media_root = tmp_path / "media_store"
    nested = media_root / "Poco X" / "202305" / "Real Photos"
    nested.mkdir(parents=True)

    # Create a sample media file
    filename = "1682837062936.jpg"
    (nested / filename).write_text("dummy")

    # Write config.json so MediaState will pick up this media_root
    config = {"STATIC_PATH": str(media_root)}
    (project_root / "config.json").write_text(json.dumps(config))

    # Create a MediaState that reads config from project_root
    state = MediaState(str(project_root))

    # Add a tag mapping that references the basename (what the app expects)
    tag_name = "testtag"
    state.tags = {tag_name: {filename}}
    state.update_sorted_tags()

    # Recompute paths for this test project and inject into app
    paths = get_paths(str(project_root))
    media_module.PATHS = paths
    media_module.STATE = state

    # Call page_for_medias directly under a test request context to render HTML
    with media_app.test_request_context(path=f"/tags/{tag_name}"):
        text = media_module.page_for_medias(state.tags[tag_name], tag_name)
        # If a response object is returned (render_template), ensure it's str
        if not isinstance(text, str):
            text = text.get_data(as_text=True)

    # The HTML should contain the configured media_url prefix (e.g. 'static')
    assert paths['media_url'] in text

    # The HTML must NOT contain the absolute filesystem path (no drive-letter paths)
    # Ensure the absolute static directory path is not embedded in the rendered HTML
    assert str(media_root) not in text
    assert str(media_root).replace('\\', '/') not in text

    # Also ensure the media entry for our file is present as a URL
    assert filename in text
