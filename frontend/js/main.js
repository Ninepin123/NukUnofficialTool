// main.js - 主要功能和導航控制

document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
});

function initializeNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.section');

    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetSection = this.getAttribute('data-section');
            
            // 移除所有按鈕的active狀態
            navButtons.forEach(btn => btn.classList.remove('active'));
            // 添加當前按鈕的active狀態
            this.classList.add('active');
            
            // 隱藏所有區段
            sections.forEach(section => section.classList.remove('active'));
            // 顯示目標區段
            const targetElement = document.getElementById(`${targetSection}-section`);
            if (targetElement) {
                targetElement.classList.add('active');
                
                // 如果切換到排課系統，初始化課程列表
                if (targetSection === 'course' && typeof initializeCourseSystem === 'function') {
                    initializeCourseSystem();
                }
            }
        });
    });
}

// 全域工具函數
function showMessage(element, message, type = 'info') {
    element.textContent = message;
    element.className = `status status-${type}`;
}

function clearMessage(element) {
    element.textContent = '';
    element.className = 'status';
}

// API 請求工具函數
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}