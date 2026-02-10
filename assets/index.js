// Global variables from template
var currentIndex = -1;

// Touch screen gesture variables
var initialDistance = 0;
var initialScale = 1;
var initialX = 0;
var initialY = 0;
var isSwiping = false;

// DOM elements cache
const tagNameInput = document.getElementById('tagNameInput');
const tagModal = document.getElementById('tagSelect');
var modalMenu = document.getElementById("modalMenu");

/**
 * Open media in modal
 */
function openModal(mediaElement, type) {
    pauseAllVideos();
    var modal = document.getElementById('mediaModal');
    var modalImg = document.getElementById('img01');
    var modalVideo = document.getElementById('video01');
    var mediaName = document.getElementById('mediaName');
    var currentMediaTags = document.getElementById('currentMediaTags');
    var currentMedia = mediaElement.getAttribute('data-full');
    var currentMediaName = currentMedia.split('/').pop();

    mediaName.textContent = currentMediaName;
    currentIndex = medias.indexOf(currentMedia);
    currentMediaTags.textContent = media_tags[currentIndex] || '--';
    console.log(currentIndex);

    modal.style.display = "block";
    if (type === 'image') {
        modalVideo.style.display = "none";
        modalImg.src = currentMedia;
        modalImg.style.display = "block";
    } else if (type === 'video') {
        modalImg.style.display = "none";
        modalVideo.src = currentMedia;
        modalVideo.style.display = "block";
    }

    document.getElementById('bottomBar').style.display = 'none';
}

/**
 * Close modal and resume page functionality
 */
function closeModal() {
    var modal = document.getElementById('mediaModal');
    modal.style.display = "none";
    var modalVideo = document.getElementById('video01');
    modalVideo.pause();
    if (document.fullscreenElement === modal) {
        document.exitFullscreen().catch(err => console.error(err));
    }
    lazyVideoLoad();
    closeTagModal();
    document.getElementById('bottomBar').style.display = 'block';
}

/**
 * Change to previous/next media in modal
 */
function changeMedia(step) {
    var gridItems = document.querySelectorAll('.grid-item.media-item');

    currentIndex += step;
    if (currentIndex >= medias.length) {
        currentIndex = 0;
    } else if (currentIndex < 0) {
        currentIndex = medias.length - 1;
    }

    // Skip hidden items
    while (gridItems[currentIndex] && gridItems[currentIndex].style.display == 'none') {
        currentIndex += step < 0 ? -1 : 1;
        if (currentIndex >= medias.length) {
            currentIndex = 0;
        } else if (currentIndex < 0) {
            currentIndex = medias.length - 1;
        }
    }

    var modalImg = document.getElementById('img01');
    var modalVideo = document.getElementById('video01');
    var mediaName = document.getElementById('mediaName');
    var currentMediaTags = document.getElementById('currentMediaTags');

    var currentMedia = medias[currentIndex];
    var currentMediaName = currentMedia.split('/').pop();
    mediaName.textContent = currentMediaName;
    currentMediaTags.textContent = media_tags[currentIndex] || '--';
    toggleSelectedInTagModal();

    if (currentMedia.endsWith('.mp4') || currentMedia.endsWith('.webm')) {
        modalVideo.src = currentMedia;
        modalVideo.style.display = "block";
        modalImg.style.display = "none";
    } else {
        modalImg.src = currentMedia;
        modalImg.style.display = "block";
        modalVideo.pause();
        modalVideo.style.display = "none";
    }

    closeTagModal();
}

/**
 * Toggle full screen mode
 */
function toggleFullScreen() {
    var modalContentContainer = document.getElementById('mediaModal');
    var fullScreenBtn = document.getElementById('fullscreen-btn');
    if (!document.fullscreenElement) {
        if (modalContentContainer.requestFullscreen) {
            modalContentContainer.requestFullscreen();
        } else if (modalContentContainer.mozRequestFullScreen) {
            modalContentContainer.mozRequestFullScreen();
        } else if (modalContentContainer.webkitRequestFullscreen) {
            modalContentContainer.webkitRequestFullscreen();
        } else if (modalContentContainer.msRequestFullscreen) {
            modalContentContainer.msRequestFullscreen();
        }
        fullScreenBtn.textContent = '>|<';
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        fullScreenBtn.textContent = '⛶';
    }
}

/**
 * Zoom in/out on images
 */
function zoomIn() {
    var modalImg = document.getElementById('img01');
    var modalVideo = document.getElementById('video01');
    if (modalImg.style.display !== "none") {
        modalImg.style.scale = modalImg.style.scale === '2' ? '1' : '2';
    } else if (modalVideo.style.display !== "none") {
        modalVideo.style.scale = modalVideo.style.scale === '2' ? '1' : '2';
    }
}

/**
 * Delete currently displayed media
 */
function deleteMedia() {
    if (!confirm('Are you sure you want to delete this media?')) {
        return;
    }
    toggleModalMenu();
    var mediaSrc = medias[currentIndex];
    fetch('/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: mediaSrc }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                medias.splice(currentIndex, 1);
                media_tags.splice(currentIndex, 1);
                changeMedia(0);
            } else {
                alert('Error deleting media: ' + data.error);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });

    var gridItems = document.querySelectorAll('.grid-item');
    if (gridItems[currentIndex]) {
        gridItems[currentIndex].remove();
    }
}

/**
 * Search media by keywords in current directory
 */
function searchMedia(searchInput) {
    var searchWords = searchInput.value.toLowerCase().split(' ').filter(word => word);
    console.log(searchWords);
    var gridItems = document.querySelectorAll('.grid-item');
    gridItems.forEach(item => {
        var mediaName = item.getAttribute('data-name').toLowerCase().split('/').slice(-1)[0];
        mediaName = mediaName.split('.').slice(0, -1).join('.');
        var matches = searchWords.every(word => mediaName.includes(word));
        item.style.display = matches ? 'block' : 'none';
    });

    var tagItems = document.querySelectorAll('.tag-button');
    tagItems.forEach(item => {
        var tagName = item.getAttribute('data-name').toLowerCase();
        var tagPinyin = item.getAttribute('data-pinyin').toLowerCase();
        var matches = searchWords.every(word => tagName.includes(word) || tagPinyin.includes(word));
        item.style.display = matches ? 'inline-block' : 'none';
    });
}

/**
 * Global search across all media
 */
function searchMediaGlobal() {
    var searchInput = document.getElementById('searchBar');
    var searchWords = searchInput.value.toLowerCase().split(' ').filter(word => word);
    var path = subpath === '' ? ' ' : subpath;
    var url = encodeURI('/search_media/' + path + '?keywords=' + searchWords.join('_'));
    console.log(url);
    window.location.href = url;
}

/**
 * Search tags in tag modal
 */
function searchTagModal() {
    var searchWords = tagNameInput.value.toLowerCase().split(' ').filter(word => word);
    var tagItems = document.querySelectorAll('.tag-modal-button');
    tagItems.forEach(item => {
        var tagName = item.getAttribute('data-name').toLowerCase();
        var tagPinyin = item.getAttribute('data-pinyin').toLowerCase();
        var matches = searchWords.every(word => tagName.includes(word) || tagPinyin.includes(word));
        item.style.display = matches ? 'inline-block' : 'none';
    });
}

/**
 * Show only selected tags in modal
 */
function showOnlySelectedTagInModal() {
    var tagItems = document.querySelectorAll('.tag-modal-button');
    tagItems.forEach(item => {
        var matches = item.classList.contains('selected');
        item.style.display = matches ? 'inline-block' : 'none';
    });
}

/**
 * Show last used tags in modal
 */
function showLastUsedTagInModal() {
    console.log(last_used_tags, typeof (last_used_tags));
    var tagItems = document.querySelectorAll('.tag-modal-button');
    tagItems.forEach(item => {
        var tagName = item.getAttribute('data-name');
        var matches = last_used_tags.includes(tagName);
        item.style.display = matches ? 'inline-block' : 'none';
    });
}

/**
 * Rename current media
 */
function renameMedia() {
    var mediaSrc = medias[currentIndex];
    var oldName = mediaSrc.split('/').pop();
    var extension = oldName.split('.').pop();
    var baseName = oldName.replace(/\.[^/.]+$/, "");
    var newName = prompt("Enter new name for the media (without extension):", baseName);
    if (newName && newName !== baseName) {
        fetch('/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: mediaSrc, new_name: newName }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    var oldMediaSrc = mediaSrc;
                    var newMediaSrc = oldMediaSrc.replace(/\/[^\/]+$/, '/' + newName + '.' + extension);
                    medias[currentIndex] = newMediaSrc;

                    var modalImg = document.getElementById('img01');
                    var modalVideo = document.getElementById('video01');
                    var mediaName = document.getElementById('mediaName');

                    if (modalImg.style.display !== "none") {
                        modalImg.src = newMediaSrc;
                    } else if (modalVideo.style.display !== "none") {
                        modalVideo.src = newMediaSrc;
                    }
                    mediaName.textContent = newName + '.' + extension;
                } else {
                    alert('Error renaming media: ' + data.error);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    }
}

/**
 * Load lazy videos when they enter viewport
 */
function lazyVideoLoad() {
    var lazyVideos = [].slice.call(document.querySelectorAll("video.lazy"));
    if ("IntersectionObserver" in window) {
        var lazyVideoObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (videoObserver) {
                video = videoObserver.target;
                if (videoObserver.isIntersecting) {
                    if (!video.src) {
                        video.src = video.getAttribute('data-src');
                        video.load();
                    } else if (video.paused) {
                        video.play();
                    }
                } else {
                    video.pause();
                }
            });
        });

        lazyVideos.forEach(function (lazyVideo) {
            lazyVideoObserver.observe(lazyVideo);
        });
    }
}

/**
 * Pause all videos on the page
 */
function pauseAllVideos() {
    var videos = document.querySelectorAll('.grid-item video');
    videos.forEach(video => {
        video.pause();
    });
}

/**
 * Navigate to video clip marker page
 */
function clipMedia() {
    var currentMedia = medias[currentIndex];
    if (currentMedia.endsWith('.mp4') || currentMedia.endsWith('.webm')) {
        window.location.href = '/video_clip_marker?video=' + encodeURIComponent(currentMedia);
    }
}

/**
 * Toggle tag button selection state
 */
function toggleSelected(elem) {
    elem.classList.toggle('selected');
}

/**
 * Pre-select all existing tags in tag modal
 */
function toggleSelectedInTagModal() {
    const buttons = document.querySelectorAll('.tag-modal-button');
    buttons.forEach(button => {
        if (currentIndex != -1 && media_tags[currentIndex].includes(button.getAttribute('data-name'))) {
            button.classList.add('selected');
        } else {
            button.classList.remove('selected');
        }
    });
}

/**
 * Show tag modal for single media
 */
function showTagModal() {
    toggleSelectedInTagModal();
    tagModal.style.display = "block";
    modalMenu.style.display = "none";
}

/**
 * Close tag modal
 */
function closeTagModal() {
    tagModal.style.display = "none";
}

/**
 * Toggle tag modal (grid view)
 */
function toggleTagModal() {
    if (tagModal.style.display == "block") {
        closeModal();
    } else {
        currentIndex = -1;
        showTagModal();
    }
}

/**
 * Create new tag
 */
function createNewTag() {
    var new_tag = tagNameInput.value.trim();
    var new_tag_pinyin = 'abcdefghijklmnopqrstuvwxyz';
    var new_tag_button = document.createElement("button");
    new_tag_button.setAttribute('class', 'tag-modal-button');
    new_tag_button.setAttribute('data-name', new_tag);
    new_tag_button.setAttribute('data-pinyin', new_tag_pinyin);
    new_tag_button.onclick = function () { toggleSelected(new_tag_button); };
    new_tag_button.innerHTML = new_tag;
    var tagModalButtons = document.getElementById('existingTags');
    tagModalButtons.appendChild(new_tag_button);
    saveTags(new_tag);
}

/**
 * Clear tag input
 */
function clearInput() {
    tagNameInput.value = '';
    tagNameInput.focus();
    searchTagModal();
}

/**
 * Get all selected tags
 */
function get_selected_tags() {
    var selectedTags = [];
    const buttons = document.querySelectorAll('.tag-modal-button.selected');
    buttons.forEach(button => {
        var tag_name = button.getAttribute('data-name');
        selectedTags.push(tag_name);
        if (currentIndex == -1 || !media_tags[currentIndex].includes(tag_name)) {
            if (!last_used_tags.includes(tag_name)) {
                last_used_tags.push(tag_name);
                if (last_used_tags.length > 10) {
                    last_used_tags.shift();
                }
            }
        }
    });
    return selectedTags;
}

/**
 * Save tags for media
 */
function saveTags(create_new_tag = '') {
    var selectedTags = get_selected_tags();
    var mediaModal = document.getElementById('mediaModal');
    var currentMediaTags = document.getElementById('currentMediaTags');
    var currentMedia = '';

    if (mediaModal.style.display == "none") {
        // In grid view
        var selectedGridItems = document.querySelectorAll('.grid-checkbox:checked');
        var selectedMediaNames = Array.from(selectedGridItems).map(item => item.dataset.name);
        currentMedia = selectedMediaNames;

        selectedMediaNames.forEach(media => {
            currentIndex = medias.indexOf(media);
            media_tags[currentIndex] = media_tags[currentIndex].concat(selectedTags);
            currentMediaTags.textContent = media_tags[currentIndex];
        });
    } else {
        // For current displayed media
        media_tags[currentIndex] = selectedTags;
        currentMediaTags.textContent = media_tags[currentIndex];
        currentMedia = medias[currentIndex];
    }

    console.log(currentMedia, selectedTags);
    fetch('/save_tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media: currentMedia, tags: selectedTags })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save tags.');
            }
        })
        .catch(error => {
            console.error(error);
        });

    if (create_new_tag == '') {
        closeTagModal();
    }
}

/**
 * Toggle media name display
 */
function toggleMediaName() {
    var nameText = document.getElementById('mediaName');
    nameText.style.display = nameText.style.display === "block" ? "none" : "block";
}

/**
 * Navigate to folder containing current media with focus
 */
function goToLocation() {
    var currentMedia = medias[currentIndex];
    var folder = currentMedia.split('/').slice(2, -1).join('/');
    window.location.href = '/browse/' + folder + '?focus=' + encodeURIComponent(currentMedia);
}

/**
 * Focus media from URL parameter and scroll into view
 */
function focusMediaFromURL() {
    try {
        const params = new URLSearchParams(window.location.search);
        const focus = params.get('focus');
        if (!focus) return;

        const gridItems = document.querySelectorAll('.grid-item');
        for (const item of gridItems) {
            if (item.dataset.name === focus) {
                item.style.display = 'block';
                item.scrollIntoView({ behavior: 'smooth', block: 'center' });

                const origBox = item.style.boxShadow;
                item.style.boxShadow = '0 0 0 4px rgba(255, 215, 0, 0.9)';
                setTimeout(() => { item.style.boxShadow = origBox; }, 2500);
                break;
            }
        }
    } catch (e) {
        console.error('focusMediaFromURL error', e);
    }
}

/**
 * Toggle modal menu
 */
function toggleModalMenu() {
    var modalMenu = document.getElementById("modalMenu");
    if (modalMenu.style.display === "block") {
        modalMenu.style.display = "none";
    } else {
        modalMenu.style.display = "block";
    }
    var clipButton = document.getElementById("clipButton");
    var currentMedia = medias[currentIndex];
    if (currentMedia.endsWith('.mp4') || currentMedia.endsWith('.webm')) {
        clipButton.style.display = "block";
    } else {
        clipButton.style.display = "none";
    }
}

/**
 * Toggle side menu
 */
function toggleSideMenu() {
    var sideMenu = document.getElementById('sideMenu');
    sideMenu.classList.toggle("open");
}

/**
 * Fold side menu
 */
function foldSideMenu() {
    var sideMenu = document.getElementById('sideMenu');
    sideMenu.classList.remove("open");
}

/**
 * Toggle media checkboxes for multi-select
 */
function toggleMediaCheckbox() {
    const checkboxElements = document.querySelectorAll('.grid-checkbox');
    const selectedItems = document.querySelectorAll('.grid-checkbox:checked');
    if (checkboxElements[0].style.display != 'block') {
        checkboxElements.forEach(item => {
            item.style.display = 'block';
        });
    } else if (checkboxElements.length != selectedItems.length) {
        checkboxElements.forEach(item => {
            item.checked = true;
        });
    } else {
        checkboxElements.forEach(item => {
            item.checked = false;
            item.style.display = 'none';
        });
    }
}

/**
 * Delete selected items
 */
function deleteSelected() {
    const selectedItems = document.querySelectorAll('.grid-checkbox:checked');
    const selectedNames = Array.from(selectedItems).map(item => item.dataset.name);

    if (selectedNames.length > 0) {
        if (!confirm('Are you sure you want to delete this media?')) {
            return;
        }
        fetch('/delete_multiple', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: selectedNames, endpoint: endpoint }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    selectedItems.forEach(item => item.closest('.grid-item').remove());
                    selectedNames.forEach(item => {
                        var idx = medias.indexOf(item);
                        medias.splice(idx, 1);
                        media_tags.splice(idx, 1);
                    });
                } else {
                    alert('Failed to delete selected items');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    } else {
        alert('No items selected');
    }
}

/**
 * Rename selected items
 */
function renameSelected() {
    const selectedItems = document.querySelectorAll('.grid-checkbox:checked');
    const selectedNames = Array.from(selectedItems).map(item => item.dataset.name);
    if (selectedNames.length > 0) {
        var newName = prompt("Enter new name (with extension if there is), use # as original name placeholder", "");
        if (!confirm('Are you sure you want to rename?')) {
            return;
        }
        fetch('/rename_multiple', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: selectedNames, endpoint: endpoint, new_name: newName }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Failed to rename selected items');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    } else {
        alert('No items selected');
    }
}

/**
 * Cut selected items
 */
function cutSelected() {
    const selectedItems = document.querySelectorAll('.grid-checkbox:checked');
    const selectedNames = Array.from(selectedItems).map(item => item.dataset.name);

    if (selectedNames.length > 0) {
        fetch('/cut_multiple', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: selectedNames, endpoint: endpoint }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Do nothing
                } else {
                    alert('Failed to cut selected items');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    } else {
        alert('No items selected');
    }
}

/**
 * Paste selected items
 */
function pasteSelected() {
    fetch('/paste_multiple', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination: subpath, endpoint: endpoint }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to paste selected items');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

/**
 * Filter media by tags
 */
function filterMediaWithTags(operation) {
    const selectedItems = document.querySelectorAll('.grid-checkbox:checked');
    const selectedNames = Array.from(selectedItems).map(item => item.dataset.name);

    if (selectedNames.length > 0) {
        console.log(selectedNames);
        var url = encodeURI('/filter_media_with_tags?op=' + operation + '&tags=' + selectedNames.join('_'));
        console.log(url);
        window.location.href = url;
    } else {
        alert('No items selected');
    }
}

// Event listeners setup
document.addEventListener("DOMContentLoaded", function () {
    lazyVideoLoad();
    focusMediaFromURL();
});
document.addEventListener("scroll", lazyVideoLoad);
document.addEventListener("scroll", foldSideMenu);

// Click on left/right of modal to change media
(function () {
    var mediaModal = document.getElementById('mediaModal');
    if (!mediaModal) return;

    mediaModal.addEventListener('click', function (e) {
        var controlSelectors = [
            '.prev',
            '.next',
            '.menu-btn',
            '#modalMenu',
            '.modal-menu',
            '.close',
            '.tag-modal-button',
            '#mediaName',
            '#currentMediaTags'
        ];

        for (var i = 0; i < controlSelectors.length; i++) {
            if (e.target.closest(controlSelectors[i])) {
                return;
            }
        }

        var rect = mediaModal.getBoundingClientRect();
        var x = e.clientX - rect.left;
        if (x < rect.width / 3) {
            changeMedia(-1);
        } else if (x > 2 * rect.width / 3) {
            changeMedia(1);
        }
    });
})();
