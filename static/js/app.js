/* ═══════════════════════════════════════════════════════════════
   AI EXAM MANAGER — Admin Panel JavaScript (app.js)
   Single-page application: 16 sections, charts, import/export, AI
   ═══════════════════════════════════════════════════════════════ */
'use strict';

// ── Global State ──────────────────────────────────────────────
const State = {
    currentSection: 'dashboard',
    charts: {},
    importSection: null,
    selectedFile: null,
    confirmCallback: null,
    wizardStep: 1,
    generatedExams: [],
    selectedSubjects: []
};

// ── DOM Ready ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initImportModal();
    initMobileToggle();
    navigateTo('dashboard');
});

// ── Navigation ────────────────────────────────────────────────
function initNavigation() {
    document.querySelectorAll('.nav-item[data-section]').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            navigateTo(item.dataset.section);
        });
    });
}

function navigateTo(section) {
    State.currentSection = section;
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    const active = document.querySelector(`.nav-item[data-section="${section}"]`);
    if (active) active.classList.add('active');

    const titles = {
        dashboard: 'Dashboard', invigilators: 'Invigilator Management',
        rooms: 'Room Management', subjects: 'Subject Management',
        students: 'Student Management', generator: 'AI Exam Generator',
        exams: 'Exam Sessions', seating: 'Seating Chart',
        duties: 'Duty List', inventory: 'Inventory Management',
        restocks: 'Restock Requests', branches: 'Branch Management',
        staffduties: 'Staff Duties', emergency: 'Emergency Handler',
        audit: 'Audit Log', settings: 'Settings'
    };
    document.getElementById('pageTitle').textContent = titles[section] || section;

    const sectionFns = {
        dashboard: renderDashboard, invigilators: renderInvigilators,
        rooms: renderRooms, subjects: renderSubjects,
        students: renderStudents, generator: renderGenerator,
        exams: renderExams, seating: renderSeating,
        duties: renderDuties, inventory: renderInventory,
        restocks: renderRestocks, branches: renderBranches,
        staffduties: renderStaffDuties, emergency: renderEmergency,
        audit: renderAudit, settings: renderSettings
    };

    const fn = sectionFns[section];
    if (fn) fn();

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
}

function initMobileToggle() {
    document.getElementById('mobileToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });
}

// ── Toast Notifications ───────────────────────────────────────
function toast(msg, type = 'info') {
    const icons = { success: 'check-circle', error: 'times-circle', warning: 'exclamation-triangle', info: 'info-circle' };
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i><span>${msg}</span>`;
    document.getElementById('toastContainer').appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(100%)'; setTimeout(() => t.remove(), 300); }, 3200);
}

// ── Confirm Modal ─────────────────────────────────────────────
function showConfirm(title, message, callback) {
    State.confirmCallback = callback;
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmModal').classList.add('active');
    document.getElementById('confirmBtn').onclick = () => { closeConfirmModal(); callback(); };
}
function closeConfirmModal() { document.getElementById('confirmModal').classList.remove('active'); }

// ── Import Modal ──────────────────────────────────────────────
function initImportModal() {
    const dz = document.getElementById('dropZone');
    const fi = document.getElementById('importFileInput');
    dz.addEventListener('click', () => fi.click());
    fi.addEventListener('change', e => handleFileSelect(e.target.files[0]));
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
    dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag-over'); if (e.dataTransfer.files[0]) handleFileSelect(e.dataTransfer.files[0]); });
}

function openImportModal(section) {
    State.importSection = section;
    State.selectedFile = null;
    document.getElementById('importStatus').style.display = 'none';
    document.getElementById('importBtn').disabled = true;
    document.getElementById('importFileInput').value = '';
    document.getElementById('dropZone').querySelector('p').textContent = 'Drag & drop your Excel file here';
    document.getElementById('downloadTemplateLink').href = `/api/template/${section}`;
    document.getElementById('importModal').classList.add('active');
}
function closeImportModal() { document.getElementById('importModal').classList.remove('active'); }

function handleFileSelect(file) {
    if (!file) return;
    State.selectedFile = file;
    document.getElementById('dropZone').querySelector('p').textContent = `Selected: ${file.name}`;
    document.getElementById('importBtn').disabled = false;
}

async function processImport() {
    if (!State.selectedFile || !State.importSection) return;
    const formData = new FormData();
    formData.append('file', State.selectedFile);
    const status = document.getElementById('importStatus');
    status.style.display = 'block';
    status.style.background = 'rgba(59,130,246,0.1)';
    status.style.color = '#93c5fd';
    status.textContent = 'Importing...';
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const res = await fetch(`/api/import/${State.importSection}`, { 
            method: 'POST', 
            body: formData,
            headers: { 
                'X-CSRFToken': csrfToken,
                'X-CSRF-Token': csrfToken 
            }
        });
        const data = await res.json();
        if (data.success) {
            status.style.background = 'rgba(16,185,129,0.1)';
            status.style.color = '#6ee7b7';
            status.textContent = `✓ Imported ${data.imported} records successfully!`;
            toast(`Imported ${data.imported} records into ${State.importSection}`, 'success');
            setTimeout(() => { closeImportModal(); navigateTo(State.importSection); }, 1500);
        } else {
            status.style.background = 'rgba(239,68,68,0.1)';
            status.style.color = '#fca5a5';
            status.textContent = `✗ Error: ${data.error}`;
        }
    } catch (e) {
        status.textContent = '✗ Upload failed. Please try again.';
    }
}

// ── API Helpers ───────────────────────────────────────────────
async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: {} };
    
    // Auto-inject CSRF Token for state-changing methods
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            opts.headers['X-CSRFToken'] = csrfToken;
            opts.headers['X-CSRF-Token'] = csrfToken;
        }
    }

    if (body) { 
        opts.headers['Content-Type'] = 'application/json'; 
        opts.body = JSON.stringify(body); 
    }

    // Cache-busting for GET to ensure freshness
    const targetUrl = method === 'GET' ? `${url}${url.includes('?') ? '&' : '?'}_t=${Date.now()}` : url;

    const res = await fetch(targetUrl, opts);
    if (!res.ok) {
        let err = `HTTP ${res.status}`;
        try { const d = await res.json(); err = d.error || d.message || err; } catch(e) {}
        throw new Error(err);
    }
    return res.json();
}

function exportSection(section) {
    window.location.href = `/api/export/${section}`;
    toast(`Downloading ${section} Excel export...`, 'info');
}

function exportPDF(section) {
    window.location.href = `/api/export/${section}/pdf`;
    toast(`Generating ${section} PDF...`, 'info');
}

// ── Dashboard ─────────────────────────────────────────────────
async function renderDashboard() {
    const ca = document.getElementById('contentArea');
    ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
    try {
        const data = await api('/api/stats');
        const h = data.resource_health || {};
        // Update health badge
        const hb = document.getElementById('healthBadge');
        hb.textContent = `\u2665 ${h.overall_health || 0}%`;
        const hClass = h.overall_health >= 70 ? '' : h.overall_health >= 40 ? 'warning' : 'critical';
        hb.className = `header-badge ${hClass}`;

        const statCards = [
            { icon: 'user-shield', color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', label: 'Invigilators', value: data.total_invigilators, sub: `${data.available_invigilators} available` },
            { icon: 'door-open', color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'Rooms', value: data.total_rooms, sub: `${data.available_rooms} available` },
            { icon: 'book', color: '#8b5cf6', bg: 'rgba(139,92,246,0.12)', label: 'Subjects', value: data.total_subjects, sub: `${data.total_students} students` },
            { icon: 'calendar-check', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Exams', value: data.total_exams, sub: `${data.scheduled_exams} scheduled` },
            { icon: 'boxes-stacked', color: '#06b6d4', bg: 'rgba(6,182,212,0.12)', label: 'Inventory Items', value: data.total_inventory, sub: `${data.low_stock_items} low stock` },
            { icon: 'clipboard-list', color: '#ec4899', bg: 'rgba(236,72,153,0.12)', label: 'Duties', value: data.total_duties, sub: `${data.attended_duties} attended` },
        ];

        ca.innerHTML = `
      <div class="stats-grid">${statCards.map(s => `
        <div class="stat-card">
          <div class="stat-icon" style="background:${s.bg};color:${s.color}"><i class="fas fa-${s.icon}"></i></div>
          <div class="stat-value" style="color:${s.color}">${s.value}</div>
          <div class="stat-label">${s.label}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${s.sub}</div>
        </div>`).join('')}
      </div>

      <div class="charts-grid">
        <div class="card">
          <div class="card-title"><i class="fas fa-chart-bar"></i>Students per Subject</div>
          <div class="chart-container"><canvas id="subjectsChart"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title"><i class="fas fa-heart-pulse"></i>Resource Health</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:8px">
            ${[['Capacity', h.capacity_score, '#10b981'], ['Invigilators', h.invigilator_score, '#3b82f6'], ['Supplies', h.supply_score, '#f59e0b'], ['Overall', h.overall_health, '#8b5cf6']].map(([l, v, c]) => `
            <div style="padding:16px;background:rgba(15,23,42,0.4);border-radius:10px;text-align:center">
              <div style="font-size:24px;font-weight:700;color:${c}">${v || 0}%</div>
              <div style="font-size:11px;color:var(--text-muted);margin-top:4px">${l}</div>
              <div class="progress-bar" style="margin-top:8px"><div class="progress-fill" style="width:${v || 0}%;background:${c}"></div></div>
            </div>`).join('')}
          </div>
          ${(h.recommendations || []).map(r => `<div class="ai-suggestion info"><i class="fas fa-robot"></i>${r}</div>`).join('')}
        </div>
        <div class="card">
          <div class="card-title"><i class="fas fa-chart-pie"></i>Invigilator Availability</div>
          <div class="chart-container"><canvas id="invChart"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title"><i class="fas fa-chart-line"></i>Exams by Date</div>
          <div class="chart-container"><canvas id="sessionsChart"></canvas></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-scroll"></i>Recent Activity</div>
        </div>
        <div>${(data.recent_activity || []).map(a => `
          <div class="activity-item">
            <div class="activity-icon ${a.log_type}"><i class="fas fa-${iconForType(a.log_type)}"></i></div>
            <div class="activity-text"><strong>${a.action}</strong><br><span style="font-size:12px;color:var(--text-muted)">${a.details}</span>
            <div class="activity-time"><i class="far fa-clock"></i> ${a.timestamp}</div></div>
          </div>`).join('') || '<div class="empty-state"><i class="fas fa-scroll"></i><p>No recent activity</p></div>'}
        </div>
      </div>`;

        // Subjects chart
        if (data.subjects_chart && data.subjects_chart.labels.length) {
            const ctx1 = document.getElementById('subjectsChart').getContext('2d');
            if (State.charts.subjects) State.charts.subjects.destroy();
            State.charts.subjects = new Chart(ctx1, { type: 'bar', data: { labels: data.subjects_chart.labels, datasets: [{ label: 'Students', data: data.subjects_chart.data, backgroundColor: data.subjects_chart.colors || '#3b82f6', borderRadius: 6, borderWidth: 0 }] }, options: chartOptions('Students') });
        }
        // Invigilator pie
        if (data.invigilator_chart) {
            const ctx2 = document.getElementById('invChart').getContext('2d');
            if (State.charts.inv) State.charts.inv.destroy();
            State.charts.inv = new Chart(ctx2, { type: 'doughnut', data: { labels: data.invigilator_chart.labels, datasets: [{ data: data.invigilator_chart.data, backgroundColor: data.invigilator_chart.colors, borderWidth: 0 }] }, options: { ...chartOptions(), cutout: '70%', plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 12 } } } } } });
        }
        // Sessions line chart
        if (data.sessions_chart && data.sessions_chart.labels.length) {
            const ctx3 = document.getElementById('sessionsChart').getContext('2d');
            if (State.charts.sessions) State.charts.sessions.destroy();
            State.charts.sessions = new Chart(ctx3, { type: 'line', data: { labels: data.sessions_chart.labels, datasets: [{ label: 'Exams', data: data.sessions_chart.data, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.4, pointBackgroundColor: '#3b82f6' }] }, options: chartOptions('Count') });
        }
    } catch (e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Failed to load dashboard: ${e.message}</p></div>`; }
}

function chartOptions(label = '') {
    return { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(148,163,184,0.1)', borderWidth: 1, titleColor: '#e2e8f0', bodyColor: '#94a3b8' } }, scales: { x: { grid: { color: 'rgba(148,163,184,0.05)' }, ticks: { color: '#64748b', font: { size: 11 } } }, y: { grid: { color: 'rgba(148,163,184,0.05)' }, ticks: { color: '#64748b', font: { size: 11 } } } } };
}

function iconForType(t) {
    const m = { create: 'plus-circle', update: 'pen', delete: 'trash', auth: 'shield-halved', import: 'file-import', export: 'file-export', ai: 'wand-magic-sparkles', emergency: 'triangle-exclamation', attendance: 'calendar-check', approve: 'check-circle', reject: 'times-circle' };
    return m[t] || 'circle-dot';
}

// ── Invigilators ──────────────────────────────────────────────
async function renderInvigilators() {
    const ca = document.getElementById('contentArea');
    ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
    try {
        const invs = await api('/api/invigilators');
        ca.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-user-shield"></i>Invigilators (${invs.length})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="openImportModal('invigilators')"><i class="fas fa-file-import"></i>Import</button>
            <button class="btn btn-secondary btn-sm" onclick="exportSection('invigilators')"><i class="fas fa-file-export"></i>Export</button>
            <button class="btn btn-primary btn-sm" onclick="showInvForm()"><i class="fas fa-plus"></i>Add</button>
          </div>
        </div>
        <div id="invForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)">
          <div class="form-row">
            <div class="form-group"><label>Name *</label><input class="form-control" id="invName" placeholder="Full name"></div>
            <div class="form-group"><label>Department</label><input class="form-control" id="invDept" placeholder="e.g. Computer Science"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Email</label><input class="form-control" id="invEmail" type="email" placeholder="email@college.edu"></div>
            <div class="form-group"><label>Phone</label><input class="form-control" id="invPhone" placeholder="+91 ..."></div>
            <div class="form-group"><label>Max Duties</label><input class="form-control" id="invMaxDuties" type="number" value="5" min="1"></div>
            <div class="form-group"><label>Group ID</label><input class="form-control" id="invGroupId" type="number" value="0" min="0" title="Same group ID = social peers (anti-cheat)"></div>
          </div>
          <div class="btn-group">
            <button class="btn btn-primary" onclick="saveInvigilator()"><i class="fas fa-save"></i>Save</button>
            <button class="btn btn-secondary" onclick="document.getElementById('invForm').style.display='none'">Cancel</button>
          </div>
        </div>
        <div class="table-container">
          <table><thead><tr><th>Name</th><th>Department</th><th>Email</th><th>Phone</th><th>Duties</th><th>Available</th><th>Actions</th></tr></thead>
          <tbody>${invs.length ? invs.map(i => `
            <tr>
              <td><strong>${i.name}</strong></td><td>${i.department || '—'}</td>
              <td>${i.email || '—'}</td><td>${i.phone || '—'}</td>
              <td><div style="display:flex;align-items:center;gap:8px"><span>${i.duty_count}/${i.max_duties}</span><div class="progress-bar" style="width:60px"><div class="progress-fill" style="width:${Math.min(100, (i.duty_count / Math.max(i.max_duties, 1)) * 100)}%;background:${i.duty_count >= i.max_duties ? '#ef4444' : '#10b981'}"></div></div></div></td>
              <td><label class="toggle"><input type="checkbox" ${i.available ? 'checked' : ''} onchange="toggleInv(${i.id})"><span class="toggle-slider"></span></label></td>
              <td><div class="btn-group"><button class="btn btn-danger btn-icon btn-sm" onclick="deleteInv(${i.id},'${i.name}')"><i class="fas fa-trash"></i></button></div></td>
            </tr>`).join('') : '<tr><td colspan="7" class="empty-state"><i class="fas fa-user-slash"></i><p>No invigilators. Add one to begin.</p></td></tr>'}
          </tbody></table>
        </div>
      </div>`;
    } catch (e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}

function showInvForm() { document.getElementById('invForm').style.display = 'block'; }

async function saveInvigilator() {
    const name = document.getElementById('invName').value.trim();
    if (!name) { toast('Name is required', 'error'); return; }
    try {
        await api('/api/invigilators', 'POST', { name, department: document.getElementById('invDept').value, email: document.getElementById('invEmail').value, phone: document.getElementById('invPhone').value, max_duties: parseInt(document.getElementById('invMaxDuties').value) || 5, group_id: parseInt(document.getElementById('invGroupId').value) || 0 });
        toast('Invigilator added!', 'success');
        renderInvigilators();
    } catch (e) { toast(e.message, 'error'); }
}

async function toggleInv(id) {
    try { await api(`/api/invigilators/${id}/toggle`, 'POST'); toast('Availability updated', 'success'); }
    catch (e) { toast(e.message, 'error'); renderInvigilators(); }
}

async function deleteInv(id, name) {
    showConfirm('Delete Invigilator', `Remove "${name}"? This cannot be undone.`, async () => {
        try { await api(`/api/invigilators/${id}`, 'DELETE'); toast('Invigilator deleted', 'success'); renderInvigilators(); }
        catch (e) { toast(e.message, 'error'); }
    });
}

// ── Rooms ─────────────────────────────────────────────────────
async function renderRooms() {
    const ca = document.getElementById('contentArea');
    ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
    try {
        const rooms = await api('/api/rooms');
        ca.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-door-open"></i>Rooms (${rooms.length})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="openImportModal('rooms')"><i class="fas fa-file-import"></i>Import</button>
            <button class="btn btn-secondary btn-sm" onclick="exportSection('rooms')"><i class="fas fa-file-export"></i>Export</button>
            <button class="btn btn-primary btn-sm" onclick="showRoomForm()"><i class="fas fa-plus"></i>Add</button>
          </div>
        </div>
        <div id="roomForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)">
          <div class="form-row">
            <div class="form-group"><label>Room Name *</label><input class="form-control" id="rName" placeholder="e.g. Hall A"></div>
            <div class="form-group"><label>Capacity *</label><input class="form-control" id="rCap" type="number" value="40" min="1"></div>
            <div class="form-group"><label>Floor</label><input class="form-control" id="rFloor" placeholder="e.g. 1st Floor"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Room Type</label><select class="form-control" id="rType"><option>Classroom</option><option>Exam Hall</option><option>Lab</option><option>Seminar Hall</option></select></div>
            <div class="form-group"><label>Buffer Seats</label><input class="form-control" id="rBuffer" type="number" value="5" min="0"></div>
            <div class="form-group"><label>Equipment</label><input class="form-control" id="rEquip" placeholder="e.g. Projector, AC"></div>
          </div>
          <div class="btn-group">
            <button class="btn btn-primary" onclick="saveRoom()"><i class="fas fa-save"></i>Save</button>
            <button class="btn btn-secondary" onclick="document.getElementById('roomForm').style.display='none'">Cancel</button>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px">
          ${rooms.length ? rooms.map(r => `
            <div class="card" style="margin:0;padding:18px">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
                <div>
                  <div style="font-weight:600;font-size:15px">${r.name}</div>
                  <div style="font-size:12px;color:var(--text-muted)">${r.floor} · ${r.room_type}</div>
                </div>
                <span class="badge ${r.is_available ? 'badge-success' : 'badge-danger'}">${r.is_available ? 'Available' : 'Unavailable'}</span>
              </div>
              <div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
                <i class="fas fa-users" style="color:var(--accent)"></i> Capacity: <strong>${r.capacity}</strong> &nbsp;
                <i class="fas fa-chair" style="color:var(--warning)"></i> Buffer: <strong>${r.buffer_seats}</strong>
              </div>
              ${r.equipment ? `<div style="font-size:12px;color:var(--text-muted);margin-bottom:12px"><i class="fas fa-tools"></i> ${r.equipment}</div>` : ''}
              <div class="btn-group">
                <button class="btn btn-secondary btn-sm" onclick="toggleRoom(${r.id})">${r.is_available ? 'Mark Unavailable' : 'Mark Available'}</button>
                <button class="btn btn-danger btn-icon btn-sm" onclick="deleteRoom(${r.id},'${r.name}')"><i class="fas fa-trash"></i></button>
              </div>
            </div>`).join('') : '<div class="empty-state" style="grid-column:1/-1"><i class="fas fa-door-closed"></i><p>No rooms added yet.</p></div>'}
        </div>
      </div>`;
    } catch (e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}

function showRoomForm() { document.getElementById('roomForm').style.display = 'block'; }

async function saveRoom() {
    const name = document.getElementById('rName').value.trim();
    if (!name) { toast('Room name is required', 'error'); return; }
    try {
        await api('/api/rooms', 'POST', { name, capacity: parseInt(document.getElementById('rCap').value) || 40, floor: document.getElementById('rFloor').value, room_type: document.getElementById('rType').value, buffer_seats: parseInt(document.getElementById('rBuffer').value) || 5, equipment: document.getElementById('rEquip').value });
        toast('Room added!', 'success'); renderRooms();
    } catch (e) { toast(e.message, 'error'); }
}

async function toggleRoom(id) {
    try {
        const r = await api(`/api/rooms/${id}`, 'GET');
        await api(`/api/rooms/${id}`, 'PUT', { is_available: !r.is_available });
        toast('Room availability updated', 'success'); renderRooms();
    } catch (e) {
        // Simpler toggle approach
        const rooms = await api('/api/rooms');
        const room = rooms.find(r => r.id === id);
        if (room) { await api(`/api/rooms/${id}`, 'PUT', { is_available: !room.is_available }); toast('Updated', 'success'); renderRooms(); }
    }
}

async function deleteRoom(id, name) {
    showConfirm('Delete Room', `Remove room "${name}"?`, async () => {
        try { await api(`/api/rooms/${id}`, 'DELETE'); toast('Room deleted', 'success'); renderRooms(); }
        catch (e) { toast(e.message, 'error'); }
    });
}

// ── Subjects ──────────────────────────────────────────────────
async function renderSubjects() {
    const ca = document.getElementById('contentArea');
    ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
    try {
        const subjects = await api('/api/subjects');
        ca.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-book"></i>Subjects (${subjects.length})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="openImportModal('subjects')"><i class="fas fa-file-import"></i>Import</button>
            <button class="btn btn-secondary btn-sm" onclick="exportSection('subjects')"><i class="fas fa-file-export"></i>Export</button>
            <button class="btn btn-primary btn-sm" onclick="showSubjForm()"><i class="fas fa-plus"></i>Add</button>
          </div>
        </div>
        <div id="subjForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)">
          <div class="form-row">
            <div class="form-group"><label>Subject Name *</label><input class="form-control" id="sName" placeholder="e.g. Data Structures"></div>
            <div class="form-group"><label>Code</label><input class="form-control" id="sCode" placeholder="e.g. CS301"></div>
            <div class="form-group"><label>Branch</label><input class="form-control" id="sBranch" placeholder="e.g. Computer Science"></div>
            <div class="form-group"><label>Student Count</label><input class="form-control" id="sCount" type="number" value="0" min="0"></div>
            <div class="form-group"><label>Color</label><input class="form-control" id="sColor" type="color" value="#4A90D9"></div>
          </div>
          <div class="btn-group">
            <button class="btn btn-primary" onclick="saveSubject()"><i class="fas fa-save"></i>Save</button>
            <button class="btn btn-secondary" onclick="document.getElementById('subjForm').style.display='none'">Cancel</button>
          </div>
        </div>
        <div class="table-container">
          <table><thead><tr><th>Subject</th><th>Code</th><th>Branch</th><th>Students</th><th>Actions</th></tr></thead>
          <tbody>${subjects.length ? subjects.map(s => `
            <tr>
              <td><span class="color-dot" style="background:${s.color};margin-right:8px"></span><strong>${s.name}</strong></td>
              <td><span class="badge badge-info">${s.code || '—'}</span></td>
              <td>${s.branch || '—'}</td>
              <td><div style="display:flex;align-items:center;gap:8px"><span>${s.student_count}</span></div></td>
              <td><button class="btn btn-danger btn-icon btn-sm" onclick="deleteSubject(${s.id},'${s.name}')"><i class="fas fa-trash"></i></button></td>
            </tr>`).join('') : '<tr><td colspan="5"><div class="empty-state"><i class="fas fa-book-open"></i><p>No subjects yet.</p></div></td></tr>'}
          </tbody></table>
        </div>
      </div>`;
    } catch (e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}

function showSubjForm() { document.getElementById('subjForm').style.display = 'block'; }

async function saveSubject() {
    const name = document.getElementById('sName').value.trim();
    if (!name) { toast('Subject name required', 'error'); return; }
    try {
        await api('/api/subjects', 'POST', { name, code: document.getElementById('sCode').value, branch: document.getElementById('sBranch').value, student_count: parseInt(document.getElementById('sCount').value) || 0, color: document.getElementById('sColor').value });
        toast('Subject added!', 'success'); renderSubjects();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteSubject(id, name) {
    showConfirm('Delete Subject', `Remove "${name}"?`, async () => {
        try { await api(`/api/subjects/${id}`, 'DELETE'); toast('Deleted', 'success'); renderSubjects(); }
        catch (e) { toast(e.message, 'error'); }
    });
}

// ── Students ──────────────────────────────────────────────────
async function renderStudents() {
    const ca = document.getElementById('contentArea');
    ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
    try {
        const students = await api('/api/students');
        ca.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-graduation-cap"></i>Students (${students.length})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="openImportModal('students')"><i class="fas fa-file-import"></i>Import</button>
            <button class="btn btn-secondary btn-sm" onclick="exportSection('students')"><i class="fas fa-file-export"></i>Export</button>
            <button class="btn btn-primary btn-sm" onclick="showStudForm()"><i class="fas fa-plus"></i>Add</button>
          </div>
        </div>
        <div id="studForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)">
          <div class="form-row">
            <div class="form-group"><label>Full Name *</label><input class="form-control" id="stName" placeholder="Student name"></div>
            <div class="form-group"><label>Roll No *</label><input class="form-control" id="stRoll" placeholder="e.g. CS2024001"></div>
            <div class="form-group"><label>Branch</label><input class="form-control" id="stBranch" placeholder="e.g. Computer Science"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Group ID <span style="color:var(--text-muted);font-size:11px">(for anti-cheat seating)</span></label><input class="form-control" id="stGroup" type="number" value="0" min="0"></div>
            <div class="form-group"><label>Email</label><input class="form-control" id="stEmail" type="email" placeholder="student@email.com"></div>
            <div class="form-group"><label>Phone</label><input class="form-control" id="stPhone" placeholder="Phone number"></div>
          </div>
          <div class="btn-group">
            <button class="btn btn-primary" onclick="saveStudent()"><i class="fas fa-save"></i>Save</button>
            <button class="btn btn-secondary" onclick="document.getElementById('studForm').style.display='none'">Cancel</button>
          </div>
        </div>
        <div class="table-container">
          <table><thead><tr><th>Name</th><th>Roll No</th><th>Branch</th><th>Group ID</th><th>Email</th><th>Actions</th></tr></thead>
          <tbody>${students.length ? students.map(s => `
            <tr>
              <td><strong>${s.name}</strong></td>
              <td><span class="badge badge-info">${s.roll_no}</span></td>
              <td>${s.branch || '—'}</td>
              <td>${s.group_id || '—'}</td>
              <td>${s.email || '—'}</td>
              <td><button class="btn btn-danger btn-icon btn-sm" onclick="deleteStudent(${s.id},'${s.name}')"><i class="fas fa-trash"></i></button></td>
            </tr>`).join('') : '<tr><td colspan="6"><div class="empty-state"><i class="fas fa-user-graduate"></i><p>No students yet. Import from Excel to begin.</p></div></td></tr>'}
          </tbody></table>
        </div>
      </div>`;
    } catch (e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}

function showStudForm() { document.getElementById('studForm').style.display = 'block'; }

async function saveStudent() {
    const name = document.getElementById('stName').value.trim();
    const roll_no = document.getElementById('stRoll').value.trim();
    if (!name || !roll_no) { toast('Name and Roll No are required', 'error'); return; }
    try {
        await api('/api/students', 'POST', { name, roll_no, branch: document.getElementById('stBranch').value, group_id: parseInt(document.getElementById('stGroup').value) || 0, email: document.getElementById('stEmail').value, phone: document.getElementById('stPhone').value });
        toast('Student added!', 'success'); renderStudents();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteStudent(id, name) {
    showConfirm('Delete Student', `Remove "${name}"?`, async () => {
        try { await api(`/api/students/${id}`, 'DELETE'); toast('Deleted', 'success'); renderStudents(); }
        catch (e) { toast(e.message, 'error'); }
    });
}

// ── AI Exam Generator (Modern Single-Page Interface) ─────────────────────────────────────────
async function renderGenerator() {
  const ca = document.getElementById('contentArea');
  let subjects = [], settings = {};
  
  ca.innerHTML = `
    <div style="text-align:center;padding:80px">
      <div class="ai-orb" style="width:120px; height:120px; margin:0 auto"></div>
      <div style="margin-top:24px; color:var(--text-muted); font-size:14px; letter-spacing:2px">SYNCHRONIZING AI CORES...</div>
    </div>`;
    
  try { [subjects, settings] = await Promise.all([api('/api/subjects'), api('/api/settings')]); } catch(e) {
    toast('Hardware initialization failed. Verify database connectivity.', 'error');
  }
  
  const today = new Date().toISOString().split('T')[0];
  const nextWeek = new Date(Date.now()+7*86400000).toISOString().split('T')[0];

  ca.innerHTML = `
    <div class="wizard-grid">
      
      <!-- Left: Configuration Dashboard -->
      <div class="card" style="padding:32px; border:1px solid var(--border-hover); background:linear-gradient(135deg, rgba(15,23,42,0.6) 0%, rgba(15,23,42,0.9) 100%)">
        <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:32px">
          <div>
            <h2 style="font-size:28px; font-weight:700; background:linear-gradient(to right, #60a5fa, #a855f7); -webkit-background-clip:text; -webkit-text-fill-color:transparent">Neural Scheduler</h2>
            <p style="color:var(--text-muted); font-size:14px">Configure curriculum parameters for temporal synthesis.</p>
          </div>
          <div style="background:rgba(16,185,129,0.1); color:#10b981; padding:6px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:1px; border:1px solid rgba(16,185,129,0.2)">
            ACTIVE ENGINE v2.4
          </div>
        </div>

        <div style="margin-bottom:32px">
          <label style="display:block; font-size:12px; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:12px">Execution Window</label>
          <div class="form-row" style="grid-template-columns:1fr 1fr 120px; gap:16px">
            <div class="form-group mb-0">
               <input class="form-control" id="genStart" type="date" value="${today}">
            </div>
            <div class="form-group mb-0">
               <input class="form-control" id="genEnd" type="date" value="${nextWeek}">
            </div>
            <div class="form-group mb-0">
              <select class="form-control" id="genSessions">
                <option value="1">1 Slot</option>
                <option value="2" selected>2 Slots</option>
              </select>
            </div>
          </div>
        </div>

        <div style="margin-bottom:32px">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px">
            <label style="font-size:12px; font-weight:700; color:var(--text-muted); text-transform:uppercase">Subject Matrices</label>
            <div style="font-size:11px">
              <a href="#" onclick="toggleAllSubjects(true);return false" style="color:var(--accent);text-decoration:none">Select All</a> &middot; 
              <a href="#" onclick="toggleAllSubjects(false);return false" style="color:var(--text-muted);text-decoration:none">Clear</a>
            </div>
          </div>
          <div id="subjGrid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:12px; max-height:280px; overflow-y:auto; padding-right:8px">
            ${subjects.map(s=>`
              <div class="subject-pill active" data-id="${s.id}" onclick="togglePill(this)">
                <div class="dot" style="background:${s.color}; box-shadow:0 0 10px ${s.color}"></div>
                <div style="flex:1">
                  <div style="font-size:13px; font-weight:600">${s.name}</div>
                  <div style="font-size:10px; opacity:0.6">${s.code} &middot; ${s.student_count} PAX</div>
                </div>
                <i class="fas fa-check-circle" style="color:var(--accent); font-size:14px"></i>
              </div>`).join('')}
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; padding-top:24px; border-top:1px solid var(--border)">
          <div style="display:flex; align-items:center; gap:12px">
            <i class="fas fa-microchip" style="color:var(--text-muted); font-size:20px"></i>
            <div>
              <div style="font-size:12px; font-weight:600">Quantum Isolation</div>
              <div style="font-size:10px; color:var(--text-muted)">Social Graph Guarding Active</div>
            </div>
          </div>
          <button class="btn btn-primary pulse-emerald" id="generateBtn" onclick="runGenerate()" style="padding:14px 40px; font-weight:700; font-size:16px; border-radius:30px">
            <i class="fas fa-bolt"></i> Synthesize Schedule
          </button>
        </div>
      </div>

      <!-- Right: Real-time Output Console -->
      <div style="display:flex; flex-direction:column; gap:20px">
        <div class="card" style="background:#000; border:1px solid #333; height:400px; display:flex; flex-direction:column">
          <div style="padding:12px 16px; background:#111; border-bottom:1px solid #222; display:flex; justify-content:space-between; align-items:center">
            <div style="font-size:11px; font-weight:700; color:#666; letter-spacing:1px">DIAGNOSTIC CONSOLE</div>
            <div style="display:flex; gap:6px">
              <span style="width:8px; height:8px; border-radius:50%; background:#ff5f56"></span>
              <span style="width:8px; height:8px; border-radius:50%; background:#ffbd2e"></span>
              <span style="width:8px; height:8px; border-radius:50%; background:#27c93f"></span>
            </div>
          </div>
          <div id="aiConsole" class="ai-console" style="flex:1; border:none; height:auto; background:transparent">
            <div class="console-line">> KERNEL: AI Exam Scheduler v2.4 initialized.</div>
            <div class="console-line">> READY: Waiting for synthesis parameters...</div>
          </div>
        </div>

        <div class="card" style="text-align:center; background:linear-gradient(rgba(56, 189, 248, 0.05), transparent)">
          <i class="fas fa-circle-info" style="font-size:24px; color:var(--accent); margin-bottom:12px"></i>
          <div style="font-size:14px; font-weight:600">Deterministic Allocation</div>
          <p style="font-size:12px; color:var(--text-muted); margin-top:8px">The AI uses a Constraint Satisfaction Problem (CSP) solver to eliminate scheduling overlaps.</p>
        </div>
      </div>

    </div>
  `;
}

function togglePill(el) {
  el.classList.toggle('active');
  const icon = el.querySelector('i');
  if(el.classList.contains('active')) {
    icon.className = 'fas fa-check-circle';
    icon.style.color = 'var(--accent)';
  } else {
    icon.className = 'far fa-circle';
    icon.style.color = 'var(--text-muted)';
  }
}

function toggleAllSubjects(val) {
  document.querySelectorAll('.subject-pill').forEach(el => {
    if(val) el.classList.add('active'); else el.classList.remove('active');
    const icon = el.querySelector('i');
    if(el.classList.contains('active')) {
      icon.className = 'fas fa-check-circle';
      icon.style.color = 'var(--accent)';
    } else {
      icon.className = 'far fa-circle';
      icon.style.color = 'var(--text-muted)';
    }
  });
}

function updateConsole(msg, type="info") {
  const cons = document.getElementById('aiConsole');
  if(!cons) return;
  const line = document.createElement('div');
  line.className = `console-line ${type}`;
  line.innerHTML = `> ${msg}`;
  cons.appendChild(line);
  cons.scrollTop = cons.scrollHeight;
}

// Ensure the old goToStep2 and goToStep3 are dead code explicitly overridden or removed.

async function runGenerate() {
  const activePills = document.querySelectorAll('.subject-pill.active');
  const selectedSubjects = Array.from(activePills).map(p => parseInt(p.dataset.id));
  
  if (!selectedSubjects.length) { 
    updateConsole('ERROR: No curriculum selected for synthesis.', 'error');
    toast('Select at least one subject','error'); 
    return; 
  }

  const s = document.getElementById('genStart').value;
  const e = document.getElementById('genEnd').value;
  const ses = parseInt(document.getElementById('genSessions').value);
  
  if (!s || !e) { 
    updateConsole('ERROR: Temporal window is undefined.', 'error');
    toast('Start and End dates required','error'); 
    return; 
  }

  const btn = document.getElementById('generateBtn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Synthesizing...'; }
  
  updateConsole('INITIATING TIMETABLE SYNTHESIS...', 'warning');
  updateConsole('Applying Social Graph Isolation filters...', 'info');
  
  try {
    const data = await api('/api/exams/generate','POST',{
      start_date: s, 
      end_date: e, 
      sessions_per_day: ses, 
      subject_ids: selectedSubjects
    });
    
    updateConsole('SYNTHESIS COMPLETE. VERIFYING SEATING MATRICES...', 'success');
    await new Promise(r => setTimeout(r, 800)); // Aesthetic delay
    
    const ca = document.getElementById('contentArea');
    ca.innerHTML = `
      <div class="card" style="animation: fadeInUp 0.5s ease; border: 1px solid var(--success); background:rgba(16, 185, 129, 0.02)">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px">
          <div>
            <h3 style="font-size:20px; font-weight:700; color:var(--success)">
              <i class="fas fa-check-circle"></i> Timetable Generated Successfully
            </h3>
            <p style="font-size:13px; color:var(--text-muted)">The exam schedule has been committed to the database.</p>
          </div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="renderGenerator()"><i class="fas fa-redo"></i> Reset AI</button>
            <button class="btn btn-secondary btn-sm" onclick="exportSection('exams')"><i class="fas fa-file-excel"></i> Excel Export</button>
            <button class="btn btn-primary btn-sm" onclick="navigateTo('exams')"><i class="fas fa-arrow-right"></i> View Grid</button>
          </div>
        </div>

        <div class="stats-grid" style="grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:32px">
          <div class="stat-card">
            <div class="stat-label">Exams Created</div>
            <div class="stat-value" style="color:var(--accent)">${data.total_exams}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Duties Assigned</div>
            <div class="stat-value" style="color:var(--purple)">${data.duties_assigned}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Conflicts</div>
            <div class="stat-value" style="color:${data.conflicts.length?'var(--danger)':'var(--success)'}">${data.conflicts.length}</div>
          </div>
        </div>

        <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; overflow:hidden">
          <div style="padding:12px 16px; background:rgba(255,255,255,0.03); font-size:12px; font-weight:700; color:var(--text-muted)">PREVIEW TIMELINE</div>
          <div style="max-height:300px; overflow-y:auto; padding:8px">
            ${data.exams.length ? data.exams.map(ex => `
              <div style="display:flex; align-items:center; gap:16px; padding:12px; border-bottom:1px solid var(--border)">
                <div style="text-align:center; min-width:60px">
                  <div style="font-size:10px; color:var(--text-muted)">${ex.date.split('-').slice(1).join('/')}</div>
                  <div style="font-size:12px; font-weight:700">${ex.session_label}</div>
                </div>
                <div style="flex:1">
                  <div style="font-size:14px; font-weight:600">${ex.subject_name}</div>
                  <div style="font-size:11px; color:var(--text-muted)">${ex.room_name} &bull; ${ex.start_time}</div>
                </div>
                <div class="badge badge-info">${ex.subject_code}</div>
              </div>
            `).join('') : '<div style="padding:40px; text-align:center; color:var(--text-muted)">No exams returned. Check logs.</div>'}
          </div>
        </div>
      </div>
    `;
    toast('Synthesis finalized','success');
  } catch(e) { 
    updateConsole('FATAL ERROR: ' + e.message, 'error');
    toast(e.message,'error'); 
    if(btn){ btn.disabled = false; btn.innerHTML = '<i class="fas fa-bolt"></i> Retry Synthesis'; }
  }
}

// ── Exam Sessions ─────────────────────────────────────────────
async function renderExams() {
  const ca = document.getElementById('contentArea');
  ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try {
    const res = await api('/api/exams');
    const exams = res.data || [];
    ca.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-calendar-check"></i>Sessions (${res.total || 0})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="exportSection('exams')"><i class="fas fa-file-excel"></i>Excel</button>
            <button class="btn btn-secondary btn-sm" onclick="exportPDF('exams')"><i class="fas fa-file-pdf"></i>PDF</button>
            <button class="btn btn-warning btn-sm" onclick="clearAllExams()"><i class="fas fa-trash"></i>Clear All</button>
            <button class="btn btn-primary btn-sm" onclick="navigateTo('generator')"><i class="fas fa-wand-magic-sparkles"></i>Generate</button>
          </div>
        </div>
        <div class="table-container"><table><thead><tr><th>Subject</th><th>Code</th><th>Room</th><th>Date</th><th>Time</th><th>Session</th><th>Status</th><th>Del</th></tr></thead>
        <tbody>${exams.length?exams.map(e=>`<tr><td><strong>${e.subject_name}</strong></td><td><span class="badge badge-info">${e.subject_code||'—'}</span></td><td>${e.room_name}</td><td>${e.date}</td><td>${e.start_time}–${e.end_time}</td><td><span class="badge badge-purple">${e.session_label}</span></td><td><span class="badge ${e.status==='completed'?'badge-success':e.status==='cancelled'?'badge-danger':'badge-warning'}">${e.status}</span></td><td><button class="btn btn-danger btn-icon btn-sm" onclick="deleteExam(${e.id})"><i class="fas fa-trash"></i></button></td></tr>`).join(''):'<tr><td colspan="8"><div class="empty-state"><i class="fas fa-calendar-xmark"></i><p>No exams. Use the AI Generator.</p><button class="btn btn-primary" onclick="navigateTo(\'generator\')"><i class="fas fa-wand-magic-sparkles"></i>Generate Now</button></div></td></tr>'}</tbody></table></div>
      </div>`;
  } catch(e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}
async function deleteExam(id) { try{await api(`/api/exams/${id}`,'DELETE');toast('Deleted','success');renderExams();}catch(e){toast(e.message,'error');} }
async function clearAllExams() { showConfirm('Clear All Exams','Delete all exams, seating, and duties? Cannot be undone.',async()=>{try{await api('/api/exams/clear','POST');toast('Cleared','success');renderExams();}catch(e){toast(e.message,'error');}}); }

// ── Seating Chart ─────────────────────────────────────────────
async function renderSeating() {
  const ca = document.getElementById('contentArea');
  ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try {
    const [seats, examsRes, rooms] = await Promise.all([
      api('/api/seating'),
      api('/api/exams?per_page=100'),
      api('/api/rooms')
    ]);
    const exams = examsRes.data || [];
    window._allSeats = seats; window._allRooms = rooms;
    ca.innerHTML = `
      <div class="card">
        <div class="card-header"><div class="card-title"><i class="fas fa-chair"></i>Seating Chart</div>
          <select class="form-control" id="seatExamFilter" style="width:240px" onchange="filterSeats()">
            <option value="">All Exams</option>${exams.map(e=>`<option value="${e.id}">${e.subject_name} – ${e.date}</option>`).join('')}
          </select>
        </div>
        ${!seats.length?'<div class="alert-banner warning"><i class="fas fa-info-circle"></i>No seating yet. Generate a timetable with students first.</div>':''}
        <div id="seatingContent">${seats.length?renderSeatingGrid(seats,rooms):'<div class="empty-state"><i class="fas fa-chair"></i><p>Seating appears after exam generation with students.</p></div>'}</div>
      </div>`;
  } catch(e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}
function filterSeats(){const id=parseInt(document.getElementById('seatExamFilter').value)||null;const f=window._allSeats?(id?window._allSeats.filter(s=>s.exam_id===id):window._allSeats):[];document.getElementById('seatingContent').innerHTML=f.length?renderSeatingGrid(f,window._allRooms||[]):'<div class="empty-state"><i class="fas fa-chair"></i><p>No seats for selected exam.</p></div>';}
function renderSeatingGrid(seats,rooms){const byRoom={};seats.forEach(s=>{if(!byRoom[s.room_id])byRoom[s.room_id]=[];byRoom[s.room_id].push(s);});return Object.entries(byRoom).map(([rid,rs])=>{const room=rooms.find(r=>r.id==rid);return`<div style="margin-bottom:24px"><div style="font-weight:600;margin-bottom:12px;color:var(--text-secondary)"><i class="fas fa-door-open"></i> ${room?room.name:'Room '+rid} — ${rs.length} students</div><div class="seating-grid">${rs.map(s=>`<div class="seat occupied" title="${s.student_name} (${s.student_roll})">${s.seat_no}</div>`).join('')}</div></div>`;}).join('');}

// ── Duty List ─────────────────────────────────────────────────
async function renderDuties() {
  const ca = document.getElementById('contentArea');
  ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try {
    const duties = await api('/api/duties');
    const attended=duties.filter(d=>d.attended).length;
    ca.innerHTML = `
      <div class="card">
        <div class="card-header"><div class="card-title"><i class="fas fa-clipboard-list"></i>Duty Assignments (${duties.length})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="window.location.href='/api/export/attendance/teacher'"><i class="fas fa-file-excel"></i>Teacher Excel</button>
            <button class="btn btn-secondary btn-sm" onclick="window.location.href='/api/export/attendance/teacher/pdf'"><i class="fas fa-file-pdf"></i>Teacher PDF</button>
          </div>
        </div>
        <div class="stats-grid" style="grid-template-columns:repeat(3,1fr);margin-bottom:20px">
          <div class="stat-card"><div class="stat-icon" style="background:rgba(59,130,246,0.12);color:#3b82f6"><i class="fas fa-list"></i></div><div class="stat-value" style="color:#3b82f6">${duties.length}</div><div class="stat-label">Total</div></div>
          <div class="stat-card"><div class="stat-icon" style="background:rgba(16,185,129,0.12);color:#10b981"><i class="fas fa-check"></i></div><div class="stat-value" style="color:#10b981">${attended}</div><div class="stat-label">Attended</div></div>
          <div class="stat-card"><div class="stat-icon" style="background:rgba(245,158,11,0.12);color:#f59e0b"><i class="fas fa-clock"></i></div><div class="stat-value" style="color:#f59e0b">${duties.length-attended}</div><div class="stat-label">Pending</div></div>
        </div>
        <div class="table-container"><table><thead><tr><th>Invigilator</th><th>Subject</th><th>Room</th><th>Date</th><th>Attended</th><th>Check-in</th><th>Action</th></tr></thead>
        <tbody>${duties.length?duties.map(d=>`<tr><td><strong>${d.invigilator_name}</strong></td><td>${d.subject_name||'—'}</td><td>${d.room_name||'—'}</td><td>${d.date}</td><td><span class="badge ${d.attended?'badge-success':'badge-warning'}">${d.attended?'Yes':'No'}</span></td><td>${d.check_in_time||'—'}</td><td>${!d.attended?`<button class="btn btn-success btn-sm" onclick="markDutyAttended(${d.id})"><i class="fas fa-check"></i>Mark</button>`:'✓'}</td></tr>`).join(''):'<tr><td colspan="7"><div class="empty-state"><i class="fas fa-clipboard"></i><p>No duties. Generate a timetable first.</p></div></td></tr>'}</tbody></table></div>
      </div>`;
  } catch(e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}
async function markDutyAttended(id){const now=new Date();const t=now.getHours().toString().padStart(2,'0')+':'+now.getMinutes().toString().padStart(2,'0');try{await api(`/api/duties/${id}/attend`,'POST',{attended:true,check_in_time:t});toast('Marked!','success');renderDuties();}catch(e){toast(e.message,'error');}}

// ── Inventory ─────────────────────────────────────────────────
async function renderInventory() {
  const ca = document.getElementById('contentArea');
  ca.innerHTML = `<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try {
    const [items,preds] = await Promise.all([api('/api/inventory'),api('/api/inventory/predict')]);
    const low=items.filter(i=>i.low_stock);
    ca.innerHTML = `
      <div class="card">
        <div class="card-header"><div class="card-title"><i class="fas fa-boxes-stacked"></i>Inventory (${items.length})</div>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" onclick="openImportModal('inventory')"><i class="fas fa-file-import"></i>Import</button>
            <button class="btn btn-secondary btn-sm" onclick="exportSection('inventory')"><i class="fas fa-file-export"></i>Export</button>
            <button class="btn btn-primary btn-sm" onclick="document.getElementById('itemForm').style.display='block'"><i class="fas fa-plus"></i>Add</button>
          </div>
        </div>
        ${low.length?`<div class="alert-banner warning"><i class="fas fa-exclamation-triangle"></i>${low.length} item(s) low stock: ${low.map(i=>i.name).join(', ')}</div>`:'<div class="alert-banner success"><i class="fas fa-check"></i>All stock levels healthy.</div>'}
        ${preds.length?`<div style="margin-bottom:16px">${preds.slice(0,3).map(p=>`<div class="ai-suggestion ${p.urgency}"><i class="fas fa-robot"></i>${p.item_name}: ${p.days_until_low===0?'Out of stock!':p.days_until_low+' days until low.'} Restock ${p.recommended_restock} units.</div>`).join('')}</div>`:''}
        <div id="itemForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)">
          <div class="form-row">
            <div class="form-group"><label>Item Name *</label><input class="form-control" id="iName" placeholder="e.g. A4 Paper"></div>
            <div class="form-group"><label>Category</label><select class="form-control" id="iCat"><option>Stationery</option><option>Equipment</option><option>General</option><option>Printed Material</option></select></div>
            <div class="form-group"><label>Quantity</label><input class="form-control" id="iQty" type="number" value="0" min="0"></div>
            <div class="form-group"><label>Min Threshold</label><input class="form-control" id="iMin" type="number" value="10" min="0"></div>
            <div class="form-group"><label>Unit</label><input class="form-control" id="iUnit" value="pcs"></div>
          </div>
          <div class="btn-group">
            <button class="btn btn-primary" onclick="saveItem()"><i class="fas fa-save"></i>Save</button>
            <button class="btn btn-secondary" onclick="document.getElementById('itemForm').style.display='none'">Cancel</button>
          </div>
        </div>
        <div class="table-container"><table><thead><tr><th>Item</th><th>Category</th><th>Stock</th><th>Threshold</th><th>Status</th><th>Adjust ±50</th><th>Actions</th></tr></thead>
        <tbody>${items.length?items.map(i=>`<tr><td><strong>${i.name}</strong></td><td><span class="badge badge-info">${i.category}</span></td>
          <td><div style="display:flex;align-items:center;gap:8px"><span style="font-weight:600">${i.quantity}</span><div class="progress-bar" style="width:60px"><div class="progress-fill" style="width:${Math.min(100,i.quantity/Math.max(i.min_threshold*2,1)*100)}%;background:${i.low_stock?'#ef4444':'#10b981'}"></div></div></div></td>
          <td>${i.min_threshold} ${i.unit}</td>
          <td><span class="badge ${i.low_stock?'badge-danger':'badge-success'}">${i.low_stock?'Low':'OK'}</span></td>
          <td><div class="btn-group"><button class="btn btn-secondary btn-sm" onclick="adjustItem(${i.id},-50)">−50</button><button class="btn btn-success btn-sm" onclick="adjustItem(${i.id},50)">+50</button></div></td>
          <td><div class="btn-group"><button class="btn btn-warning btn-sm" onclick="promptRestock(${i.id},'${i.name.replace(/'/g,"\\'")}')"><i class="fas fa-truck"></i></button><button class="btn btn-danger btn-icon btn-sm" onclick="deleteItem(${i.id},'${i.name.replace(/'/g,"\\'")}')"><i class="fas fa-trash"></i></button></div></td>
        </tr>`).join(''):'<tr><td colspan="7"><div class="empty-state"><i class="fas fa-box-open"></i><p>No items. Add or import.</p></div></td></tr>'}</tbody></table></div>
      </div>`;
  } catch(e) { ca.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`; }
}
async function saveItem(){const name=document.getElementById('iName').value.trim();if(!name){toast('Name required','error');return;}try{await api('/api/inventory','POST',{name,category:document.getElementById('iCat').value,quantity:parseInt(document.getElementById('iQty').value)||0,min_threshold:parseInt(document.getElementById('iMin').value)||10,unit:document.getElementById('iUnit').value});toast('Item added!','success');renderInventory();}catch(e){toast(e.message,'error');}}
async function adjustItem(id,amount){try{await api(`/api/inventory/${id}/adjust`,'POST',{amount});toast(`Stock ${amount>0?'added':'reduced'}!`,'success');renderInventory();}catch(e){toast(e.message,'error');}}
async function deleteItem(id,name){showConfirm('Delete Item',`Remove "${name}"?`,async()=>{try{await api(`/api/inventory/${id}`,'DELETE');toast('Deleted','success');renderInventory();}catch(e){toast(e.message,'error');}});}
async function promptRestock(id,name){const q=prompt(`Restock quantity for "${name}":`,100);if(!q||isNaN(q))return;const r=prompt('Reason:','Low stock')||'';try{await api('/api/restocks','POST',{item_id:id,requested_qty:parseInt(q),reason:r});toast('Restock requested!','success');navigateTo('restocks');}catch(e){toast(e.message,'error');}}

// ── Restock Requests ──────────────────────────────────────────
async function renderRestocks(){const ca=document.getElementById('contentArea');ca.innerHTML=`<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;try{const r=await api('/api/restocks');ca.innerHTML=`<div class="card"><div class="card-header"><div class="card-title"><i class="fas fa-truck-loading"></i>Restock Requests (${r.length})</div></div><div class="table-container"><table><thead><tr><th>Item</th><th>Qty</th><th>By</th><th>Reason</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead><tbody>${r.length?r.map(x=>`<tr><td><strong>${x.item_name}</strong></td><td>${x.requested_qty}</td><td>${x.requested_by||'—'}</td><td>${x.reason||'—'}</td><td>${x.date}</td><td><span class="badge ${x.status==='approved'?'badge-success':x.status==='rejected'?'badge-danger':'badge-warning'}">${x.status}</span></td><td>${x.status==='pending'?`<div class="btn-group"><button class="btn btn-success btn-sm" onclick="approveRestock(${x.id})"><i class="fas fa-check"></i>Approve</button><button class="btn btn-danger btn-sm" onclick="rejectRestock(${x.id})"><i class="fas fa-times"></i>Reject</button></div>`:'Done'}</td></tr>`).join(''):'<tr><td colspan="7"><div class="empty-state"><i class="fas fa-truck"></i><p>No requests.</p></div></td></tr>'}</tbody></table></div></div>`;}catch(e){ca.innerHTML=`<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;}}
async function approveRestock(id){try{await api(`/api/restocks/${id}/approve`,'POST');toast('Approved! Inventory updated.','success');renderRestocks();}catch(e){toast(e.message,'error');}}
async function rejectRestock(id){try{await api(`/api/restocks/${id}/reject`,'POST');toast('Rejected','warning');renderRestocks();}catch(e){toast(e.message,'error');}}

// ── Branches ──────────────────────────────────────────────────
async function renderBranches(){const ca=document.getElementById('contentArea');ca.innerHTML=`<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;try{const b=await api('/api/branches');ca.innerHTML=`<div class="card"><div class="card-header"><div class="card-title"><i class="fas fa-sitemap"></i>Branches (${b.length})</div><div class="btn-group"><button class="btn btn-secondary btn-sm" onclick="openImportModal('branches')"><i class="fas fa-file-import"></i>Import</button><button class="btn btn-secondary btn-sm" onclick="exportSection('branches')"><i class="fas fa-file-export"></i>Export</button><button class="btn btn-primary btn-sm" onclick="document.getElementById('branchForm').style.display='block'"><i class="fas fa-plus"></i>Add</button></div></div><div id="branchForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)"><div class="form-row"><div class="form-group"><label>Name *</label><input class="form-control" id="bName" placeholder="e.g. Computer Science"></div><div class="form-group"><label>Code</label><input class="form-control" id="bCode" placeholder="CS"></div><div class="form-group"><label>Students</label><input class="form-control" id="bCount" type="number" value="0"></div><div class="form-group"><label>Color</label><input class="form-control" id="bColor" type="color" value="#4A90D9"></div></div><div class="btn-group"><button class="btn btn-primary" onclick="saveBranch()"><i class="fas fa-save"></i>Save</button><button class="btn btn-secondary" onclick="document.getElementById('branchForm').style.display='none'">Cancel</button></div></div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px">${b.length?b.map(x=>`<div class="card" style="margin:0;padding:18px;border-left:4px solid ${x.color}"><div style="font-weight:600;font-size:15px;margin-bottom:4px">${x.name}</div><span class="badge badge-info">${x.code||'—'}</span><div style="font-size:28px;font-weight:700;color:${x.color};margin:12px 0">${x.student_count}</div><div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">Students</div><button class="btn btn-danger btn-sm" style="width:100%" onclick="deleteBranch(${x.id},'${x.name}')"><i class="fas fa-trash"></i>Delete</button></div>`).join(''):'<div class="empty-state" style="grid-column:1/-1"><i class="fas fa-sitemap"></i><p>No branches yet.</p></div>'}</div></div>`;}catch(e){ca.innerHTML=`<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;}}
async function saveBranch(){const name=document.getElementById('bName').value.trim();if(!name){toast('Name required','error');return;}try{await api('/api/branches','POST',{name,code:document.getElementById('bCode').value,student_count:parseInt(document.getElementById('bCount').value)||0,color:document.getElementById('bColor').value});toast('Branch added!','success');renderBranches();}catch(e){toast(e.message,'error');}}
async function deleteBranch(id,name){showConfirm('Delete Branch',`Remove "${name}"?`,async()=>{try{await api(`/api/branches/${id}`,'DELETE');toast('Deleted','success');renderBranches();}catch(e){toast(e.message,'error');}});}

// ── Staff Duties ──────────────────────────────────────────────
async function renderStaffDuties(){const ca=document.getElementById('contentArea');ca.innerHTML=`<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;try{const d=await api('/api/staff-duties');ca.innerHTML=`<div class="card"><div class="card-header"><div class="card-title"><i class="fas fa-user-tie"></i>Staff Duties (${d.length})</div><div class="btn-group"><button class="btn btn-secondary btn-sm" onclick="openImportModal('staff_duties')"><i class="fas fa-file-import"></i>Import</button><button class="btn btn-secondary btn-sm" onclick="window.location.href='/api/export/attendance/staff'"><i class="fas fa-file-excel"></i>Staff Excel</button><button class="btn btn-secondary btn-sm" onclick="window.location.href='/api/export/attendance/staff/pdf'"><i class="fas fa-file-pdf"></i>Staff PDF</button><button class="btn btn-primary btn-sm" onclick="document.getElementById('sdForm').style.display='block'"><i class="fas fa-plus"></i>Add</button></div></div><div id="sdForm" style="display:none;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:20px;background:rgba(15,23,42,0.4)"><div class="form-row"><div class="form-group"><label>Staff Name *</label><input class="form-control" id="sdName" placeholder="e.g. Rajesh Kumar"></div><div class="form-group"><label>Duty Description</label><input class="form-control" id="sdDesc" placeholder="e.g. Hall Arrangement"></div><div class="form-group"><label>Location</label><input class="form-control" id="sdLoc" placeholder="e.g. Exam Hall A"></div></div><div class="form-row"><div class="form-group"><label>Date</label><input class="form-control" id="sdDate" type="date"></div><div class="form-group"><label>Start Time</label><input class="form-control" id="sdStart" type="time" value="08:00"></div><div class="form-group"><label>End Time</label><input class="form-control" id="sdEnd" type="time" value="17:00"></div></div><div class="btn-group"><button class="btn btn-primary" onclick="saveStaffDuty()"><i class="fas fa-save"></i>Save</button><button class="btn btn-secondary" onclick="document.getElementById('sdForm').style.display='none'">Cancel</button></div></div><div class="table-container"><table><thead><tr><th>Staff Name</th><th>Duty</th><th>Location</th><th>Date</th><th>Time</th><th>Attended</th><th>Check-in</th><th>Actions</th></tr></thead><tbody>${d.length?d.map(x=>`<tr><td><strong>${x.staff_name}</strong></td><td>${x.duty_description||'—'}</td><td>${x.location||'—'}</td><td>${x.date}</td><td>${x.start_time}–${x.end_time}</td><td><span class="badge ${x.attended?'badge-success':'badge-warning'}">${x.attended?'Yes':'No'}</span></td><td>${x.check_in_time||'—'}</td><td><button class="btn btn-danger btn-icon btn-sm" onclick="deleteStaffDuty(${x.id})"><i class="fas fa-trash"></i></button></td></tr>`).join(''):'<tr><td colspan="8"><div class="empty-state"><i class="fas fa-clipboard"></i><p>No staff duties. Add or import.</p></div></td></tr>'}</tbody></table></div></div>`;}catch(e){ca.innerHTML=`<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;}}
async function saveStaffDuty(){const n=document.getElementById('sdName').value.trim();if(!n){toast('Staff name required','error');return;}try{await api('/api/staff-duties','POST',{staff_name:n,duty_description:document.getElementById('sdDesc').value,location:document.getElementById('sdLoc').value,date:document.getElementById('sdDate').value,start_time:document.getElementById('sdStart').value,end_time:document.getElementById('sdEnd').value});toast('Duty added!','success');renderStaffDuties();}catch(e){toast(e.message,'error');}}
async function deleteStaffDuty(id){showConfirm('Delete Duty','Remove this staff duty?',async()=>{try{await api(`/api/staff-duties/${id}`,'DELETE');toast('Deleted','success');renderStaffDuties();}catch(e){toast(e.message,'error');}});}

// ── Emergency Handler ─────────────────────────────────────────
async function renderEmergency(){
  const ca=document.getElementById('contentArea');
  ca.innerHTML=`<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try{
    const [rooms,invs,logs,aiSug]=await Promise.all([api('/api/rooms'),api('/api/invigilators'),api('/api/emergency/logs'),api('/api/ai/suggest','POST',{section:'emergency'})]);
    const availRooms=rooms.filter(r=>r.is_available);
    const availInvs=invs.filter(i=>i.available);
    ca.innerHTML=`
      <div class="stats-grid" style="grid-template-columns:repeat(3,1fr)">
        <div class="stat-card"><div class="stat-icon" style="background:rgba(239,68,68,0.12);color:#ef4444"><i class="fas fa-triangle-exclamation"></i></div><div class="stat-value" style="color:#ef4444">${logs.filter(l=>!l.resolved).length}</div><div class="stat-label">Active Emergencies</div></div>
        <div class="stat-card"><div class="stat-icon" style="background:rgba(16,185,129,0.12);color:#10b981"><i class="fas fa-door-open"></i></div><div class="stat-value" style="color:#10b981">${availRooms.length}</div><div class="stat-label">Backup Rooms</div></div>
        <div class="stat-card"><div class="stat-icon" style="background:rgba(59,130,246,0.12);color:#3b82f6"><i class="fas fa-user-shield"></i></div><div class="stat-value" style="color:#3b82f6">${availInvs.length}</div><div class="stat-label">Reserve Invigilators</div></div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
        <div class="card">
          <div class="card-title" style="margin-bottom:16px"><i class="fas fa-door-closed" style="color:#ef4444"></i>Room Emergency</div>
          <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px">Flag a room as unavailable. AI will auto-reroute affected exams to available rooms with minimum student displacement.</p>
          <div class="form-group"><label>Select Room</label>
            <select class="form-control" id="emergRoomId">
              <option value="">Choose room...</option>
              ${rooms.map(r=>`<option value="${r.id}" ${!r.is_available?'disabled style="color:#ef4444"':''}>${r.name} (${r.capacity} seats) ${!r.is_available?'[UNAVAILABLE]':''}</option>`).join('')}
            </select>
          </div>
          <div class="form-group"><label>Reason</label><input class="form-control" id="emergRoomReason" placeholder="e.g. Power failure, flooding, structural issue"></div>
          <button class="btn btn-danger" onclick="triggerRoomEmergency()"><i class="fas fa-bolt"></i>Trigger Room Emergency</button>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:16px"><i class="fas fa-user-xmark" style="color:#f59e0b"></i>Invigilator Absent</div>
          <p style="color:var(--text-secondary);font-size:13px;margin-bottom:16px">Mark an invigilator as absent. AI instantly finds the least-loaded available replacement.</p>
          <div class="form-group"><label>Select Invigilator</label>
            <select class="form-control" id="emergInvId">
              <option value="">Choose invigilator...</option>
              ${invs.map(i=>`<option value="${i.id}" ${!i.available?'disabled style="color:#ef4444"':''}>${i.name} ${!i.available?'[UNAVAILABLE]':''}</option>`).join('')}
            </select>
          </div>
          <div class="form-group"><label>Reason</label><input class="form-control" id="emergInvReason" placeholder="e.g. Sick leave, emergency, no-show"></div>
          <button class="btn btn-warning" onclick="triggerInvEmergency()"><i class="fas fa-bolt"></i>Handle Invigilator Absence</button>
        </div>
      </div>

      <div class="card">
        <div class="card-title" style="margin-bottom:12px"><i class="fas fa-robot"></i>AI Readiness Status</div>
        ${(aiSug.suggestions||[]).map(s=>`<div class="ai-suggestion ${s.type}"><i class="fas fa-brain"></i>${s.message}</div>`).join('')}
      </div>

      <div id="emergResult" style="display:none;margin-bottom:20px"></div>

      <div class="card">
        <div class="card-title" style="margin-bottom:16px"><i class="fas fa-scroll"></i>Emergency Log</div>
        ${logs.length?`<div class="table-container"><table><thead><tr><th>Type</th><th>From</th><th>To</th><th>Reason</th><th>Students</th><th>Status</th><th>Time</th></tr></thead><tbody>${logs.map(l=>`<tr><td><span class="badge ${l.emergency_type==='room'?'badge-danger':'badge-warning'}">${l.emergency_type}</span></td><td>${l.old_resource}</td><td>${l.new_resource||'—'}</td><td>${l.reason}</td><td>${l.affected_students||0}</td><td><span class="badge ${l.resolved?'badge-success':'badge-danger'}">${l.resolved?'Resolved':'Active'}</span></td><td>${l.timestamp}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty-state"><i class="fas fa-shield-check"></i><p>No emergency events logged.</p></div>'}
      </div>`;
  }catch(e){ca.innerHTML=`<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;}
}

async function triggerRoomEmergency(){
  const id=parseInt(document.getElementById('emergRoomId').value);
  const reason=document.getElementById('emergRoomReason').value;
  if(!id){toast('Select a room','error');return;}
  try{
    const r=await api('/api/emergency/room','POST',{room_id:id,reason:reason||'Room unavailable'});
    const div=document.getElementById('emergResult');
    div.style.display='block';
    div.className=`alert-banner ${r.success?'success':'danger'}`;
    div.innerHTML=`<i class="fas fa-${r.success?'check':'times'}"></i>${r.message || (r.success?'Emergency handled successfully.':'No reassignments possible.')}${r.reassignments&&r.reassignments.length?'<ul style="margin-top:8px;padding-left:20px">'+r.reassignments.map(x=>`<li>${x.subject_name}: ${x.old_room} → ${x.new_room} (${x.student_count} students)</li>`).join('')+'</ul>':''}`;
    toast(r.success?'Room emergency handled!':'Could not fully resolve',r.success?'success':'error');
    renderEmergency();
  }catch(e){toast('Error: '+e.message,'error');}
}

async function triggerInvEmergency(){
  const id=parseInt(document.getElementById('emergInvId').value);
  const reason=document.getElementById('emergInvReason').value;
  if(!id){toast('Select an invigilator','error');return;}
  try{
    const r=await api('/api/emergency/invigilator','POST',{invigilator_id:id,reason:reason||'Absent'});
    const div=document.getElementById('emergResult');
    div.style.display='block';
    div.className=`alert-banner ${r.success?'success':'danger'}`;
    div.innerHTML=`<i class="fas fa-${r.success?'check':'times'}"></i>${r.message}${r.reassignments&&r.reassignments.length?'<ul style="margin-top:8px;padding-left:20px">'+r.reassignments.map(x=>`<li>${x.old_invigilator} → ${x.new_invigilator} for ${x.subject_name||'duty'} in ${x.room_name}</li>`).join('')+'</ul>':''}`;
    toast(r.success?'Reassignment done!':'Could not fully resolve',r.success?'success':'error');
    renderEmergency();
  }catch(e){toast('Error: '+e.message,'error');}
}

// ── Audit Log ─────────────────────────────────────────────────
async function renderAudit(){
  const ca=document.getElementById('contentArea');
  ca.innerHTML=`<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try{
    const logs=await api('/api/audit?limit=100');
    const types=[...new Set(logs.map(l=>l.log_type))];
    ca.innerHTML=`
      <div class="card">
        <div class="card-header">
          <div class="card-title"><i class="fas fa-scroll"></i>Audit Log (${logs.length})</div>
          <div class="btn-group">
            <select class="form-control" id="auditTypeFilter" style="width:160px" onchange="filterAudit(this.value)">
              <option value="">All Types</option>
              ${types.map(t=>`<option value="${t}">${t}</option>`).join('')}
            </select>
          </div>
        </div>
        <div id="auditList">${renderAuditList(logs)}</div>
      </div>`;
    window._allLogs=logs;
  }catch(e){ca.innerHTML=`<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;}
}

function filterAudit(type){const logs=window._allLogs||[];const filtered=type?logs.filter(l=>l.log_type===type):logs;document.getElementById('auditList').innerHTML=renderAuditList(filtered);}

function renderAuditList(logs){
  if(!logs.length)return'<div class="empty-state"><i class="fas fa-scroll"></i><p>No log entries.</p></div>';
  return logs.map(l=>`
    <div class="activity-item">
      <div class="activity-icon ${l.log_type}"><i class="fas fa-${iconForType(l.log_type)}"></i></div>
      <div class="activity-text">
        <strong>${l.action}</strong> <span style="color:var(--text-muted);font-size:12px">by ${l.user}</span>
        ${l.details?`<br><span style="font-size:12px;color:var(--text-muted)">${l.details}</span>`:''}
        <div class="activity-time"><i class="far fa-clock"></i> ${l.timestamp}</div>
      </div>
      <span class="badge badge-${l.log_type==='delete'?'danger':l.log_type==='create'?'success':l.log_type==='ai'?'purple':'info'}">${l.log_type}</span>
    </div>`).join('');
}

// ── Settings ──────────────────────────────────────────────────
async function renderSettings(){
  const ca=document.getElementById('contentArea');
  ca.innerHTML=`<div style="text-align:center;padding:60px"><i class="fas fa-spinner fa-spin" style="font-size:32px;color:#3b82f6"></i></div>`;
  try{
    const s=await api('/api/settings');
    ca.innerHTML=`
      <div class="card">
        <div class="card-header"><div class="card-title"><i class="fas fa-gear"></i>College Settings</div></div>
        <div style="max-width:700px">
          <div style="font-size:14px;font-weight:600;color:var(--accent);margin-bottom:16px;text-transform:uppercase;letter-spacing:0.5px">College Profile</div>
          <div class="form-row">
            <div class="form-group"><label>College Name</label><input class="form-control" id="sCollegeName" value="${s.college_name||''}"></div>
            <div class="form-group"><label>College Code</label><input class="form-control" id="sCollegeCode" value="${s.college_code||''}"></div>
          </div>
          <div class="form-group"><label>Address</label><input class="form-control" id="sAddress" value="${s.address||''}"></div>
          <div class="form-row">
            <div class="form-group"><label>Phone</label><input class="form-control" id="sPhone" value="${s.phone||''}"></div>
            <div class="form-group"><label>Email</label><input class="form-control" id="sEmail" value="${s.email||''}"></div>
          </div>
          <div style="font-size:14px;font-weight:600;color:var(--accent);margin:24px 0 16px;text-transform:uppercase;letter-spacing:0.5px">Exam Schedule Defaults</div>
          <div class="form-row">
            <div class="form-group"><label>Morning Start</label><input class="form-control" id="sMornStart" type="time" value="${s.morning_start||'09:00'}"></div>
            <div class="form-group"><label>Morning End</label><input class="form-control" id="sMornEnd" type="time" value="${s.morning_end||'12:00'}"></div>
            <div class="form-group"><label>Afternoon Start</label><input class="form-control" id="sAftnStart" type="time" value="${s.afternoon_start||'14:00'}"></div>
            <div class="form-group"><label>Afternoon End</label><input class="form-control" id="sAftnEnd" type="time" value="${s.afternoon_end||'17:00'}"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Sessions per Day</label><select class="form-control" id="sSessions"><option value="1" ${s.sessions_per_day==='1'?'selected':''}>1</option><option value="2" ${s.sessions_per_day!=='1'?'selected':''}>2</option></select></div>
          </div>
          <button class="btn btn-primary" onclick="saveSettings()"><i class="fas fa-save"></i>Save Settings</button>
        </div>
      </div>`;
  }catch(e){ca.innerHTML=`<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>${e.message}</p></div>`;}
}

async function saveSettings(){
  try{
    await api('/api/settings','POST',{college_name:document.getElementById('sCollegeName').value,college_code:document.getElementById('sCollegeCode').value,address:document.getElementById('sAddress').value,phone:document.getElementById('sPhone').value,email:document.getElementById('sEmail').value,morning_start:document.getElementById('sMornStart').value,morning_end:document.getElementById('sMornEnd').value,afternoon_start:document.getElementById('sAftnStart').value,afternoon_end:document.getElementById('sAftnEnd').value,sessions_per_day:document.getElementById('sSessions').value});
    toast('Settings saved!','success');
  }catch(e){toast(e.message,'error');}
}
