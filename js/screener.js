// ── Full Stock Dataset ────────────────────────────────────────
let allStocks = [];
let filteredStocks = [];
let currentPage = 1;
const perPage = 10;
let currentView = 'table';
let sortCol = 'aiScore';
let sortDir = -1;
let complianceFilter = 'all';

// ── Render Table ──────────────────────────────────────────────
function renderTable() {
  const tbody = document.getElementById('stockTableBody');
  if (!tbody) return;
  const start = (currentPage - 1) * perPage;
  const pageData = filteredStocks.slice(start, start + perPage);

  tbody.innerHTML = pageData.map(s => {
    const scoreClass = s.aiScore >= 80 ? 'high' : s.aiScore >= 65 ? 'mid' : 'low';
    const verdictClass = s.verdict === 'BUY' ? 'buy' : s.verdict === 'HOLD' ? 'hold' : 'avoid';
    const shClass = s.shariah === 'Halal' ? 'halal' : 'doubtful';
    const mcStr = !s.marketcap ? 'N/A' : s.marketcap >= 1000 ? '$' + (s.marketcap/1000).toFixed(1) + 'T' : '$' + s.marketcap + 'B';
    const sparkColor = s.change >= 0 ? '#10b981' : '#ef4444';
    const trendPath = buildSparkPath(s.trend);
    return `
      <tr onclick="location.href='stock.html?sym=${s.symbol}'">
        <td><div class="td-stock">
          <div class="td-avatar" style="background:linear-gradient(135deg,${s.color}55,${s.color})">${s.symbol.slice(0,2)}</div>
          <div><div class="td-symbol">${s.symbol}</div><div class="td-name">${s.name}</div></div>
        </div></td>
        <td class="td-price">$${s.price.toFixed(2)}</td>
        <td class="td-change ${s.change >= 0 ? 'up' : 'down'}">${s.change >= 0 ? '▲' : '▼'} ${Math.abs(s.change).toFixed(2)}%</td>
        <td class="td-spark">
          <svg viewBox="0 0 80 36" preserveAspectRatio="none">
            <path d="${trendPath}" fill="none" stroke="${sparkColor}" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </td>
        <td><div class="ai-score-cell"><span class="ai-score-pill ${scoreClass}">${s.aiScore}%</span></div></td>
        <td><span class="badge badge-${verdictClass}">${s.verdict}</span></td>
        <td><span class="badge badge-${shClass}">${s.shariah === 'Halal' ? '✓' : '⚠'} ${s.shariah}</span></td>
        <td style="font-family:var(--font-mono);color:var(--text-dim)">${mcStr}</td>
        <td><span class="tag">${s.sector}</span></td>
      </tr>`;
  }).join('');

  renderPagination();
  document.getElementById('countNum').textContent = filteredStocks.length;
}

// ── Render Grid ───────────────────────────────────────────────
function renderGrid() {
  const grid = document.getElementById('gridView');
  if (!grid) return;
  const start = (currentPage - 1) * perPage;
  const pageData = filteredStocks.slice(start, start + perPage);

  grid.innerHTML = pageData.map(s => {
    const verdictClass = s.verdict === 'BUY' ? 'buy' : s.verdict === 'HOLD' ? 'hold' : 'avoid';
    const shClass = s.shariah === 'Halal' ? 'halal' : 'doubtful';
    const trendPath = buildSparkPath(s.trend);
    const sparkColor = s.change >= 0 ? '#10b981' : '#ef4444';
    return `
      <div class="stock-card" onclick="location.href='stock.html?sym=${s.symbol}'">
        <div class="sc-header">
          <div class="sc-identity">
            <div class="sc-avatar" style="background:linear-gradient(135deg,${s.color}55,${s.color})">${s.symbol.slice(0,2)}</div>
            <div><div class="sc-symbol">${s.symbol}</div><div class="sc-name">${s.name}</div></div>
          </div>
          <span class="badge badge-${verdictClass}">${s.verdict}</span>
        </div>
        <div class="sc-chart">
          <svg viewBox="0 0 180 50" preserveAspectRatio="none" style="width:100%;height:50px">
            <path d="${buildSparkPath(s.trend, 180, 50)}" fill="none" stroke="${sparkColor}" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="sc-price-row">
          <div class="sc-price">$${s.price.toFixed(2)}</div>
          <div class="sc-change ${s.change >= 0 ? 'price-up' : 'price-down'}">${s.change >= 0 ? '▲' : '▼'} ${Math.abs(s.change).toFixed(2)}%</div>
        </div>
        <div class="sc-footer">
          <span class="badge badge-${shClass}">${s.shariah === 'Halal' ? '✓' : '⚠'} ${s.shariah}</span>
          <span style="font-family:var(--font-mono);font-size:0.75rem;color:var(--text-muted)">AI: ${s.aiScore}%</span>
          <span class="tag">${s.sector}</span>
        </div>
      </div>`;
  }).join('');

  renderPagination();
}

function buildSparkPath(trend, w = 80, h = 36) {
  const min = Math.min(...trend), max = Math.max(...trend);
  const range = max - min || 1;
  const pts = trend.map((v, i) => {
    const x = (i / (trend.length - 1)) * w;
    const y = h - ((v - min) / range) * (h - 4) - 2;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return pts.join(' ');
}

// ── Pagination ────────────────────────────────────────────────
function renderPagination() {
  const pg = document.getElementById('pagination');
  if (!pg) return;
  const total = Math.ceil(filteredStocks.length / perPage);
  let html = `<button class="page-btn" onclick="goPage(${currentPage-1})" ${currentPage===1?'disabled':''}><i class="fa fa-chevron-left"></i></button>`;
  for (let i = 1; i <= Math.min(total, 7); i++) {
    html += `<button class="page-btn ${i===currentPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
  }
  if (total > 7) html += `<span style="color:var(--text-muted);font-size:0.8rem">…</span><button class="page-btn" onclick="goPage(${total})">${total}</button>`;
  html += `<button class="page-btn" onclick="goPage(${currentPage+1})" ${currentPage===total?'disabled':''}><i class="fa fa-chevron-right"></i></button>`;
  pg.innerHTML = html;
}

window.goPage = function(p) {
  const total = Math.ceil(filteredStocks.length / perPage);
  if (p < 1 || p > total) return;
  currentPage = p;
  currentView === 'table' ? renderTable() : renderGrid();
  window.scrollTo({ top: 200, behavior: 'smooth' });
};

// ── Search & Filter ───────────────────────────────────────────
function applyAll() {
  const q = (document.getElementById('searchInput')?.value || '').toLowerCase();
  const sector = document.getElementById('sectorFilter')?.value || '';
  const market = document.getElementById('marketFilter')?.value || '';
  const minScore = parseInt(document.getElementById('scoreRange')?.value || '0');

  filteredStocks = allStocks.filter(s => {
    const matchQ = !q || s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q);
    const matchSector = !sector || s.sector === sector;
    const matchScore = s.aiScore >= minScore;
    const matchCompliance = complianceFilter === 'all' || s.shariah.toLowerCase() === complianceFilter;
    return matchQ && matchSector && matchScore && matchCompliance;
  });

  if (sortCol) {
    filteredStocks.sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      return typeof av === 'string' ? av.localeCompare(bv) * sortDir : (av - bv) * sortDir;
    });
  }

  currentPage = 1;
  currentView === 'table' ? renderTable() : renderGrid();
}

document.getElementById('searchInput')?.addEventListener('input', applyAll);
document.getElementById('sectorFilter')?.addEventListener('change', applyAll);
document.getElementById('marketFilter')?.addEventListener('change', applyAll);
document.getElementById('scoreRange')?.addEventListener('input', applyAll);

window.setCompliance = function(val, el) {
  complianceFilter = val;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  applyAll();
};

window.applyFilters = applyAll;
window.resetFilters = function() {
  document.getElementById('searchInput').value = '';
  document.getElementById('sectorFilter').value = '';
  document.getElementById('scoreRange').value = 60;
  document.getElementById('scoreVal').textContent = '60%';
  complianceFilter = 'all';
  document.querySelectorAll('.filter-btn')[0].click();
  applyAll();
};

// ── Sort ──────────────────────────────────────────────────────
window.sortTable = function(col) {
  if (sortCol === col) sortDir *= -1;
  else { sortCol = col; sortDir = -1; }
  document.querySelectorAll('.stocks-table th').forEach(th => th.classList.remove('sorted'));
  applyAll();
};

window.setSortTab = function(el, mode) {
  document.querySelectorAll('.sort-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  const map = { score:'aiScore', gainers:'change', losers:'change', volume:'marketcap', marketcap:'marketcap' };
  sortCol = map[mode];
  sortDir = mode === 'losers' ? 1 : -1;
  applyAll();
};

// ── View Toggle ───────────────────────────────────────────────
window.setView = function(view, el) {
  currentView = view;
  document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  const tableWrap = document.getElementById('tableView');
  const gridWrap  = document.getElementById('gridView');
  if (view === 'table') {
    tableWrap.classList.remove('hidden');
    gridWrap.classList.add('hidden');
    renderTable();
  } else {
    tableWrap.classList.add('hidden');
    gridWrap.classList.remove('hidden');
    renderGrid();
  }
};

// ── Init ──────────────────────────────────────────────────────
function showScreenerLoading() {
  const tbody = document.getElementById('stockTableBody');
  const grid = document.getElementById('gridView');
  const loaderHtml = `
    <tr>
      <td colspan="9" style="text-align:center; padding:3rem 1rem">
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1rem">
          <div class="ai-spinner" style="width:36px; height:36px; border:3px solid rgba(14, 165, 233, 0.15); border-top-color:var(--primary); border-radius:50%; animation:spin 1s linear infinite"></div>
          <div style="font-size:0.875rem; color:var(--text-muted)">Loading stocks database...</div>
        </div>
      </td>
    </tr>
  `;
  if (tbody) tbody.innerHTML = loaderHtml;
  if (grid) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:4rem 1rem; gap:1rem">
        <div class="ai-spinner" style="width:36px; height:36px; border:3px solid rgba(14, 165, 233, 0.15); border-top-color:var(--primary); border-radius:50%; animation:spin 1s linear infinite"></div>
        <div style="font-size:0.875rem; color:var(--text-muted)">Loading stocks database...</div>
      </div>
    `;
  }
}

function showScreenerError() {
  const tbody = document.getElementById('stockTableBody');
  const grid = document.getElementById('gridView');
  const errorHtml = `
    <tr>
      <td colspan="9" style="text-align:center; padding:3rem 1rem">
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1rem">
          <div style="width:40px; height:40px; border-radius:50%; background:rgba(239, 68, 68, 0.1); display:flex; align-items:center; justify-content:center; color:var(--red); font-size:1.25rem">⚠</div>
          <div>
            <div style="font-weight:700; color:var(--white); font-size:0.9rem">Connection Failed</div>
            <div style="font-size:0.75rem; color:var(--text-muted)">Could not connect to the backend server.</div>
          </div>
          <button class="btn-outline" onclick="initScreener()" style="font-size:0.75rem; padding:0.5rem 1rem">
            <i class="fa fa-sync-alt"></i> Retry Connection
          </button>
        </div>
      </td>
    </tr>
  `;
  if (tbody) tbody.innerHTML = errorHtml;
  if (grid) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:4rem 1rem; gap:1rem; border:1px solid var(--border); border-radius:var(--radius); background:var(--card)">
        <div style="width:40px; height:40px; border-radius:50%; background:rgba(239, 68, 68, 0.1); display:flex; align-items:center; justify-content:center; color:var(--red); font-size:1.25rem">⚠</div>
        <div style="text-align:center">
          <div style="font-weight:700; color:var(--white); font-size:0.9rem">Connection Failed</div>
          <div style="font-size:0.75rem; color:var(--text-muted)">Could not connect to the backend server.</div>
        </div>
        <button class="btn-outline" onclick="initScreener()" style="font-size:0.75rem; padding:0.5rem 1rem">
          <i class="fa fa-sync-alt"></i> Retry Connection
        </button>
      </div>
    `;
  }
}

async function initScreener() {
  showScreenerLoading();
  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/stocks/screener`, {
      headers: window.HalalStocks.getAuthHeaders()
    });
    if (res.ok) {
      const data = await res.json();
      allStocks = data.map(s => ({
        symbol: s.symbol,
        name: s.name,
        price: s.price,
        change: s.change_pct,
        aiScore: s.ai_score,
        verdict: s.verdict,
        shariah: s.shariah_status,
        marketcap: s.market_cap ? (s.market_cap / 1e9) : 0, // Convert to Billions for display in frontend
        color: s.color || "#0ea5e9",
        sector: s.sector,
        trend: [s.price * 0.95, s.price * 0.97, s.price * 0.96, s.price * (1 + (s.change_pct/100))]
      }));
      applyAll();
    } else {
      showScreenerError();
    }
  } catch (err) {
    console.error("Error loading screener data:", err);
    showScreenerError();
  }
}

initScreener();