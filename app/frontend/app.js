const API = '/api';

async function loadTasks() {
    const container = document.getElementById('task-list');
    try {
        const res = await fetch(`${API}/tasks`);
        const tasks = await res.json();
        if (!tasks.length) {
            container.innerHTML = '<p class="empty">Aucune tâche pour le moment.</p>';
            return;
        }
        container.innerHTML = tasks.map(t => `
            <div class="task ${t.done ? 'done' : ''}">
                <div>
                    <div class="title"><strong>${escape(t.title)}</strong></div>
                    <div>${escape(t.description || '')}</div>
                    <div class="meta">⏱ ${t.duration} min</div>
                </div>
                <div class="actions">
                    <button class="primary" onclick="toggle(${t.id})">${t.done ? '↺' : '✓'}</button>
                    <button class="danger" onclick="remove(${t.id})">🗑</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<p class="empty">Erreur : ${e.message}</p>`;
    }
}

function escape(s) {
    return String(s).replace(/[&<>"']/g, c =>
        ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

document.getElementById('task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = {
        title: document.getElementById('title').value.trim(),
        description: document.getElementById('description').value.trim(),
        duration: parseInt(document.getElementById('duration').value) || 0,
    };
    if (!body.title) return;
    await fetch(`${API}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    e.target.reset();
    loadTasks();
});

async function toggle(id) {
    await fetch(`${API}/tasks/${id}/done`, { method: 'PATCH' });
    loadTasks();
}

async function remove(id) {
    if (!confirm('Supprimer cette tâche ?')) return;
    await fetch(`${API}/tasks/${id}`, { method: 'DELETE' });
    loadTasks();
}

loadTasks();