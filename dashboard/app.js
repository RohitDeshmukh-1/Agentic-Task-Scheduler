/* ═══════════════════════════════════════════════════════════════
   TaskPilot — Dashboard Application Logic
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = window.location.origin + '/api/v1';
let currentUser = null;
let activityLog = [];

// ─── View Navigation ────────────────────────────────────────────
function showView(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    const view = document.getElementById(`view-${viewName}`);
    const link = document.querySelector(`[data-view="${viewName}"]`);
    
    if (view) view.classList.add('active');
    if (link) link.classList.add('active');
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => showView(link.dataset.view));
});

// ─── API Helpers ────────────────────────────────────────────────
async function api(endpoint, options = {}) {
    try {
        const resp = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });
        if (!resp.ok) throw new Error(`API Error: ${resp.status}`);
        if (resp.status === 204) return null;
        return await resp.json();
    } catch (err) {
        console.error('API Error:', err);
        return null;
    }
}

// ─── Chat System ────────────────────────────────────────────────
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');

function addMessage(text, isUser = false) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'message-user' : 'message-bot'}`;
    
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Convert WhatsApp-style formatting to HTML
    let html = text
        .replace(/\*([^*]+)\*/g, '<strong>$1</strong>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
    
    div.innerHTML = `
        <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
        <div>
            <div class="message-bubble">${html}</div>
            <div class="message-time">${now}</div>
        </div>
    `;
    
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return div;
}

function addTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message message-bot';
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

async function sendMessage(text) {
    if (!text || !text.trim()) return;
    
    const message = text.trim();
    chatInput.value = '';
    
    // Add user message
    addMessage(message, true);
    
    // Add to activity log
    addActivity('💬', `You said: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}"`);
    
    // Show typing
    addTypingIndicator();
    chatSend.disabled = true;
    
    try {
        const result = await api('/webhook/console', {
            method: 'POST',
            body: JSON.stringify({ phone: '+919999999999', message }),
        });
        
        removeTypingIndicator();
        
        if (result && result.response) {
            addMessage(result.response);
            addActivity('🤖', `TaskPilot responded`);
            
            // Refresh dashboard data after processing
            setTimeout(() => refreshDashboard(), 500);
        } else {
            addMessage("Sorry, I couldn't process that. Please try again.");
        }
    } catch (err) {
        removeTypingIndicator();
        addMessage("Connection error. Make sure the server is running.");
    }
    
    chatSend.disabled = false;
    chatInput.focus();
}

chatSend.addEventListener('click', () => sendMessage(chatInput.value));
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(chatInput.value);
    }
});

// ─── Activity Feed ──────────────────────────────────────────────
function addActivity(icon, text) {
    const feed = document.getElementById('activity-feed');
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Remove empty state
    const empty = feed.querySelector('.activity-empty');
    if (empty) empty.remove();
    
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.innerHTML = `
        <div class="activity-icon">${icon}</div>
        <div>
            <div class="activity-text">${text}</div>
            <div class="activity-time">${now}</div>
        </div>
    `;
    
    feed.insertBefore(item, feed.firstChild);
    
    // Keep only last 20 items
    while (feed.children.length > 20) {
        feed.removeChild(feed.lastChild);
    }
}

// ─── Dashboard Data ─────────────────────────────────────────────
async function refreshDashboard() {
    // Get users
    const users = await api('/users/');
    if (!users || users.length === 0) return;
    
    currentUser = users[0];
    
    // Update stat cards
    updateStatCards(currentUser);
    
    // Get today's tasks
    const today = new Date().toISOString().split('T')[0];
    const tasks = await api(`/tasks/today?user_id=${currentUser.id}`);
    if (tasks) {
        updateTaskList(tasks);
        updateTasksView(tasks);
    }
    
    // Get analytics
    const analytics = await api(`/users/${currentUser.id}/analytics?days=7`);
    if (analytics) {
        updateChart(analytics.daily_trends);
    }
}

function updateStatCards(user) {
    // Streak
    const streakEl = document.getElementById('streak-value');
    animateNumber(streakEl, parseInt(streakEl.textContent) || 0, user.current_streak);
    
    const ring = document.getElementById('streak-ring');
    const streakPct = Math.min((user.current_streak / 30) * 100, 100);
    ring.setAttribute('stroke-dasharray', `${streakPct} ${100 - streakPct}`);
    
    // XP
    const xpEl = document.getElementById('xp-value');
    animateNumber(xpEl, parseInt(xpEl.textContent) || 0, user.total_xp);
    document.getElementById('level-badge').textContent = `Lv. ${user.level}`;
    
    // Rate
    const rateEl = document.getElementById('rate-value');
    const rate = Math.round(user.consistency_score * 100);
    rateEl.textContent = `${rate}%`;
}

function animateNumber(el, from, to) {
    const duration = 800;
    const start = performance.now();
    
    function step(timestamp) {
        const progress = Math.min((timestamp - start) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = Math.round(from + (to - from) * ease);
        el.textContent = current.toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
    }
    
    requestAnimationFrame(step);
}

function updateTaskList(tasks) {
    const list = document.getElementById('today-task-list');
    const completed = tasks.filter(t => t.status === 'completed').length;
    
    // Update stat card
    document.getElementById('tasks-today-value').textContent = `${completed}/${tasks.length}`;
    const pct = tasks.length > 0 ? (completed / tasks.length * 100) : 0;
    document.getElementById('tasks-progress').style.width = `${pct}%`;
    
    if (tasks.length === 0) {
        list.innerHTML = `
            <div class="task-empty">
                <div class="task-empty-icon">✨</div>
                <p>No tasks yet. Send a message to get started!</p>
            </div>`;
        return;
    }
    
    list.innerHTML = tasks.map(task => {
        const statusClass = task.status === 'completed' ? 'done' : task.status === 'missed' ? 'missed' : '';
        const statusIcon = { completed: '✅', pending: '⏳', missed: '❌', rescheduled: '🔄', in_progress: '🔄' }[task.status] || '⏳';
        
        return `
            <div class="task-item">
                <div class="task-check ${statusClass}" onclick="toggleTask('${task.id}', '${task.status}')"></div>
                <div class="task-info">
                    <div class="task-desc" style="${task.status === 'completed' ? 'text-decoration: line-through; opacity: 0.6;' : ''}">${task.description}</div>
                    <div class="task-meta">
                        <span>${task.category}</span>
                        <span>•</span>
                        <span class="task-badge ${task.difficulty}">${task.difficulty}</span>
                    </div>
                </div>
                <div class="task-xp">+${task.xp_reward} XP</div>
            </div>`;
    }).join('');
}

async function toggleTask(taskId, currentStatus) {
    if (currentStatus === 'completed') return;
    
    await api(`/tasks/${taskId}/complete`, { method: 'POST' });
    addActivity('✅', 'Task completed!');
    refreshDashboard();
}

function updateTasksView(tasks) {
    const grid = document.getElementById('tasks-grid');
    
    if (tasks.length === 0) {
        grid.innerHTML = `
            <div class="task-empty">
                <div class="task-empty-icon">📝</div>
                <p>No tasks found.</p>
            </div>`;
        return;
    }
    
    grid.innerHTML = tasks.map(task => {
        const statusIcon = { completed: '✅', pending: '⏳', missed: '❌', rescheduled: '🔄', in_progress: '🔄' }[task.status] || '⏳';
        const priorityColor = { urgent: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#22c55e' }[task.priority] || '#f59e0b';
        
        return `
            <div class="task-card">
                <div class="task-card-header">
                    <div class="task-card-status">${statusIcon}</div>
                    <div style="width:8px;height:8px;border-radius:50%;background:${priorityColor}"></div>
                </div>
                <div class="task-card-desc">${task.description}</div>
                <div class="task-card-meta">
                    <span class="task-badge ${task.difficulty}">${task.difficulty}</span>
                    <span class="task-badge" style="background:rgba(99,102,241,0.15);color:#818cf8">${task.category}</span>
                    <span class="task-xp">+${task.xp_reward} XP</span>
                </div>
            </div>`;
    }).join('');
}

// ─── Chart ──────────────────────────────────────────────────────
function updateChart(trends) {
    const container = document.getElementById('weekly-chart');
    
    if (!trends || trends.length === 0) {
        // Show sample chart
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        container.innerHTML = days.map(day => `
            <div class="chart-bar-group">
                <div class="chart-bar-wrap">
                    <div class="chart-bar total" style="height: 20%"></div>
                    <div class="chart-bar completed" style="height: 10%"></div>
                </div>
                <div class="chart-bar-label">${day}</div>
            </div>`).join('');
        return;
    }
    
    const maxTasks = Math.max(...trends.map(t => t.total), 1);
    
    container.innerHTML = trends.map(trend => {
        const day = new Date(trend.date).toLocaleDateString('en', { weekday: 'short' });
        const totalH = (trend.total / maxTasks * 180);
        const compH = (trend.completed / maxTasks * 180);
        
        return `
            <div class="chart-bar-group">
                <div class="chart-bar-wrap">
                    <div class="chart-bar total" style="height: ${totalH}px" title="Total: ${trend.total}"></div>
                    <div class="chart-bar completed" style="height: ${compH}px" title="Done: ${trend.completed}"></div>
                </div>
                <div class="chart-bar-label">${day}</div>
            </div>`;
    }).join('');
}

// ─── Task Filters ───────────────────────────────────────────────
document.getElementById('task-filter-date').valueAsDate = new Date();

document.getElementById('task-filter-status').addEventListener('change', filterTasks);
document.getElementById('task-filter-date').addEventListener('change', filterTasks);

async function filterTasks() {
    if (!currentUser) return;
    
    const dateVal = document.getElementById('task-filter-date').value;
    const status = document.getElementById('task-filter-status').value;
    
    const tasks = await api(`/tasks/?user_id=${currentUser.id}&start_date=${dateVal}&end_date=${dateVal}`);
    if (!tasks) return;
    
    const filtered = status === 'all' ? tasks : tasks.filter(t => t.status === status);
    updateTasksView(filtered);
}

// ─── Refresh Button ─────────────────────────────────────────────
document.getElementById('btn-refresh-chart').addEventListener('click', refreshDashboard);

// ─── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    refreshDashboard();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshDashboard, 30000);
    
    // Focus chat input when switching to chat
    document.querySelector('[data-view="chat"]').addEventListener('click', () => {
        setTimeout(() => chatInput.focus(), 100);
    });
});
