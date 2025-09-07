/**
 * Yeying面试官系统 - 主JavaScript文件
 */

$(document).ready(function() {
    // 初始化页面
    initializePage();
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