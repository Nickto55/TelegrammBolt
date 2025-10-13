// TelegrammBolt - Main JavaScript

// Утилиты
const Utils = {
    // Показать спиннер загрузки
    showLoading: function() {
        const overlay = document.createElement('div');
        overlay.className = 'spinner-overlay';
        overlay.id = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner-border text-light" style="width: 3rem; height: 3rem;" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        `;
        document.body.appendChild(overlay);
    },
    
    // Скрыть спиннер загрузки
    hideLoading: function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    },
    
    // Показать уведомление
    showToast: function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        // Автоматически удалить через 5 секунд
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }, 5000);
    },
    
    // Форматирование даты
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Подтверждение действия
    confirmAction: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    }
};

// API клиент
const API = {
    // Базовый метод для запросов
    request: async function(url, options = {}) {
        try {
            Utils.showLoading();
            
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            Utils.hideLoading();
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка запроса');
            }
            
            return await response.json();
        } catch (error) {
            Utils.hideLoading();
            Utils.showToast(error.message, 'danger');
            throw error;
        }
    },
    
    // GET запрос
    get: function(url) {
        return this.request(url, { method: 'GET' });
    },
    
    // POST запрос
    post: function(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // PUT запрос
    put: function(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    // DELETE запрос
    delete: function(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

// DSE управление
const DSE = {
    // Загрузить все ДСЕ
    loadAll: async function() {
        try {
            const data = await API.get('/api/dse');
            return data;
        } catch (error) {
            console.error('Error loading DSE:', error);
            return [];
        }
    },
    
    // Загрузить конкретное ДСЕ
    loadById: async function(id) {
        try {
            const data = await API.get(`/api/dse/${id}`);
            return data;
        } catch (error) {
            console.error('Error loading DSE:', error);
            return null;
        }
    },
    
    // Создать новое ДСЕ
    create: async function(data) {
        try {
            const result = await API.post('/api/dse', data);
            Utils.showToast('ДСЕ успешно создано', 'success');
            return result;
        } catch (error) {
            console.error('Error creating DSE:', error);
            return null;
        }
    },
    
    // Обновить ДСЕ
    update: async function(id, data) {
        try {
            const result = await API.put(`/api/dse/${id}`, data);
            Utils.showToast('ДСЕ успешно обновлено', 'success');
            return result;
        } catch (error) {
            console.error('Error updating DSE:', error);
            return null;
        }
    },
    
    // Удалить ДСЕ
    delete: async function(id) {
        Utils.confirmAction('Вы уверены, что хотите удалить это ДСЕ?', async () => {
            try {
                await API.delete(`/api/dse/${id}`);
                Utils.showToast('ДСЕ успешно удалено', 'success');
                location.reload();
            } catch (error) {
                console.error('Error deleting DSE:', error);
            }
        });
    }
};

// Экспорт данных
const Export = {
    // Экспорт в Excel
    toExcel: function() {
        window.location.href = '/api/export/excel';
        Utils.showToast('Начинается загрузка Excel файла...', 'info');
    },
    
    // Генерация PDF
    toPdf: async function(data) {
        try {
            const response = await fetch('/api/export/pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `report_${new Date().getTime()}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                
                Utils.showToast('PDF отчет успешно создан', 'success');
            } else {
                throw new Error('Ошибка генерации PDF');
            }
        } catch (error) {
            Utils.showToast(error.message, 'danger');
        }
    }
};

// Чат
const Chat = {
    // Загрузить сообщения
    loadMessages: async function() {
        try {
            const messages = await API.get('/api/chat/messages');
            return messages;
        } catch (error) {
            console.error('Error loading messages:', error);
            return [];
        }
    },
    
    // Отправить сообщение
    sendMessage: async function(message, targetUserId = null) {
        try {
            const data = {
                message: message,
                target_user_id: targetUserId
            };
            
            const result = await API.post('/api/chat/send', data);
            return result;
        } catch (error) {
            console.error('Error sending message:', error);
            return null;
        }
    },
    
    // Отобразить сообщения
    displayMessages: function(messages, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${msg.isSent ? 'sent' : 'received'}`;
            messageDiv.innerHTML = `
                <div class="message-text">${msg.text}</div>
                <div class="time">${Utils.formatDate(msg.timestamp)}</div>
            `;
            container.appendChild(messageDiv);
        });
        
        // Прокрутить вниз
        container.scrollTop = container.scrollHeight;
    }
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавить класс fade-in ко всем карточкам
    document.querySelectorAll('.card').forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Автоматически скрывать alerts через 5 секунд
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Подтверждение перед отправкой форм удаления
    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});

// Экспортировать в глобальную область видимости
window.Utils = Utils;
window.API = API;
window.DSE = DSE;
window.Export = Export;
window.Chat = Chat;
