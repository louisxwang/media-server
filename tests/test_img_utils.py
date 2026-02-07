from src.media_server import img_utils


def test_get_file_list(tmp_path):
    p = tmp_path / "images"
    p.mkdir()
    (p / "a.png").write_text("x")
    (p / "b.jpg").write_text("y")
    (p / "c.txt").write_text("z")

    files = img_utils.get_file_list(str(p), extensions=(".png", ".jpg"))
    assert sorted(files) == ["a.png", "b.jpg"]


def test_get_xmp_tags_no_xmp(tmp_path):
    f = tmp_path / "img.jpg"
    f.write_bytes(b"no xmp here")
    tags = img_utils.get_xmp_tags(str(f))
    assert tags == []
