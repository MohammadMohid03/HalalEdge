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
    const loading = !s.price || s.price === 0;
    const scoreClass = s.aiScore >= 80 ? 'high' : s.aiScore >= 65 ? 'mid' : 'low';
    const verdictClass = s.verdict === 'BUY' ? 'buy' : s.verdict === 'HOLD' ? 'hold' : 'avoid';
    const shClass = s.shariah === 'Halal' ? 'halal' : 'doubtful';
    const mcStr = loading ? '···' : !s.marketcap ? 'N/A' : s.marketcap >= 1000 ? '$' + (s.marketcap/1000).toFixed(1) + 'T' : '$' + s.marketcap + 'B';
    const sparkColor = s.change >= 0 ? '#10b981' : '#ef4444';
    const trendPath = buildSparkPath(s.trend);
    return `
      <tr onclick="location.href='stock.html?sym=${s.symbol}'">
        <td><div class="td-stock">
          <div class="td-avatar" style="background:linear-gradient(135deg,${s.color}55,${s.color})">${s.symbol.slice(0,2)}</div>
          <div><div class="td-symbol">${s.symbol}</div><div class="td-name">${s.name}</div></div>
        </div></td>
        <td class="td-price">${loading ? '<span class="td-loading">···</span>' : '$' + s.price.toFixed(2)}</td>
        <td class="td-change ${s.change >= 0 ? 'up' : 'down'}">${loading ? '···' : (s.change >= 0 ? '▲' : '▼') + ' ' + Math.abs(s.change).toFixed(2) + '%'}</td>
        <td class="td-spark">
          ${loading ? '<span style="color:var(--text-muted);font-size:0.7rem">···</span>' : `<svg viewBox="0 0 80 36" preserveAspectRatio="none"><path d="${trendPath}" fill="none" stroke="${sparkColor}" stroke-width="1.8" stroke-linecap="round"/></svg>`}
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
    const loading = !s.price || s.price === 0;
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
          ${loading ? '<span style="color:var(--text-muted);font-size:0.7rem;display:flex;align-items:center;justify-content:center;height:50px">···</span>' : `<svg viewBox="0 0 180 50" preserveAspectRatio="none" style="width:100%;height:50px"><path d="${buildSparkPath(s.trend, 180, 50)}" fill="none" stroke="${sparkColor}" stroke-width="2" stroke-linecap="round"/></svg>`}
        </div>
        <div class="sc-price-row">
          <div class="sc-price">${loading ? '···' : '$' + s.price.toFixed(2)}</div>
          <div class="sc-change ${s.change >= 0 ? 'price-up' : 'price-down'}">${loading ? '···' : (s.change >= 0 ? '▲' : '▼') + ' ' + Math.abs(s.change).toFixed(2) + '%'}</div>
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
  enrichVisibleStocks();
  window.scrollTo({ top: 200, behavior: 'smooth' });
};

// ── Phase 2: Progressive live data loading in batches of 50 ──
let progressiveRequestId = 0;
let enrichRequestId = 0;
const BATCH_SIZE = 50;

async function fetchBatchData(symbols) {
  if (symbols.length === 0) return [];
  const symStr = symbols.join(',');
  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/stocks/batch-data?symbols=${encodeURIComponent(symStr)}`, {
      headers: window.HalalStocks.getAuthHeaders()
    });
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error('Error fetching batch data:', err);
    return [];
  }
}

function applyBatchData(data) {
  let changed = false;
  data.forEach(d => {
    if (!d.price) return;
    const stock = allStocks.find(s => s.symbol === d.symbol);
    if (stock && (!stock.price || stock.price === 0)) {
      stock.price = d.price;
      stock.change = d.change_pct || 0;
      stock.marketcap = d.market_cap ? (d.market_cap / 1e9) : 0;
      if (d.ai_score) stock.aiScore = d.ai_score;
      if (d.verdict) stock.verdict = d.verdict;
      stock.trend = [d.price * 0.95, d.price * 0.97, d.price * 0.96, d.price * (1 + ((d.change_pct || 0) / 100))];
      changed = true;
    }
  });
  return changed;
}

async function loadAllStocksProgressively() {
  const reqId = ++progressiveRequestId;
  const allSymbols = allStocks.filter(s => !s.price || s.price === 0).map(s => s.symbol);

  for (let i = 0; i < allSymbols.length; i += BATCH_SIZE) {
    if (reqId !== progressiveRequestId) return;
    const chunk = allSymbols.slice(i, i + BATCH_SIZE);
    const data = await fetchBatchData(chunk);
    if (reqId !== progressiveRequestId) return;
    if (applyBatchData(data)) {
      currentView === 'table' ? renderTable() : renderGrid();
    }
  }
}

async function enrichVisibleStocks() {
  const reqId = ++enrichRequestId;
  const start = (currentPage - 1) * perPage;
  const pageData = filteredStocks.slice(start, start + perPage);
  const needEnrich = pageData.filter(s => !s.price || s.price === 0).map(s => s.symbol);
  if (needEnrich.length === 0) return;

  const data = await fetchBatchData(needEnrich);
  if (reqId !== enrichRequestId) return;
  if (applyBatchData(data)) {
    currentView === 'table' ? renderTable() : renderGrid();
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
        marketcap: s.market_cap ? (s.market_cap / 1e9) : 0,
        color: s.color || "#0ea5e9",
        sector: s.sector,
        trend: [s.price * 0.95, s.price * 0.97, s.price * 0.96, s.price * (1 + (s.change_pct/100))]
      }));
      applyAll();
      loadAllStocksProgressively();
    } else {
      showScreenerError();
    }
  } catch (err) {
    console.error("Error loading screener data:", err);
    showScreenerError();
  }
}

initScreener();