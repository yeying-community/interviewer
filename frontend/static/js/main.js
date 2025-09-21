/**
 * Yeying面试官系统 - 主JavaScript文件
 */

$(document).ready(function() {
    // 初始化页面
    initializePage();

    // 测试删除按钮是否存在
    console.log('页面加载完成，删除按钮数量:', $('.delete-room-btn').length + $('.delete-session-btn').length);

    // 测试jQuery是否工作
    console.log('jQuery版本:', $.fn.jquery);

    // 测试事件绑定
    $('#test-btn').on('click', function() {
        alert('jQuery工作正常！');
    });
});

// 初始化页面
function initializePage() {
    // 初始化提示工具
    initializeTooltips();
    
    // 绑定全局事件
    bindGlobalEvents();
    
    console.log('Yeying面试官系统已加载');
}

// 初始化Bootstrap提示工具
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 绑定全局事件
function bindGlobalEvents() {
    // 点击卡片跳转
    $(document).on('click', '.room-card, .session-card', function(e) {
        // 如果点击的是按钮，不执行跳转
        if ($(e.target).is('a, button') || $(e.target).parents('a, button').length) {
            return;
        }

        var href = $(this).data('href') || $(this).find('a').attr('href');
        if (href) {
            window.location.href = href;
        }
    });

    // 删除面试间按钮事件
    $(document).on('click', '.delete-room-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();

        console.log('删除面试间按钮被点击');

        const roomId = $(this).attr('data-room-id');
        const roomName = $(this).attr('data-room-name');

        console.log('房间ID:', roomId, '房间名称:', roomName);

        showDeleteConfirmModal('面试间', roomName, function() {
            deleteRoom(roomId);
        });
    });

    // 删除面试会话按钮事件
    $(document).on('click', '.delete-session-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();

        console.log('删除面试会话按钮被点击');

        const sessionId = $(this).attr('data-session-id');
        const sessionName = $(this).attr('data-session-name');

        console.log('会话ID:', sessionId, '会话名称:', sessionName);

        showDeleteConfirmModal('面试会话', sessionName, function() {
            deleteSession(sessionId);
        });
    });

    // ESC键关闭模态框
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            $('.modal').modal('hide');
        }
    });
}

// 工具函数：显示Toast通知
function showToast(type, message, duration = 3000) {
    const types = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const bgClass = types[type] || 'bg-info';
    
    const toastHtml = `
        <div class="toast position-fixed top-0 end-0 m-3" role="alert" style="z-index: 9999;">
            <div class="toast-header ${bgClass} text-white">
                <i class="fas fa-info-circle me-2"></i>
                <strong class="me-auto">系统通知</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    const toastElement = $(toastHtml).appendTo('body');
    const toast = new bootstrap.Toast(toastElement[0], {
        autohide: true,
        delay: duration
    });
    
    toast.show();
    
    // 自动清理DOM
    toastElement.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// 工具函数：格式化时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// 工具函数：防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 工具函数：节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// 工具函数：复制到剪贴板
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // 现代浏览器使用Clipboard API
        return navigator.clipboard.writeText(text).then(() => {
            showToast('success', '已复制到剪贴板');
        }).catch(() => {
            showToast('error', '复制失败');
        });
    } else {
        // 兼容旧浏览器
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            textArea.remove();
            showToast('success', '已复制到剪贴板');
        } catch (err) {
            textArea.remove();
            showToast('error', '复制失败');
        }
    }
}

// 工具函数：加载状态管理
function setLoading(element, isLoading) {
    const $element = $(element);
    
    if (isLoading) {
        const originalText = $element.text();
        $element.data('original-text', originalText);
        $element.html('<span class="spinner-border spinner-border-sm me-1"></span>加载中...');
        $element.prop('disabled', true);
    } else {
        const originalText = $element.data('original-text');
        $element.text(originalText);
        $element.prop('disabled', false);
    }
}

// API调用封装
class ApiClient {
    static async request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    static async get(url) {
        return this.request(url, { method: 'GET' });
    }
    
    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    static async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    static async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// 显示删除确认模态框
function showDeleteConfirmModal(type, name, onConfirm) {
    const modalHtml = `
        <div class="modal fade" id="deleteConfirmModal" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                            确认删除
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-1">你确定要删除这个${type}吗？</p>
                        <p class="text-muted mb-3"><strong>${name}</strong></p>
                        <div class="alert alert-warning mb-0">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>注意：</strong>删除操作不可恢复，相关的数据也会被一并删除。
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>
                            取消
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                            <i class="fas fa-trash me-1"></i>
                            确认删除
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 移除已存在的模态框
    $('#deleteConfirmModal').remove();

    // 添加新的模态框
    $('body').append(modalHtml);

    const modal = new bootstrap.Modal('#deleteConfirmModal');

    // 绑定确认删除事件
    $('#confirmDeleteBtn').on('click', function() {
        modal.hide();
        onConfirm();
    });

    // 显示模态框
    modal.show();

    // 自动清理DOM
    $('#deleteConfirmModal').on('hidden.bs.modal', function() {
        $(this).remove();
    });
}

// 删除面试间
async function deleteRoom(roomId) {
    try {
        showToast('info', '正在删除面试间...');

        const result = await ApiClient.delete(`/api/rooms/${roomId}`);

        if (result.success) {
            showToast('success', '面试间删除成功');

            // 如果在面试间详情页，跳转到首页
            if (window.location.pathname.includes('/room/')) {
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                // 如果在首页，刷新页面
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showToast('error', result.error || '删除面试间失败');
        }
    } catch (error) {
        console.error('删除面试间出错:', error);
        showToast('error', '删除面试间失败，请稍后重试');
    }
}

// 删除面试会话
async function deleteSession(sessionId) {
    try {
        showToast('info', '正在删除面试会话...');

        const result = await ApiClient.delete(`/api/sessions/${sessionId}`);

        if (result.success) {
            showToast('success', '面试会话删除成功');

            // 如果在会话详情页，跳转回面试间
            if (window.location.pathname.includes('/session/')) {
                // 需要从URL或其他方式获取room_id，这里先刷新页面
                setTimeout(() => {
                    window.history.back();
                }, 1000);
            } else {
                // 刷新当前页面
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showToast('error', result.error || '删除面试会话失败');
        }
    } catch (error) {
        console.error('删除面试会话出错:', error);
        showToast('error', '删除面试会话失败，请稍后重试');
    }
}

// 全局变量
window.YeyingInterviewer = {
    showToast,
    formatDateTime,
    debounce,
    throttle,
    copyToClipboard,
    setLoading,
    ApiClient
};

// 页面卸载时的清理工作
$(window).on('beforeunload', function() {
    // 清理定时器、事件监听器等
    console.log('页面即将卸载，执行清理工作');
});