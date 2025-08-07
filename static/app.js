// 全局变量
let currentPage = 1;
let currentFileType = '';
let currentView = 'grid'; // 默认网格视图
let currentSearchTerm = '';
let currentSortBy = 'upload_time';
let currentSortOrder = 'desc';
let searchTimeout = null;

// 辅助函数：格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 显示粘贴通知 - 使用toast通知系统
function showPasteNotification(fileCount) {
    const message = `粘贴成功！已从剪贴板粘贴 ${fileCount} 个文件`;
    showToast(message, 'success', 3000);
}

// 加载存储配置信息
function loadStorageConfig() {
    fetch('/api/storage-config')
        .then(response => response.json())
        .then(config => {
            const storageTypeElement = document.getElementById('currentStorageType');
            if (storageTypeElement) {
                storageTypeElement.innerHTML = `
                    <i class="${config.storage_icon}"></i> ${config.storage_name}
                `;
            }
        })
        .catch(error => {
            console.error('加载存储配置失败:', error);
            // 使用默认显示
            const storageTypeElement = document.getElementById('currentStorageType');
            if (storageTypeElement) {
                storageTypeElement.innerHTML = `
                    <i class="bi bi-hdd"></i> 本地存储
                `;
            }
        });
}

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeMobileNavigation();
});

// 移动端导航功能
function initializeMobileNavigation() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (!sidebarToggle || !sidebar || !sidebarOverlay) return;
    
    // 切换侧边栏显示
    function toggleSidebar() {
        sidebar.classList.toggle('show');
        sidebarOverlay.classList.toggle('show');
        document.body.style.overflow = sidebar.classList.contains('show') ? 'hidden' : '';
    }
    
    // 隐藏侧边栏
    function hideSidebar() {
        sidebar.classList.remove('show');
        sidebarOverlay.classList.remove('show');
        document.body.style.overflow = '';
    }
    
    // 绑定事件
    sidebarToggle.addEventListener('click', toggleSidebar);
    sidebarOverlay.addEventListener('click', hideSidebar);
    
    // 点击侧边栏内的导航链接时自动隐藏侧边栏（移动端）
    const navLinks = sidebar.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) {
                setTimeout(hideSidebar, 100); // 稍微延迟以确保页面切换完成
            }
        });
    });
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            hideSidebar(); // 在大屏幕上自动隐藏移动端侧边栏
        }
    });
}

function initializeApp() {
    initializeNavigation();
    initializeFileUpload();
    initializeNotes();
    initializeChat(); // 初始化聊天记录模块
    initializeFileManagement(); // 初始化文件管理
    loadFiles();
    loadNotes();
    loadStorageConfig(); // 加载存储配置
}

function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link[data-section]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            showSection(this.dataset.section);
        });
    });
}

function showSection(section) {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(s => s.style.display = 'none');
    document.getElementById(`${section}-section`).style.display = 'block';
    
    // 当切换到聊天模块时，加载聊天记录
    if (section === 'chat') {
        loadChatMessages();
        // 聚焦到输入框
        setTimeout(() => {
            const chatInput = document.getElementById('chatMessageContent');
            if (chatInput) {
                chatInput.focus();
            }
        }, 100);
    }
}

function initializeFileManagement() {
    // 视图切换
    document.getElementById('gridView').addEventListener('click', function() {
        currentView = 'grid';
        document.getElementById('gridView').classList.add('active');
        document.getElementById('listView').classList.remove('active');
        displayFiles(window.currentFiles || []);
    });
    
    document.getElementById('listView').addEventListener('click', function() {
        currentView = 'list';
        document.getElementById('listView').classList.add('active');
        document.getElementById('gridView').classList.remove('active');
        displayFiles(window.currentFiles || []);
    });
    
    // 搜索功能
    document.getElementById('fileSearch').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearchTerm = this.value.trim();
            currentPage = 1;
            loadFiles();
        }, 300); // 防抖动
    });
    
    document.getElementById('clearSearch').addEventListener('click', function() {
        document.getElementById('fileSearch').value = '';
        currentSearchTerm = '';
        currentPage = 1;
        loadFiles();
    });
    
    // 筛选功能
    document.getElementById('fileTypeFilter').addEventListener('change', function() {
        currentFileType = this.value;
        currentPage = 1;
        loadFiles();
    });
    
    // 排序功能
    document.getElementById('fileSortBy').addEventListener('change', function() {
        currentSortBy = this.value;
        currentPage = 1;
        loadFiles();
    });
    
    document.getElementById('fileSortOrder').addEventListener('change', function() {
        currentSortOrder = this.value;
        currentPage = 1;
        loadFiles();
    });
}

function initializeFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
        handleFileUpload(e.dataTransfer.files);
    });
    
    // 文件选择上传
    fileInput.addEventListener('change', function() {
        handleFileUpload(this.files);
    });
    
    // 粘贴上传功能
    document.addEventListener('paste', function(e) {
        console.log('粘贴事件被触发'); // 调试信息
        
        // 检查是否在上传区域或者文件管理页面
        const activeSection = document.querySelector('.content-section[style*="block"]');
        console.log('当前活跃页面:', activeSection ? activeSection.id : 'none'); // 调试信息
        
        // 允许在文件管理页面和上传页面使用粘贴功能
        if (!activeSection || (activeSection.id !== 'files-section' && activeSection.id !== 'upload-section')) {
            console.log('不在允许的页面，退出'); // 调试信息
            return;
        }
        
        const clipboardItems = e.clipboardData.items;
        console.log('剪贴板项目数量:', clipboardItems.length); // 调试信息
        const files = [];
        
        for (let i = 0; i < clipboardItems.length; i++) {
            const item = clipboardItems[i];
            console.log(`项目 ${i}:`, item.kind, item.type); // 调试信息
            
            // 检查是否为文件类型
            if (item.kind === 'file') {
                const file = item.getAsFile();
                if (file) {
                    console.log('找到文件:', file.name, file.size); // 调试信息
                    files.push(file);
                }
            }
        }
        
        console.log('总共找到文件数量:', files.length); // 调试信息
        
        if (files.length > 0) {
            e.preventDefault();
            console.log('开始上传文件'); // 调试信息
            handleFileUpload(files);
            
            // 显示粘贴提示
            showPasteNotification(files.length);
        } else {
            console.log('剪贴板中没有文件'); // 调试信息
        }
    });
    
    // 清空上传历史按钮事件
    const clearHistoryBtn = document.getElementById('clearUploadHistory');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            const uploadList = document.getElementById('uploadList');
            const uploadProgress = document.getElementById('uploadProgress');
            
            // 确认对话框
            if (confirm('确定要清空所有上传历史记录吗？')) {
                uploadList.innerHTML = '';
                uploadProgress.style.display = 'none';
                
                // 显示清空成功提示
                const notification = document.createElement('div');
                notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
                notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
                notification.innerHTML = `
                    <i class="bi bi-check-circle"></i>
                    <strong>清空成功！</strong> 上传历史记录已清空
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                
                document.body.appendChild(notification);
                
                // 3秒后自动消失
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 3000);
            }
        });
    }
}

function handleFileUpload(files) {
    if (files.length === 0) return;
    
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadList = document.getElementById('uploadList');
    uploadProgress.style.display = 'block';
    
    // 不清空之前的上传列表，让新上传在下面新增
    // uploadList.innerHTML = ''; // 已移除
    
    Array.from(files).forEach((file, index) => {
        uploadFile(file, index);
    });
}

function uploadFile(file, index) {
    const uploadList = document.getElementById('uploadList');
    
    // 创建上传项目的HTML
    const uploadItem = document.createElement('div');
    uploadItem.className = 'upload-item mb-3 p-3 border rounded';
    uploadItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
                <strong>${file.name}</strong>
                <small class="text-muted d-block">${formatFileSize(file.size)}</small>
            </div>
            <span class="upload-status badge bg-info">准备上传...</span>
        </div>
        <div class="progress mb-2">
            <div class="progress-bar" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
        </div>
        <div class="upload-details text-muted small"></div>
    `;
    
    uploadList.appendChild(uploadItem);
    
    const progressBar = uploadItem.querySelector('.progress-bar');
    const statusBadge = uploadItem.querySelector('.upload-status');
    const detailsDiv = uploadItem.querySelector('.upload-details');
    
    const formData = new FormData();
    formData.append('file', file);
    // 使用默认存储方式（由后端决定）
    // formData.append('storage_type', 'local'); // 已移除，由后端配置决定
    // formData.append('description', ''); // 已移除文件描述功能
    
    // 使用XMLHttpRequest来支持上传进度
    const xhr = new XMLHttpRequest();
    
    // 上传进度事件
    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            progressBar.style.width = percentComplete + '%';
            progressBar.textContent = percentComplete + '%';
            progressBar.setAttribute('aria-valuenow', percentComplete);
            
            statusBadge.textContent = '上传中...';
            statusBadge.className = 'upload-status badge bg-primary';
            
            const uploadedMB = (e.loaded / 1024 / 1024).toFixed(2);
            const totalMB = (e.total / 1024 / 1024).toFixed(2);
            detailsDiv.textContent = `已上传 ${uploadedMB}MB / ${totalMB}MB`;
        }
    });
    
    // 上传完成事件
    xhr.addEventListener('load', function() {
        if (xhr.status === 200) {
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.message) {
                    statusBadge.textContent = '上传成功';
                    statusBadge.className = 'upload-status badge bg-success';
                    detailsDiv.textContent = '文件已成功上传到服务器';
                    
                    // 延迟刷新文件列表，让用户看到成功状态
                    setTimeout(() => {
                        loadFiles();
                    }, 1000);
                } else {
                    throw new Error(response.error || '上传失败');
                }
            } catch (error) {
                statusBadge.textContent = '上传失败';
                statusBadge.className = 'upload-status badge bg-danger';
                detailsDiv.textContent = '服务器响应错误: ' + error.message;
            }
        } else {
            statusBadge.textContent = '上传失败';
            statusBadge.className = 'upload-status badge bg-danger';
            detailsDiv.textContent = `HTTP错误: ${xhr.status} ${xhr.statusText}`;
        }
    });
    
    // 上传错误事件
    xhr.addEventListener('error', function() {
        statusBadge.textContent = '上传失败';
        statusBadge.className = 'upload-status badge bg-danger';
        detailsDiv.textContent = '网络错误，请检查网络连接';
    });
    
    // 开始上传
    statusBadge.textContent = '开始上传...';
    statusBadge.className = 'upload-status badge bg-info';
    xhr.open('POST', '/api/upload');
    xhr.send(formData);
}

function loadFiles(page = 1) {
    let url = `/api/files?page=${page}`;
    if (currentFileType) url += `&type=${currentFileType}`;
    if (currentSearchTerm) url += `&search=${encodeURIComponent(currentSearchTerm)}`;
    if (currentSortBy) url += `&sort_by=${currentSortBy}`;
    if (currentSortOrder) url += `&sort_order=${currentSortOrder}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            window.currentFiles = data.files; // 保存当前文件列表
            displayFiles(data.files);
            updateFileStats(data);
        })
        .catch(error => {
            console.error('加载文件失败:', error);
            document.getElementById('filesContainer').innerHTML = 
                '<div class="text-center text-muted py-5">加载失败，请刷新页面</div>';
        });
}

function displayFiles(files) {
    const container = document.getElementById('filesContainer');
    
    // 设置全局文件列表，供预览功能使用
    window.currentFiles = files;
    
    if (files.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-5">暂无文件</div>';
        return;
    }
    
    if (currentView === 'grid') {
        displayFilesGrid(files, container);
    } else {
        displayFilesList(files, container);
    }
}

function displayFilesGrid(files, container) {
    let html = '<div class="file-grid">';
    
    files.forEach(file => {
        const thumbnailHtml = getThumbnailHtml(file);
        const fileIcon = getFileIcon(file.file_type);
        const formattedDate = new Date(file.upload_time).toLocaleDateString('zh-CN');
        
        html += `
            <div class="file-card" data-file-id="${file.id}">
                <div class="file-thumbnail" onclick="previewFile(${file.id})">
                    ${thumbnailHtml}
                </div>
                <div class="file-name" title="${file.original_filename}">
                    ${file.original_filename.length > 20 ? 
                        file.original_filename.substring(0, 20) + '...' : 
                        file.original_filename}
                </div>
                <div class="file-meta">
                    <div>${formatFileSize(file.file_size)}</div>
                    <div>${formattedDate}</div>
                </div>
                <div class="file-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="downloadFile(${file.id})">
                        <i class="bi bi-download"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="shareFile(${file.id})">
                        <i class="bi bi-share"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteFile(${file.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function displayFilesList(files, container) {
    let html = '<div class="file-list">';
    
    files.forEach(file => {
        const thumbnailHtml = getThumbnailHtml(file);
        const formattedDate = new Date(file.upload_time).toLocaleDateString('zh-CN');
        const formattedTime = new Date(file.upload_time).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
        
        html += `
            <div class="file-list-item" data-file-id="${file.id}">
                <div class="file-list-thumbnail" onclick="previewFile(${file.id})">
                    ${thumbnailHtml}
                </div>
                <div class="file-list-info">
                    <div class="file-list-name" title="${file.original_filename}">
                        ${file.original_filename}
                    </div>
                    <div class="file-list-meta">
                        <span class="badge bg-secondary me-2">${file.file_type}</span>
                        ${formatFileSize(file.file_size)} • ${formattedDate} ${formattedTime}
                    </div>
                </div>
                <div class="file-list-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="downloadFile(${file.id})">
                        <i class="bi bi-download"></i> 下载
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="shareFile(${file.id})">
                        <i class="bi bi-share"></i> 分享
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteFile(${file.id})">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// 获取缩略图 HTML
function getThumbnailHtml(file) {
    if ((file.file_type === 'image' || file.file_type === 'video') && file.thumbnail_path) {
        const iconClass = getFileIcon(file.file_type);
        const videoOverlay = file.file_type === 'video' ? '<div class="video-overlay"><i class="bi bi-play-circle-fill"></i></div>' : '';
        return `<div class="thumbnail-container">
                    <img src="/api/thumbnail/${file.id}" alt="${file.original_filename}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';"
                         class="thumbnail-image">
                    <i class="file-icon bi ${iconClass}" style="display:none;"></i>
                    ${videoOverlay}
                </div>`;
    } else {
        return `<i class="file-icon bi ${getFileIcon(file.file_type)}"></i>`;
    }
}

// 获取文件类型图标
function getFileIcon(fileType) {
    const icons = {
        'image': 'bi-image',
        'video': 'bi-play-circle',
        'audio': 'bi-file-earmark-music',
        'document': 'bi-file-earmark-text',
        'archive': 'bi-file-earmark-zip',
        'code': 'bi-file-earmark-code',
        'pdf': 'bi-file-earmark-pdf',
        'word': 'bi-file-earmark-word',
        'excel': 'bi-file-earmark-excel',
        'powerpoint': 'bi-file-earmark-ppt'
    };
    return icons[fileType] || 'bi-file-earmark';
}

// 更新文件统计信息
function updateFileStats(data) {
    const fileStatsElement = document.getElementById('fileStats');
    const fileCountElement = document.getElementById('fileCount');
    
    if (data.files && data.files.length > 0) {
        const totalSize = data.files.reduce((sum, file) => sum + file.file_size, 0);
        const imageCount = data.files.filter(f => f.file_type === 'image').length;
        const videoCount = data.files.filter(f => f.file_type === 'video').length;
        const docCount = data.files.filter(f => f.file_type === 'document').length;
        
        let statsText = `总大小: ${formatFileSize(totalSize)}`;
        if (imageCount > 0) statsText += ` • 图片: ${imageCount}`;
        if (videoCount > 0) statsText += ` • 视频: ${videoCount}`;
        if (docCount > 0) statsText += ` • 文档: ${docCount}`;
        
        fileStatsElement.textContent = statsText;
        fileCountElement.textContent = `${data.files.length} 个文件`;
    } else {
        fileStatsElement.textContent = '暂无文件';
        fileCountElement.textContent = '0 个文件';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function previewFile(fileId) {
    // 从当前文件列表中找到文件信息
    const file = window.currentFiles?.find(f => f.id === fileId);
    if (!file) {
        console.error('找不到文件信息:', fileId);
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    const content = document.getElementById('previewContent');
    const title = document.querySelector('#previewModal .modal-title');
    
    // 设置模态框标题
    title.textContent = file.original_filename;
    
    if (file.file_type === 'image') {
        content.innerHTML = `<img src="/api/files/${fileId}" class="img-fluid" alt="${file.original_filename}">`;
    } else if (file.file_type === 'video') {
        content.innerHTML = `<video controls class="w-100"><source src="/api/files/${fileId}"></video>`;
    } else {
        content.innerHTML = '<div class="text-center">此文件类型不支持预览</div>';
    }
    
    modal.show();
}

// 下载文件
function downloadFile(fileId) {
    const file = window.currentFiles?.find(f => f.id === fileId);
    if (!file) {
        console.error('找不到文件信息:', fileId);
        return;
    }
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = `/api/files/${fileId}`;
    link.download = file.original_filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function deleteFile(fileId) {
    if (!confirm('确定要删除这个文件吗？')) return;
    
    fetch(`/api/files/${fileId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            showToast(data.message, 'success');
            loadFiles();
        });
}

// 分享功能
function shareFile(fileId) {
    document.getElementById('shareFileId').value = fileId;
    document.getElementById('shareResult').style.display = 'none';
    document.getElementById('shareForm').style.display = 'block';
    document.getElementById('createShareBtn').style.display = 'inline-block';
    new bootstrap.Modal(document.getElementById('shareModal')).show();
}

function createShareLink() {
    const fileId = document.getElementById('shareFileId').value;
    const expiresHours = parseInt(document.getElementById('expiresHours').value);
    const maxAccess = parseInt(document.getElementById('maxAccess').value);
    
    fetch(`/api/files/${fileId}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            expires_hours: expiresHours,
            max_access: maxAccess
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.share_url) {
            // 获取文件信息
            const file = window.currentFiles?.find(f => f.id === parseInt(fileId));
            const filename = file ? file.original_filename : '文件';
            const shareUrl = data.share_url;
            
            // 设置各种格式的链接
            document.getElementById('shareUrl').value = shareUrl;
            document.getElementById('shareMarkdown').value = `![${filename}](${shareUrl})`;
            document.getElementById('shareHtml').value = `<img src="${shareUrl}" alt="${filename}" />`;
            
            // 显示结果区域，隐藏表单
            document.getElementById('shareResult').style.display = 'block';
            document.getElementById('shareForm').style.display = 'none';
            document.getElementById('createShareBtn').style.display = 'none';
        } else {
            showToast(data.error || '创建分享链接失败', 'error');
        }
    })
    .catch(error => {
        console.error('创建分享链接失败:', error);
        showToast('创建分享链接失败', 'error');
    });
}

// 复制到剪贴板的通用函数
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error('找不到元素:', elementId);
        return;
    }
    
    element.select();
    element.setSelectionRange(0, 99999);
    
    try {
        document.execCommand('copy');
        showToast('已复制到剪贴板', 'success');
    } catch (err) {
        console.error('复制失败:', err);
        showToast('复制失败', 'error');
    }
}



// 兼容性函数（保持旧的函数名）
function copyShareUrl() {
    copyToClipboard('shareUrl');
}

// 旧的错误处理代码（保持兼容性）
function handleCopyError(err) {
    console.error('复制失败:', err);
    showToast('复制失败，请手动复制', 'warning');
}

// 笔记功能
function initializeNotes() {
    document.getElementById('saveNote').addEventListener('click', saveNote);
    document.getElementById('createShareBtn').addEventListener('click', createShareLink);
}

function loadNotes(page = 1) {
    fetch(`/api/notes?page=${page}`)
        .then(response => response.json())
        .then(data => {
            displayNotes(data.notes);
        });
}

function displayNotes(notes) {
    const container = document.getElementById('notesContainer');
    
    if (notes.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-5">暂无笔记</div>';
        return;
    }
    
    let html = '<div class="row">';
    notes.forEach(note => {
        html += `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${note.title}</h5>
                        <p class="card-text">${note.content.substring(0, 100)}...</p>
                        <button class="btn btn-sm btn-outline-primary" onclick="editNote(${note.id})">编辑</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteNote(${note.id})">删除</button>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

function editNote(noteId) {
    if (noteId) {
        fetch(`/api/notes/${noteId}`)
            .then(response => response.json())
            .then(note => {
                document.getElementById('noteId').value = note.id;
                document.getElementById('noteTitle').value = note.title;
                document.getElementById('noteContent').value = note.content;
                document.getElementById('noteTags').value = note.tags.join(',');
                new bootstrap.Modal(document.getElementById('noteModal')).show();
            });
    } else {
        document.getElementById('noteForm').reset();
        document.getElementById('noteId').value = '';
        new bootstrap.Modal(document.getElementById('noteModal')).show();
    }
}

function saveNote() {
    const noteId = document.getElementById('noteId').value;
    const data = {
        title: document.getElementById('noteTitle').value,
        content: document.getElementById('noteContent').value,
        tags: document.getElementById('noteTags').value.split(',').map(t => t.trim()).filter(t => t)
    };
    
    const url = noteId ? `/api/notes/${noteId}` : '/api/notes';
    const method = noteId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        showToast(result.message, 'success');
        bootstrap.Modal.getInstance(document.getElementById('noteModal')).hide();
        loadNotes();
    });
}

function deleteNote(noteId) {
    if (!confirm('确定要删除这个笔记吗？')) return;
    
    fetch(`/api/notes/${noteId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            showToast(data.message, 'success');
            loadNotes();
        });
}

function showAlert(message, type) {
    // 简单的提示实现
    alert(message);
}

// 新的toast通知系统
function showToast(message, type = 'success', duration = 3000) {
    // 创建通知元素
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
        opacity: 0;
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    // 根据类型设置颜色
    if (type === 'success') {
        toast.style.backgroundColor = '#28a745';
    } else if (type === 'danger' || type === 'error') {
        toast.style.backgroundColor = '#dc3545';
    } else if (type === 'warning') {
        toast.style.backgroundColor = '#ffc107';
        toast.style.color = '#212529';
    } else {
        toast.style.backgroundColor = '#17a2b8';
    }
    
    // 添加图标和文本
    const icon = type === 'success' ? '✓' : (type === 'error' || type === 'danger') ? '✗' : 'i';
    toast.innerHTML = `<span style="margin-right: 8px;">${icon}</span>${message}`;
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 显示动画
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    }, 10);
    
    // 自动隐藏
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        
        // 移除元素
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// 聊天记录模块功能
let currentChatPage = 1;
let chatMessages = [];

function initializeChat() {
    // 初始化聊天模块事件监听器
    const chatMessageContent = document.getElementById('chatMessageContent');
    const chatInputWrapper = document.getElementById('chatInputWrapper');
    const sendButton = document.getElementById('sendChatMessage');
    const uploadFileBtn = document.getElementById('uploadFileBtn');
    const uploadImageBtn = document.getElementById('uploadImageBtn');
    const chatFileUpload = document.getElementById('chatFileUpload');
    const chatImageUpload = document.getElementById('chatImageUpload');
    const chatContainer = document.querySelector('.chat-container');
    const dragOverlay = document.getElementById('dragOverlay');
    
    // 发送消息
    sendButton.addEventListener('click', sendTextMessage);
    
    // 文字输入框事件
    chatMessageContent.addEventListener('focus', () => {
        chatInputWrapper.classList.add('focus');
    });
    
    chatMessageContent.addEventListener('blur', () => {
        chatInputWrapper.classList.remove('focus');
    });
    
    // 自动调整输入框高度
    chatMessageContent.addEventListener('input', () => {
        chatMessageContent.style.height = 'auto';
        chatMessageContent.style.height = Math.min(chatMessageContent.scrollHeight, 120) + 'px';
        
        // 更新发送按钮状态
        const hasContent = chatMessageContent.value.trim().length > 0;
        sendButton.disabled = !hasContent;
    });
    
    // 回车发送（Shift+Enter换行）
    chatMessageContent.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendTextMessage();
        }
    });
    
    // 上传按钮事件
    uploadFileBtn.addEventListener('click', () => {
        chatFileUpload.click();
    });
    
    uploadImageBtn.addEventListener('click', () => {
        chatImageUpload.click();
    });
    
    // 文件上传事件
    chatFileUpload.addEventListener('change', (e) => {
        handleChatFiles(e.target.files);
        e.target.value = ''; // 清空选择
    });
    
    chatImageUpload.addEventListener('change', (e) => {
        handleChatFiles(e.target.files);
        e.target.value = ''; // 清空选择
    });
    
    // 全局拖拽事件
    let dragCounter = 0;
    
    document.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dragCounter++;
        if (document.getElementById('chat-section').style.display !== 'none') {
            dragOverlay.classList.add('active');
        }
    });
    
    document.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            dragOverlay.classList.remove('active');
        }
    });
    
    document.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    document.addEventListener('drop', (e) => {
        e.preventDefault();
        dragCounter = 0;
        dragOverlay.classList.remove('active');
        
        if (document.getElementById('chat-section').style.display !== 'none' && e.dataTransfer.files.length > 0) {
            handleChatFiles(e.dataTransfer.files);
        }
    });
    
    // 粘贴事件
    document.addEventListener('paste', (e) => {
        if (document.getElementById('chat-section').style.display !== 'none') {
            const items = e.clipboardData.items;
            const files = [];
            
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                if (item.kind === 'file') {
                    const file = item.getAsFile();
                    if (file) {
                        files.push(file);
                    }
                }
            }
            
            if (files.length > 0) {
                e.preventDefault();
                handleChatFiles(files);
            }
        }
    });
    
    // 初始化发送按钮状态
    sendButton.disabled = true;
}



// 滚动聊天记录到底部
function scrollChatToBottom() {
    const chatMessagesContainer = document.getElementById('chatMessagesContainer');
    if (chatMessagesContainer) {
        setTimeout(() => {
            chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        }, 100);
    }
}

function sendTextMessage() {
    const chatMessageContent = document.getElementById('chatMessageContent');
    const sendButton = document.getElementById('sendChatMessage');
    const content = chatMessageContent.value.trim();
    
    if (!content) return;
    
    // 禁用发送按钮
    sendButton.disabled = true;
    sendButton.innerHTML = '<i class="bi bi-hourglass-split"></i> 发送中...';
    
    fetch('/api/chat/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.chat_message) {
            chatMessageContent.value = '';
            chatMessageContent.style.height = 'auto';
            loadChatMessages(); // 重新加载消息列表
            scrollChatToBottom(); // 滚动到底部
        } else {
            showToast(data.error || '发送失败', 'error');
        }
    })
    .catch(error => {
        console.error('发送消息失败:', error);
        showToast('发送失败', 'error');
    })
    .finally(() => {
        // 恢复发送按钮
        sendButton.innerHTML = '<i class="bi bi-send"></i> 发送';
        sendButton.disabled = true; // 保持禁用状态，直到有新内容
    });
}

function handleChatFileUpload(event) {
    const files = event.target.files;
    handleChatFiles(files);
}

function handleChatFiles(files) {
    if (!files || files.length === 0) return;
    
    const fileArray = Array.from(files);
    let uploadedCount = 0;
    let totalFiles = fileArray.length;
    let hasErrors = false;
    
    fileArray.forEach((file, index) => {
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/api/chat/messages', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            uploadedCount++;
            
            if (data.chat_message) {
                // 成功上传，静默处理，所有文件完成后刷新界面
                if (uploadedCount === totalFiles) {
                    loadChatMessages();
                    scrollChatToBottom();
                }
            } else {
                hasErrors = true;
                showToast(`${file.name}: ${data.error || '上传失败'}`, 'error');
            }
        })
        .catch(error => {
            uploadedCount++;
            hasErrors = true;
            console.error('文件上传失败:', error);
            showToast(`${file.name} 上传失败`, 'error');
        });
    });
}

function loadChatMessages(page = 1) {
    fetch(`/api/chat/messages?page=${page}`)
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                displayChatMessages(data.messages);
                // 如果是第一页，滚动到底部
                if (page === 1) {
                    scrollChatToBottom();
                }
            }
        })
        .catch(error => {
            console.error('加载聊天记录失败:', error);
        });
}

function displayChatMessages(messages) {
    const container = document.getElementById('chatMessages');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-chat-dots" style="font-size: 3rem; opacity: 0.3;"></i>
                <p class="mt-3">还没有记录，开始你的第一条随心记录吧！</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    // 按时间倒序显示（最新的在下面）
    messages.reverse().forEach(message => {
        html += generateChatMessageHtml(message);
    });
    
    container.innerHTML = html;
    
    // 滚动到底部
    container.scrollTop = container.scrollHeight;
}

function generateChatMessageHtml(message) {
    const time = new Date(message.created_time).toLocaleString('zh-CN');
    
    if (message.message_type === 'text') {
        return `
            <div class="chat-message text" data-message-id="${message.id}">
                <div class="message-bubble text">
                    ${escapeHtml(message.content)}
                    <div class="message-actions">
                        <button class="delete-message" onclick="deleteChatMessage(${message.id})">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;
    } else if (message.message_type === 'image' && message.thumbnail_path) {
        return `
            <div class="chat-message file" data-message-id="${message.id}">
                <div class="image-message" onclick="previewChatFile(${message.id}, '${message.file_name}', 'image')">
                    <img src="/api/chat/thumbnails/${message.id}" alt="${message.file_name}">
                    <div class="message-actions">
                        <button class="delete-message" onclick="deleteChatMessage(${message.id})">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;
    } else if (message.message_type === 'video' && message.thumbnail_path) {
        return `
            <div class="chat-message file" data-message-id="${message.id}">
                <div class="video-message" onclick="previewChatFile(${message.id}, '${message.file_name}', 'video')">
                    <img src="/api/chat/thumbnails/${message.id}" alt="${message.file_name}">
                    <div class="message-actions">
                        <button class="delete-message" onclick="deleteChatMessage(${message.id})">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;
    } else {
        // 其他文件类型
        const icon = getFileIcon(message.message_type);
        return `
            <div class="chat-message file" data-message-id="${message.id}">
                <div class="file-message" onclick="downloadChatFile(${message.id})">
                    <i class="file-message-icon bi ${icon}"></i>
                    <div class="file-message-info">
                        <div class="file-message-name">${message.file_name}</div>
                        <div class="file-message-size">${formatFileSize(message.file_size)}</div>
                    </div>
                    <div class="message-actions">
                        <button class="delete-message" onclick="deleteChatMessage(${message.id})">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="message-time">${time}</div>
            </div>
        `;
    }
}

function previewChatFile(messageId, filename, type) {
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    const content = document.getElementById('previewContent');
    const title = document.querySelector('#previewModal .modal-title');
    
    title.textContent = filename;
    
    if (type === 'image') {
        content.innerHTML = `<img src="/api/chat/files/${messageId}" class="img-fluid" alt="${filename}">`;
    } else if (type === 'video') {
        content.innerHTML = `<video controls class="w-100"><source src="/api/chat/files/${messageId}"></video>`;
    } else {
        content.innerHTML = '<div class="text-center">此文件类型不支持预览</div>';
    }
    
    modal.show();
}

function downloadChatFile(messageId) {
    window.open(`/api/chat/files/${messageId}`, '_blank');
}

function deleteChatMessage(messageId) {
    if (!confirm('确定要删除这条记录吗？')) return;
    
    fetch(`/api/chat/messages/${messageId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            showToast(data.message, 'success');
            loadChatMessages(); // 重新加载消息列表
        })
        .catch(error => {
            console.error('删除消息失败:', error);
            showToast('删除失败', 'error');
        });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}
