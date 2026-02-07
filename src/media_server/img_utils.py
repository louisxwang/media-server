"""Contains image processing utilities."""
import os

from PIL import Image


def get_file_list(full_path, extensions=('.png',)):
    """Get all files under given folder"""
    print(f"Python getting file list from {full_path}")
    files = []
    if os.path.isdir(full_path):
        items = os.listdir(full_path)
        directories = [item for item in items if os.path.isdir(os.path.join(full_path, item))]
        files = [item for item in items if item.lower().endswith(extensions)]
        
    return files

def convert_to_jpg(file_path):
    """Find an image and convert to jpg."""
    img = Image.open(file_path)
    rgb_im = img.convert('RGB')
    rgb_im.save(file_path[:-3] + 'jpg')

# Extract XMP Data
def get_xmp_tags(file_path):
    """Extract XMP tags from an image file."""
    with open(file_path, 'rb') as f:
        d = f.read()
    xmp_start = d.find(b'<x:xmpmeta')
    xmp_end = d.find(b'</x:xmpmeta')
    if xmp_start == -1 or xmp_end == -1:
        return []
    xmp_str = d[xmp_start:xmp_end+12].decode(errors='ignore')

    if '<rdf:Bag>' in xmp_str:
        rdf_bag_str = xmp_str[xmp_str.find('<rdf:Bag>')+9:xmp_str.find('</rdf:Bag>')]
    else:
        rdf_bag_str = ''

    raw_tags = [item[8:-9] for item in rdf_bag_str.split() if len(item)>16]
    tags = []
    for tag in raw_tags:
        for i, c in enumerate(tag):
            if not (c>='a' and c<='z'):
                break
        tags.append(tag[i:])

    return tags
"""Contains image processing utilities."""

def get_file_list(full_path, extensions=('.png',)):
    """Get all files under given folder"""
    print(f"Python getting file list from {full_path}")
    files = []
    if os.path.isdir(full_path):
        items = os.listdir(full_path)
        directories = [item for item in items if os.path.isdir(os.path.join(full_path, item))]
        files = [item for item in items if item.lower().endswith(extensions)]
        
    return files

def convert_to_jpg(file_path):
    """Find an image and convert to jpg."""
    img = Image.open(file_path)
    rgb_im = img.convert('RGB')
    rgb_im.save(file_path[:-3] + 'jpg')

# Extract XMP Data
def get_xmp_tags(file_path):
    """Extract XMP tags from an image file."""
    with open(file_path, 'rb') as f:
        d = f.read()
    xmp_start = d.find(b'<x:xmpmeta')
    xmp_end = d.find(b'</x:xmpmeta')
    if xmp_start == -1 or xmp_end == -1:
        return []
    xmp_str = d[xmp_start:xmp_end+12].decode(errors='ignore')

    if '<rdf:Bag>' in xmp_str:
        rdf_bag_str = xmp_str[xmp_str.find('<rdf:Bag>')+9:xmp_str.find('</rdf:Bag>')]
    else:
        rdf_bag_str = ''

    raw_tags = [item[8:-9] for item in rdf_bag_str.split() if len(item)>16]
    tags = []
    for tag in raw_tags:
        for i, c in enumerate(tag):
            if not (c>='a' and c<='z'):
                break
        tags.append(tag[i:])

    return tags
