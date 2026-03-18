// 拖拽调整大小功能
let isResizing = false;
let currentResizer = null;
let currentElement = null;
let startX = 0;
let startY = 0;
let startWidth = 0;
let startHeight = 0;

// 初始化拖拽功能
document.addEventListener('DOMContentLoaded', () => {
    initResizable();
});

function initResizable() {
    const resizeHandles = document.querySelectorAll('.resize-handle');

    resizeHandles.forEach(handle => {
        handle.addEventListener('mousedown', startResize);
    });

    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
}

function startResize(e) {
    isResizing = true;
    currentResizer = e.target;
    currentElement = currentResizer.parentElement;

    const direction = currentResizer.dataset.direction;

    startX = e.clientX;
    startY = e.clientY;

    const rect = currentElement.getBoundingClientRect();
    startWidth = rect.width;
    startHeight = rect.height;

    currentElement.classList.add('resizing');
    document.body.style.cursor = direction === 'right' ? 'ew-resize' : 'ns-resize';

    e.preventDefault();
}

function resize(e) {
    if (!isResizing) return;

    const direction = currentResizer.dataset.direction;

    if (direction === 'right') {
        const deltaX = e.clientX - startX;
        const newWidth = startWidth + deltaX;

        // 限制最小和最大宽度
        if (newWidth >= 250 && newWidth <= window.innerWidth * 0.8) {
            currentElement.style.width = newWidth + 'px';
            currentElement.style.flexBasis = newWidth + 'px';
        }
    } else if (direction === 'bottom') {
        const deltaY = e.clientY - startY;
        const newHeight = startHeight + deltaY;

        // 限制最小和最大高度
        if (newHeight >= 200 && newHeight <= window.innerHeight * 0.8) {
            currentElement.style.height = newHeight + 'px';
            currentElement.style.flexBasis = newHeight + 'px';
        }
    }
}

function stopResize() {
    if (!isResizing) return;

    isResizing = false;
    document.body.style.cursor = '';

    if (currentElement) {
        currentElement.classList.remove('resizing');
    }

    currentResizer = null;
    currentElement = null;
}

// 折叠/展开功能
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const content = section.querySelector('.section-content');
    const btn = section.querySelector('.collapse-btn');

    if (section.classList.contains('collapsed')) {
        // 展开
        section.classList.remove('collapsed');
        content.style.display = 'flex';
        btn.textContent = '−';
        btn.title = '折叠';

        // 恢复之前的尺寸
        if (section.dataset.previousWidth) {
            section.style.width = section.dataset.previousWidth;
            section.style.flexBasis = section.dataset.previousWidth;
        }
        if (section.dataset.previousHeight) {
            section.style.height = section.dataset.previousHeight;
            section.style.flexBasis = section.dataset.previousHeight;
        }
    } else {
        // 折叠
        section.classList.add('collapsed');
        content.style.display = 'none';
        btn.textContent = '+';
        btn.title = '展开';

        // 保存当前尺寸
        const rect = section.getBoundingClientRect();
        section.dataset.previousWidth = rect.width + 'px';
        section.dataset.previousHeight = rect.height + 'px';

        // 设置折叠后的尺寸
        const header = section.querySelector('.section-header');
        const headerHeight = header.getBoundingClientRect().height;

        if (section.classList.contains('chat-section')) {
            section.style.width = '50px';
            section.style.flexBasis = '50px';
        } else if (section.classList.contains('graph-panel')) {
            section.style.height = headerHeight + 'px';
            section.style.flexBasis = headerHeight + 'px';
        } else {
            section.style.width = '50px';
            section.style.flexBasis = '50px';
        }
    }
}
