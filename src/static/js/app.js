/* ============================
   InvoiceTrack Frontend App
   ============================ */

const API = {
  clockIn:           () => post('/api/clock-in'),
  clockOut:          () => post('/api/clock-out'),
  activeSession:     () => get('/api/sessions/active'),
  sessions:          (start, end) => get(`/api/sessions?start=${start}&end=${end}`),
  addExpense:        (body) => post('/api/expenses', body),
  expenses:          (start, end) => get(`/api/expenses?start=${start}&end=${end}`),
  addTopup:          (body) => post('/api/petty-cash/topup', body),
  balance:           () => get('/api/petty-cash/balance'),
  movements:         () => get('/api/petty-cash/movements'),
  generateInvoice:   (start, end, send) => post(`/api/invoice/generate?start=${start}&end=${end}&send=${send}`),
  status:            () => get('/status'),
};

/* ========== HTTP Helpers ========== */

async function get(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

async function post(url, body = null) {
  const opts = {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  };
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

/* ========== Toast System ========== */

const toastContainer = document.getElementById('toast-container');

function showToast(title, message, type = 'info', duration = 4000) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type]}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-msg">${message}</div>` : ''}
    </div>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}

/* ========== Date Utilities ========== */

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' });
}

function formatTime(timeStr) {
  if (!timeStr) return '—';
  return timeStr.substring(0, 5);
}

function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '—';
  const abs = Math.abs(amount);
  const formatted = `$${abs.toFixed(2)}`;
  return amount < 0 ? `−${formatted}` : formatted;
}

function getWeekBounds(offset = 0) {
  const today = new Date();
  const day = today.getDay();
  const monday = new Date(today);
  monday.setDate(today.getDate() - ((day + 6) % 7) + offset * 7);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return {
    start: monday.toISOString().slice(0, 10),
    end: sunday.toISOString().slice(0, 10),
  };
}

function formatWeekLabel(start, end) {
  const s = new Date(start + 'T00:00:00');
  const e = new Date(end + 'T00:00:00');
  const opts = { day: 'numeric', month: 'short' };
  return `${s.toLocaleDateString('en-AU', opts)} – ${e.toLocaleDateString('en-AU', { ...opts, year: 'numeric' })}`;
}

/* ========== Timer State ========== */

let clockInTime = null;
let timerInterval = null;
let sessionWeekOffset = 0;
let expenseWeekOffset = 0;

function startTimer(clockInStr) {
  // clockInStr is e.g. "08:30:00" — combine with today's date
  const today = new Date().toISOString().slice(0, 10);
  clockInTime = new Date(`${today}T${clockInStr}`);
  updateTimerDisplay();
  timerInterval = setInterval(updateTimerDisplay, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
  clockInTime = null;
  document.getElementById('tracker-time').textContent = '00:00:00';
  document.getElementById('tracker-time').classList.remove('running');
}

function updateTimerDisplay() {
  if (!clockInTime) return;
  const now = new Date();
  const diff = Math.floor((now - clockInTime) / 1000);
  const h = String(Math.floor(diff / 3600)).padStart(2, '0');
  const m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
  const s = String(diff % 60).padStart(2, '0');
  const el = document.getElementById('tracker-time');
  el.textContent = `${h}:${m}:${s}`;
  el.classList.add('running');
}

/* ========== Status Badge ========== */

function setStatusBadge(clockedIn, timeStr = '') {
  const badge = document.getElementById('status-badge');
  const text = document.getElementById('status-text');
  if (clockedIn) {
    badge.className = 'status-badge clocked-in';
    text.textContent = `Clocked in ${timeStr ? 'at ' + timeStr : ''}`;
  } else {
    badge.className = 'status-badge';
    text.textContent = 'Not working';
  }
}

/* ========== Clock In / Out ========== */

async function initTrackerStatus() {
  try {
    const data = await API.activeSession();
    if (data.active) {
      const timeStr = formatTime(data.session.clock_in);
      setStatusBadge(true, timeStr);
      document.getElementById('btn-clock-in').disabled = true;
      document.getElementById('btn-clock-out').disabled = false;
      document.getElementById('tracker-sub').textContent = `Started at ${timeStr}`;
      startTimer(data.session.clock_in);
    } else {
      setStatusBadge(false);
      document.getElementById('btn-clock-in').disabled = false;
      document.getElementById('btn-clock-out').disabled = true;
      document.getElementById('tracker-sub').textContent = 'No active session';
    }
  } catch (e) {
    showToast('Connection error', e.message, 'error');
  }
}

async function clockIn() {
  const btn = document.getElementById('btn-clock-in');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Clocking in…';
  try {
    const data = await API.clockIn();
    const timeStr = formatTime(data.session.clock_in);
    setStatusBadge(true, timeStr);
    document.getElementById('btn-clock-out').disabled = false;
    document.getElementById('tracker-sub').textContent = `Started at ${timeStr}`;
    startTimer(data.session.clock_in);
    showToast('Clocked in', `Session started at ${timeStr}`, 'success');
    loadSessions();
  } catch (e) {
    showToast('Clock in failed', e.message, 'error');
    btn.disabled = false;
  } finally {
    btn.innerHTML = '▶ Clock In';
  }
}

async function clockOut() {
  const btn = document.getElementById('btn-clock-out');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Clocking out…';
  try {
    const data = await API.clockOut();
    const s = data.session;
    setStatusBadge(false);
    document.getElementById('btn-clock-in').disabled = false;
    document.getElementById('tracker-sub').textContent = `Last session: ${formatTime(s.clock_in)} – ${formatTime(s.clock_out)} (${s.adjusted_hours}h billed)`;
    stopTimer();
    showToast('Clocked out', `${s.adjusted_hours}h billed — raw: ${parseFloat(s.raw_hours).toFixed(2)}h`, 'success');
    loadSessions();
    loadWeekStats();
  } catch (e) {
    showToast('Clock out failed', e.message, 'error');
    btn.disabled = false;
  } finally {
    btn.innerHTML = '■ Clock Out';
  }
}

/* ========== Sessions Table ========== */

async function loadSessions() {
  const { start, end } = getWeekBounds(sessionWeekOffset);
  document.getElementById('sessions-week-label').textContent = formatWeekLabel(start, end);

  const tbody = document.getElementById('sessions-tbody');
  const tfoot = document.getElementById('sessions-tfoot');
  tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:20px">Loading…</td></tr>';

  try {
    const data = await API.sessions(start, end);
    if (data.sessions.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="5">
          <div class="empty-state">
            <span class="empty-icon">📅</span>
            <p>No sessions for this week</p>
          </div>
        </td></tr>`;
      tfoot.innerHTML = '';
      return;
    }

    let totalHours = 0;
    tbody.innerHTML = data.sessions.map(s => {
      const hours = s.adjusted_hours ?? '—';
      if (s.adjusted_hours) totalHours += s.adjusted_hours;
      const active = !s.clock_out;
      return `
        <tr>
          <td>${formatDate(s.date)}</td>
          <td class="td-mono">${formatTime(s.clock_in)}</td>
          <td class="td-mono">${active ? '<span style="color:var(--success)">● Active</span>' : formatTime(s.clock_out)}</td>
          <td class="td-mono text-right">${s.raw_hours ? parseFloat(s.raw_hours).toFixed(2) : '—'}</td>
          <td class="td-bold td-accent text-right">${typeof hours === 'number' ? hours.toFixed(2) : hours}</td>
        </tr>`;
    }).join('');

    tfoot.innerHTML = `
      <tr class="tfoot">
        <td colspan="4" class="text-right">Total Billed Hours</td>
        <td class="td-accent text-right">${totalHours.toFixed(2)} h</td>
      </tr>`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="color:var(--danger);padding:20px">${e.message}</td></tr>`;
  }
}

/* ========== Week Stats ========== */

async function loadWeekStats() {
  const { start, end } = getWeekBounds(0);
  try {
    const [sessions, expData] = await Promise.all([
      API.sessions(start, end),
      API.expenses(start, end),
    ]);

    const totalHours = sessions.sessions.reduce((a, s) => a + (s.adjusted_hours || 0), 0);
    const rate = 35; // will be overridden by status
    const totalAmt = (totalHours * rate).toFixed(2);
    const expTotal = expData.expenses.reduce((a, e) => a + e.amount, 0);

    document.getElementById('stat-hours').textContent = totalHours.toFixed(2) + 'h';
    document.getElementById('stat-sessions').textContent = sessions.sessions.length;
    document.getElementById('stat-expenses').textContent = formatCurrency(expTotal);

    // update rate from status
    try {
      const st = await API.status();
      const rateNum = parseFloat(st.rate.replace(/[^0-9.]/g, ''));
      if (!isNaN(rateNum)) {
        const newAmt = (totalHours * rateNum).toFixed(2);
        document.getElementById('stat-amount').textContent = '$' + newAmt;
      }
    } catch (_) {
      document.getElementById('stat-amount').textContent = '$' + totalAmt;
    }
  } catch (e) {
    console.error('Stats load error:', e);
  }
}

/* ========== Expenses ========== */

async function loadExpenses() {
  const { start, end } = getWeekBounds(expenseWeekOffset);
  document.getElementById('expenses-week-label').textContent = formatWeekLabel(start, end);

  const tbody = document.getElementById('expenses-tbody');
  tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding:20px">Loading…</td></tr>';

  try {
    const data = await API.expenses(start, end);
    if (data.expenses.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="4">
          <div class="empty-state">
            <span class="empty-icon">🧾</span>
            <p>No expenses for this week</p>
          </div>
        </td></tr>`;
      return;
    }

    let total = 0;
    tbody.innerHTML = data.expenses.map(e => {
      total += e.amount;
      const paidClass = e.paid_by === 'petty_cash' ? 'td-warning' : 'td-accent';
      const paidLabel = e.paid_by === 'petty_cash' ? 'Petty Cash' : 'Personal';
      return `
        <tr>
          <td>${formatDate(e.date)}</td>
          <td>${e.description}</td>
          <td class="${paidClass}">${paidLabel}</td>
          <td class="td-bold text-right">${formatCurrency(e.amount)}</td>
        </tr>`;
    }).join('');

    const tfoot = document.getElementById('expenses-tfoot');
    tfoot.innerHTML = `
      <tr class="tfoot">
        <td colspan="3" class="text-right">Total</td>
        <td class="text-right">${formatCurrency(total)}</td>
      </tr>`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="color:var(--danger);padding:20px">${e.message}</td></tr>`;
  }
}

async function addExpense(e) {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector('button[type=submit]');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  const description = form.expense_desc.value.trim();
  const amount = parseFloat(form.expense_amount.value);
  const paid_by = form.expense_paid_by.value;
  const date = form.expense_date.value || undefined;

  try {
    await API.addExpense({ description, amount, paid_by, date: date || null });
    showToast('Expense added', `${description} — ${formatCurrency(amount)}`, 'success');
    form.expense_desc.value = '';
    form.expense_amount.value = '';
    form.expense_date.value = '';
    loadExpenses();
    loadWeekStats();
  } catch (err) {
    showToast('Failed to add expense', err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Add Expense';
  }
}

/* ========== Petty Cash ========== */

async function loadPettyCash() {
  try {
    const [balanceData, movementsData] = await Promise.all([
      API.balance(),
      API.movements(),
    ]);

    document.getElementById('petty-balance').textContent = formatCurrency(balanceData.balance);

    const tbody = document.getElementById('movements-tbody');
    if (movementsData.movements.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="4">
          <div class="empty-state">
            <span class="empty-icon">💰</span>
            <p>No movements yet</p>
          </div>
        </td></tr>`;
      return;
    }

    tbody.innerHTML = movementsData.movements.slice().reverse().map(m => {
      const typeClass = m.type === 'topup' ? 'td-success' : 'td-danger';
      const typeLabel = m.type === 'topup' ? '↑ Top-up' : '↓ Expense';
      return `
        <tr>
          <td>${formatDate(m.date)}</td>
          <td class="${typeClass}">${typeLabel}</td>
          <td class="td-bold text-right">${formatCurrency(m.amount)}</td>
          <td class="text-right td-mono">${formatCurrency(m.balance_after)}</td>
        </tr>`;
    }).join('');
  } catch (e) {
    showToast('Petty cash load error', e.message, 'error');
  }
}

async function addTopup(e) {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector('button[type=submit]');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  const amount = parseFloat(form.topup_amount.value);
  const description = form.topup_desc.value.trim() || 'Top-up';

  try {
    const data = await API.addTopup({ amount, description });
    showToast('Petty cash topped up', `New balance: ${formatCurrency(data.balance)}`, 'success');
    form.topup_amount.value = '';
    form.topup_desc.value = '';
    loadPettyCash();
  } catch (err) {
    showToast('Top-up failed', err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Top Up';
  }
}

/* ========== Invoice Generation ========== */

async function generateInvoice(e) {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById('btn-generate-invoice');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating…';

  const start = form.invoice_start.value;
  const end = form.invoice_end.value;
  const sendTelegram = form.send_telegram.checked;

  try {
    const data = await API.generateInvoice(start, end, sendTelegram);
    renderInvoiceResult(data);
    showToast('Invoice generated', `#${String(data.invoice.invoice_number).padStart(3, '0')} — $${data.final_total.toFixed(2)} AUD`, 'success');
    if (sendTelegram) showToast('Sent via Telegram', 'PDFs delivered to your chat', 'info');
  } catch (err) {
    showToast('Invoice generation failed', err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '⚡ Generate Invoice';
  }
}

function renderInvoiceResult(data) {
  const inv = data.invoice;
  const invNum = String(inv.invoice_number).padStart(3, '0');

  const linesHtml = data.lines.map(l => `
    <div class="invoice-line ${l.amount < 0 ? 'credit' : ''}">
      <span>${l.description}</span>
      <span class="amount">${formatCurrency(l.amount)}</span>
    </div>`).join('');

  const container = document.getElementById('invoice-result');
  container.innerHTML = `
    <div class="invoice-result">
      <div class="invoice-result-header">
        <span class="invoice-number">Invoice #${invNum}</span>
        <span style="color:var(--text-secondary);font-size:13px">
          ${formatDate(inv.date_from)} – ${formatDate(inv.date_to)} &nbsp;·&nbsp; ${inv.total_hours}h @ $${inv.rate}/h
        </span>
      </div>
      <div class="invoice-lines">
        ${linesHtml}
        <div class="invoice-line total">
          <span>Total (AUD)</span>
          <span class="amount">${formatCurrency(data.final_total)}</span>
        </div>
      </div>
    </div>`;
  container.classList.remove('hidden');
}

/* ========== Week Navigation ========== */

function setDefaultInvoiceDates() {
  const { start, end } = getWeekBounds(0);
  const s = document.getElementById('invoice-start');
  const e = document.getElementById('invoice-end');
  if (s && !s.value) s.value = start;
  if (e && !e.value) e.value = end;
}

function prevSessionWeek() {
  sessionWeekOffset--;
  loadSessions();
}
function nextSessionWeek() {
  sessionWeekOffset++;
  loadSessions();
}
function prevExpenseWeek() {
  expenseWeekOffset--;
  loadExpenses();
}
function nextExpenseWeek() {
  expenseWeekOffset++;
  loadExpenses();
}

/* ========== Bootstrap ========== */

document.addEventListener('DOMContentLoaded', () => {
  // Clock in/out buttons
  document.getElementById('btn-clock-in').addEventListener('click', clockIn);
  document.getElementById('btn-clock-out').addEventListener('click', clockOut);

  // Expense form
  document.getElementById('expense-form').addEventListener('submit', addExpense);

  // Topup form
  document.getElementById('topup-form').addEventListener('submit', addTopup);

  // Invoice form
  document.getElementById('invoice-form').addEventListener('submit', generateInvoice);

  // Set invoice date defaults
  setDefaultInvoiceDates();

  // Initial data load
  initTrackerStatus();
  loadSessions();
  loadWeekStats();
  loadExpenses();
  loadPettyCash();
});
