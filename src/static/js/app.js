/* ============================================================
   InvoiceTrack — Frontend Application
   Consumes the FastAPI REST API with no external dependencies.
   ============================================================ */

/* ── API layer ── */
const API = {
  clockIn:         ()            => http('POST', '/api/clock-in'),
  clockOut:        ()            => http('POST', '/api/clock-out'),
  activeSession:   ()            => http('GET',  '/api/sessions/active'),
  sessions:        (s, e)        => http('GET',  `/api/sessions?start=${s}&end=${e}`),
  addExpense:      (body)        => http('POST', '/api/expenses', body),
  expenses:        (s, e)        => http('GET',  `/api/expenses?start=${s}&end=${e}`),
  topup:           (body)        => http('POST', '/api/petty-cash/topup', body),
  balance:         ()            => http('GET',  '/api/petty-cash/balance'),
  movements:       ()            => http('GET',  '/api/petty-cash/movements'),
  generateInvoice: (s, e, send)  => http('POST', `/api/invoice/generate?start=${s}&end=${e}&send=${send}`),
  status:          ()            => http('GET',  '/status'),
};

async function http(method, url, body = null) {
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Formatting ── */
const fmt = {
  date(str) {
    if (!str) return '—';
    const d = new Date(str + 'T00:00:00');
    return d.toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' });
  },
  time(str) {
    return str ? str.substring(0, 5) : '—';
  },
  money(n) {
    if (n === null || n === undefined) return '—';
    const abs = Math.abs(n);
    const s = `$${abs.toFixed(2)}`;
    return n < 0 ? `−${s}` : s;
  },
  duration(secs) {
    const h = String(Math.floor(secs / 3600)).padStart(2, '0');
    const m = String(Math.floor((secs % 3600) / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    return `${h}:${m}:${s}`;
  },
  weekRange(offset = 0) {
    const today = new Date();
    const mon = new Date(today);
    mon.setDate(today.getDate() - ((today.getDay() + 6) % 7) + offset * 7);
    const sun = new Date(mon);
    sun.setDate(mon.getDate() + 6);
    return {
      start: mon.toISOString().slice(0, 10),
      end:   sun.toISOString().slice(0, 10),
    };
  },
  weekLabel(start, end) {
    const o = { day: 'numeric', month: 'short' };
    const s = new Date(start + 'T00:00:00').toLocaleDateString('en-AU', o);
    const e = new Date(end   + 'T00:00:00').toLocaleDateString('en-AU', { ...o, year: 'numeric' });
    return `${s} – ${e}`;
  },
};

/* ── Toast ── */
const toastStack = document.getElementById('toast-stack');

function toast(title, msg = '', type = 'info', ms = 4200) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type] ?? 'ℹ️'}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
    </div>`;
  toastStack.appendChild(el);
  setTimeout(() => {
    el.classList.add('removing');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, ms);
}

/* ── Timer state ── */
let _clockInTime   = null;
let _timerInterval = null;

function startTimer(clockInStr) {
  const today = new Date().toISOString().slice(0, 10);
  _clockInTime = new Date(`${today}T${clockInStr}`);
  _tickTimer();
  _timerInterval = setInterval(_tickTimer, 1000);
}

function stopTimer() {
  clearInterval(_timerInterval);
  _timerInterval = null;
  _clockInTime   = null;
  const el = document.getElementById('tracker-time');
  el.textContent = '00:00:00';
  el.classList.remove('running');
}

function _tickTimer() {
  if (!_clockInTime) return;
  const secs = Math.floor((Date.now() - _clockInTime) / 1000);
  const el = document.getElementById('tracker-time');
  el.textContent = fmt.duration(secs);
  el.classList.add('running');
}

/* ── Status pill ── */
function setStatus(active, label = '') {
  const pill = document.getElementById('status-pill');
  const text = document.getElementById('status-text');
  pill.classList.toggle('active', active);
  text.textContent = active ? label || 'Working' : 'Not working';

  const badge = document.getElementById('tracker-badge');
  badge.textContent = active ? '● Active' : '● Idle';
  badge.style.color = active ? 'var(--accent)' : '';
}

/* ── Week offset state ── */
let sessionWeekOff = 0;
let expenseWeekOff = 0;

/* ══════════════════════════════════════════════════
   CLOCK IN / OUT
══════════════════════════════════════════════════ */

async function initTrackerStatus() {
  try {
    const data = await API.activeSession();
    if (data.active) {
      const timeStr = fmt.time(data.session.clock_in);
      setStatus(true, `Since ${timeStr}`);
      setClockState(true, timeStr);
      startTimer(data.session.clock_in);
    } else {
      setStatus(false);
    }
  } catch (e) {
    toast('Connection failed', e.message, 'error');
  }
}

function setClockState(clocked, timeStr = '') {
  const btnIn  = document.getElementById('btn-clock-in');
  const btnOut = document.getElementById('btn-clock-out');
  const meta   = document.getElementById('tracker-meta');
  btnIn.disabled  = clocked;
  btnOut.disabled = !clocked;
  meta.textContent = clocked
    ? `Session started at ${timeStr} — click Clock Out when done`
    : 'No active session — clock in to start tracking';
}

async function clockIn() {
  const btn = document.getElementById('btn-clock-in');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>&thinsp;Clocking in…';
  try {
    const data = await API.clockIn();
    const t = fmt.time(data.session.clock_in);
    setStatus(true, `Since ${t}`);
    setClockState(true, t);
    startTimer(data.session.clock_in);
    toast('Clocked in', `Session started at ${t}`, 'success');
    loadSessions();
  } catch (e) {
    toast('Clock in failed', e.message, 'error');
    btn.disabled = false;
  } finally {
    btn.innerHTML = '▶&thinsp; Clock In';
  }
}

async function clockOut() {
  const btn = document.getElementById('btn-clock-out');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>&thinsp;Clocking out…';
  try {
    const data = await API.clockOut();
    const s = data.session;
    setStatus(false);
    setClockState(false);
    stopTimer();
    document.getElementById('tracker-meta').textContent =
      `Last session: ${fmt.time(s.clock_in)} – ${fmt.time(s.clock_out)} · ${s.adjusted_hours}h billed`;
    toast('Clocked out', `${s.adjusted_hours}h billed (raw: ${parseFloat(s.raw_hours).toFixed(2)}h)`, 'success');
    loadSessions();
    loadWeekStats();
  } catch (e) {
    toast('Clock out failed', e.message, 'error');
    btn.disabled = false;
  } finally {
    btn.innerHTML = '■&thinsp; Clock Out';
  }
}

/* ══════════════════════════════════════════════════
   WEEK STATS
══════════════════════════════════════════════════ */

async function loadWeekStats() {
  try {
    const { start, end } = fmt.weekRange(0);
    const [sess, exps, st] = await Promise.all([
      API.sessions(start, end),
      API.expenses(start, end),
      API.status().catch(() => null),
    ]);

    const totalH = sess.sessions.reduce((a, s) => a + (s.adjusted_hours || 0), 0);
    const rate   = st ? parseFloat(st.rate.replace(/[^0-9.]/g, '')) || 35 : 35;
    const expTot = exps.expenses.reduce((a, e) => a + e.amount, 0);

    document.getElementById('stat-hours').textContent    = totalH.toFixed(2) + 'h';
    document.getElementById('stat-sessions').textContent = sess.sessions.length;
    document.getElementById('stat-expenses').textContent = fmt.money(expTot);
    document.getElementById('stat-amount').textContent   = '$' + (totalH * rate).toFixed(2);
  } catch (e) {
    console.warn('Stats load error:', e.message);
  }
}

/* ══════════════════════════════════════════════════
   SESSIONS TABLE
══════════════════════════════════════════════════ */

async function loadSessions() {
  const { start, end } = fmt.weekRange(sessionWeekOff);
  document.getElementById('sessions-week-label').textContent = fmt.weekLabel(start, end);

  const tbody = document.getElementById('sessions-tbody');
  const tfoot = document.getElementById('sessions-tfoot');
  tbody.innerHTML = emptyRow(5, '⏳', 'Loading sessions…');
  tfoot.innerHTML = '';

  try {
    const data = await API.sessions(start, end);
    if (!data.sessions.length) {
      tbody.innerHTML = emptyRow(5, '📅', 'No sessions this week');
      return;
    }

    let totalH = 0;
    tbody.innerHTML = data.sessions.map(s => {
      const active  = !s.clock_out;
      const adjH    = s.adjusted_hours;
      if (adjH) totalH += adjH;
      return `
        <tr>
          <td class="td-bold">${fmt.date(s.date)}</td>
          <td class="td-mono">${fmt.time(s.clock_in)}</td>
          <td>
            ${active
              ? '<span class="tag tag-success">● Active</span>'
              : `<span class="td-mono">${fmt.time(s.clock_out)}</span>`}
          </td>
          <td class="td-mono td-right">${s.raw_hours ? parseFloat(s.raw_hours).toFixed(2) : '—'}</td>
          <td class="td-accent td-bold td-right">${adjH != null ? adjH.toFixed(2) : '—'}</td>
        </tr>`;
    }).join('');

    tfoot.innerHTML = `
      <tr>
        <td colspan="4" class="txt-right" style="font-size:12px;font-weight:600;color:var(--text-muted)">
          TOTAL BILLED
        </td>
        <td class="td-right td-accent">${totalH.toFixed(2)} h</td>
      </tr>`;
  } catch (e) {
    tbody.innerHTML = errorRow(5, e.message);
  }
}

function prevSessionWeek() { sessionWeekOff--; loadSessions(); }
function nextSessionWeek() { sessionWeekOff++; loadSessions(); }

/* ══════════════════════════════════════════════════
   EXPENSES
══════════════════════════════════════════════════ */

async function loadExpenses() {
  const { start, end } = fmt.weekRange(expenseWeekOff);
  document.getElementById('expenses-week-label').textContent = fmt.weekLabel(start, end);

  const tbody = document.getElementById('expenses-tbody');
  const tfoot = document.getElementById('expenses-tfoot');
  tbody.innerHTML = emptyRow(4, '⏳', 'Loading…');
  tfoot.innerHTML = '';

  try {
    const data = await API.expenses(start, end);
    if (!data.expenses.length) {
      tbody.innerHTML = emptyRow(4, '🧾', 'No expenses this week');
      return;
    }

    let total = 0;
    tbody.innerHTML = data.expenses.map(e => {
      total += e.amount;
      const personal = e.paid_by !== 'petty_cash';
      return `
        <tr>
          <td class="td-bold">${fmt.date(e.date)}</td>
          <td>${e.description}</td>
          <td>
            <span class="tag ${personal ? 'tag-info' : 'tag-warning'}">
              ${personal ? 'Personal' : 'Petty Cash'}
            </span>
          </td>
          <td class="td-right td-bold">${fmt.money(e.amount)}</td>
        </tr>`;
    }).join('');

    tfoot.innerHTML = `
      <tr>
        <td colspan="3" class="txt-right" style="font-size:12px;font-weight:600;color:var(--text-muted)">TOTAL</td>
        <td class="td-right">${fmt.money(total)}</td>
      </tr>`;
  } catch (e) {
    tbody.innerHTML = errorRow(4, e.message);
  }
}

async function handleAddExpense(ev) {
  ev.preventDefault();
  const btn = document.getElementById('btn-add-expense');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>';

  const desc   = document.getElementById('exp-desc').value.trim();
  const amount = parseFloat(document.getElementById('exp-amount').value);
  const paidBy = document.getElementById('exp-paid-by').value;
  const date   = document.getElementById('exp-date').value || null;

  try {
    await API.addExpense({ description: desc, amount, paid_by: paidBy, date });
    toast('Expense added', `${desc} — ${fmt.money(amount)}`, 'success');
    document.getElementById('exp-desc').value   = '';
    document.getElementById('exp-amount').value = '';
    document.getElementById('exp-date').value   = '';
    loadExpenses();
    loadWeekStats();
    loadPettyCash();
  } catch (e) {
    toast('Add expense failed', e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '+ Add Expense';
  }
}

function prevExpenseWeek() { expenseWeekOff--; loadExpenses(); }
function nextExpenseWeek() { expenseWeekOff++; loadExpenses(); }

/* ══════════════════════════════════════════════════
   PETTY CASH
══════════════════════════════════════════════════ */

async function loadPettyCash() {
  try {
    const [bal, mov] = await Promise.all([API.balance(), API.movements()]);
    document.getElementById('petty-balance').textContent = fmt.money(bal.balance);

    const tbody = document.getElementById('movements-tbody');
    if (!mov.movements.length) {
      tbody.innerHTML = emptyRow(4, '💰', 'No movements yet');
      return;
    }

    tbody.innerHTML = [...mov.movements].reverse().map(m => {
      const isTopup = m.type === 'topup';
      return `
        <tr>
          <td class="td-bold">${fmt.date(m.date)}</td>
          <td>
            <span class="tag ${isTopup ? 'tag-success' : 'tag-danger'}">
              ${isTopup ? '↑ Top-up' : '↓ Expense'}
            </span>
          </td>
          <td class="td-right td-bold ${isTopup ? 'td-success' : 'td-danger'}">${fmt.money(m.amount)}</td>
          <td class="td-right td-mono">${fmt.money(m.balance_after)}</td>
        </tr>`;
    }).join('');
  } catch (e) {
    toast('Petty cash error', e.message, 'error');
  }
}

async function handleTopup(ev) {
  ev.preventDefault();
  const btn = document.getElementById('btn-topup');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>';

  const amount = parseFloat(document.getElementById('topup-amount').value);
  const desc   = document.getElementById('topup-desc').value.trim() || 'Top-up';

  try {
    const data = await API.topup({ amount, description: desc });
    toast('Petty cash topped up', `New balance: ${fmt.money(data.balance)}`, 'success');
    document.getElementById('topup-amount').value = '';
    document.getElementById('topup-desc').value   = '';
    loadPettyCash();
  } catch (e) {
    toast('Top-up failed', e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '↑ Top Up';
  }
}

/* ══════════════════════════════════════════════════
   INVOICE GENERATOR
══════════════════════════════════════════════════ */

async function handleGenerateInvoice(ev) {
  ev.preventDefault();
  const btn  = document.getElementById('btn-generate');
  btn.disabled = true;
  btn.innerHTML = '<span class="spin"></span>&thinsp;Generating…';

  const start = document.getElementById('inv-start').value;
  const end   = document.getElementById('inv-end').value;
  const send  = document.getElementById('send-telegram').checked;

  try {
    const data = await API.generateInvoice(start, end, send);
    renderInvoice(data);
    const num = String(data.invoice.invoice_number).padStart(3, '0');
    toast(`Invoice #${num} generated`, `Total: ${fmt.money(data.final_total)} AUD`, 'success');
    if (send) toast('Sent via Telegram', 'PDFs delivered to your chat', 'info');
  } catch (e) {
    toast('Generation failed', e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '⚡&thinsp; Generate';
  }
}

function renderInvoice(data) {
  const inv    = data.invoice;
  const invNum = String(inv.invoice_number).padStart(3, '0');

  const lines = data.lines.map(l => `
    <div class="inv-line ${l.amount < 0 ? 'credit' : ''}">
      <span>${l.description}</span>
      <span class="inv-amount">${fmt.money(l.amount)}</span>
    </div>`).join('');

  const el = document.getElementById('invoice-result');
  el.innerHTML = `
    <div class="invoice-result-wrap">
      <div class="invoice-result-header">
        <span class="inv-number">Invoice #${invNum}</span>
        <span class="inv-period">
          ${fmt.date(inv.date_from)} – ${fmt.date(inv.date_to)}
          &nbsp;·&nbsp; ${inv.total_hours}h @ $${inv.rate}/h
        </span>
      </div>
      ${lines}
      <div class="inv-line total">
        <span>Total Due (AUD)</span>
        <span class="inv-amount">${fmt.money(data.final_total)}</span>
      </div>
    </div>`;
  el.classList.remove('hidden');
}

/* ── Table helpers ── */
function emptyRow(cols, icon, msg) {
  return `<tr><td colspan="${cols}">
    <div class="empty">
      <span class="empty-glyph">${icon}</span>
      <p>${msg}</p>
    </div>
  </td></tr>`;
}

function errorRow(cols, msg) {
  return `<tr><td colspan="${cols}" class="txt-center" style="color:var(--danger);padding:20px">${msg}</td></tr>`;
}

/* ── Set invoice date defaults to current week ── */
function setInvoiceDefaults() {
  const { start, end } = fmt.weekRange(0);
  const s = document.getElementById('inv-start');
  const e = document.getElementById('inv-end');
  if (s && !s.value) s.value = start;
  if (e && !e.value) e.value = end;
}

/* ══════════════════════════════════════════════════
   BOOTSTRAP
══════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  // Clock controls
  document.getElementById('btn-clock-in').addEventListener('click', clockIn);
  document.getElementById('btn-clock-out').addEventListener('click', clockOut);

  // Forms
  document.getElementById('expense-form').addEventListener('submit', handleAddExpense);
  document.getElementById('topup-form').addEventListener('submit', handleTopup);
  document.getElementById('invoice-form').addEventListener('submit', handleGenerateInvoice);

  // Invoice date defaults
  setInvoiceDefaults();

  // Initial data load
  initTrackerStatus();
  loadSessions();
  loadWeekStats();
  loadExpenses();
  loadPettyCash();
});
