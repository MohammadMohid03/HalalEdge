// ── Ticker Data ───────────────────────────────────────────────
const tickerStocks = [
  { symbol: 'AAPL', price: '189.45', change: '+2.34%', up: true },
  { symbol: 'MSFT', price: '378.92', change: '+1.87%', up: true },
  { symbol: 'GOOGL', price: '141.23', change: '-0.45%', up: false },
  { symbol: 'AMZN', price: '185.67', change: '+3.12%', up: true },
  { symbol: 'TSLA', price: '248.30', change: '-1.23%', up: false },
  { symbol: 'NVDA', price: '875.40', change: '+4.56%', up: true },
  { symbol: 'META', price: '504.18', change: '+0.98%', up: true },
  { symbol: 'ADBE', price: '563.72', change: '-0.67%', up: false },
  { symbol: 'CRM', price: '275.44', change: '+1.45%', up: true },
  { symbol: 'INTC', price: '43.21', change: '-2.10%', up: false },
  { symbol: 'QCOM', price: '168.90', change: '+2.78%', up: true },
  { symbol: 'TXN', price: '172.35', change: '+0.32%', up: true },
];

function buildTicker() {
  const track = document.getElementById('ticker');
  if (!track) return;
  const doubled = [...tickerStocks, ...tickerStocks];
  track.innerHTML = doubled.map(s => `
    <div class="ticker-item">
      <span class="ticker-symbol">${s.symbol}</span>
      <span class="ticker-price">$${s.price}</span>
      <span class="ticker-change ${s.up ? 'up' : 'down'}">${s.up ? '▲' : '▼'} ${s.change}</span>
      <span class="ticker-sep">|</span>
    </div>
  `).join('');
}
buildTicker();

// ── Stock Cards Data ──────────────────────────────────────────
const stocksData = [
  {
    symbol: 'AAPL', name: 'Apple Inc.', price: '189.45', change: '+2.34', pct: '+2.34%',
    up: true, tag: 'buy', sector: 'Tech', color: '#1d4ed8',
    path: 'M0,40 C20,38 40,30 60,25 C80,20 100,22 120,18 C140,14 160,10 180,8',
    marketcap: '$2.9T', score: 87
  },
  {
    symbol: 'MSFT', name: 'Microsoft Corp.', price: '378.92', change: '+1.87', pct: '+1.87%',
    up: true, tag: 'buy', sector: 'Tech', color: '#0ea5e9',
    path: 'M0,45 C20,42 40,35 60,30 C80,25 100,20 120,15 C140,10 160,8 180,5',
    marketcap: '$2.8T', score: 84
  },
  {
    symbol: 'NVDA', name: 'NVIDIA Corp.', price: '875.40', change: '+4.56', pct: '+4.56%',
    up: true, tag: 'buy', sector: 'Semiconductors', color: '#76c442',
    path: 'M0,50 C20,45 40,38 60,28 C80,18 100,12 120,8 C140,4 160,2 180,1',
    marketcap: '$2.1T', score: 91
  },
  {
    symbol: 'GOOGL', name: 'Alphabet Inc.', price: '141.23', change: '-0.45', pct: '-0.45%',
    up: false, tag: 'hold', sector: 'Tech', color: '#f59e0b',
    path: 'M0,30 C20,32 40,35 60,33 C80,31 100,30 120,32 C140,34 160,33 180,35',
    marketcap: '$1.8T', score: 73
  },
  {
    symbol: 'AMZN', name: 'Amazon.com Inc.', price: '185.67', change: '+3.12', pct: '+3.12%',
    up: true, tag: 'buy', sector: 'E-Commerce', color: '#f97316',
    path: 'M0,48 C20,44 40,36 60,29 C80,22 100,16 120,11 C140,6 160,4 180,3',
    marketcap: '$1.9T', score: 82
  },
  {
    symbol: 'CRM', name: 'Salesforce Inc.', price: '275.44', change: '+1.45', pct: '+1.45%',
    up: true, tag: 'hold', sector: 'SaaS', color: '#06b6d4',
    path: 'M0,42 C20,40 40,38 60,36 C80,32 100,28 120,24 C140,20 160,18 180,16',
    marketcap: '$267B', score: 76
  },
];

function makeMiniPath(pathD, up) {
  const color = up ? '#10b981' : '#ef4444';
  return `<svg viewBox="0 0 180 55" preserveAspectRatio="none">
    <defs>
      <linearGradient id="g${Math.random().toString(36).slice(2)}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color}" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path d="${pathD}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round"/>
  </svg>`;
}

function renderStockCards(filter) {
  const grid = document.getElementById('stockGrid');
  if (!grid) return;
  const filtered = filter === 'all' ? stocksData : stocksData.filter(s => s.tag === filter);
  grid.innerHTML = filtered.map(s => `
    <div class="stock-card" onclick="location.href='stock.html?sym=${s.symbol}'">
      <div class="sc-header">
        <div class="sc-identity">
          <div class="sc-avatar" style="background:linear-gradient(135deg,${s.color}55,${s.color})">
            ${s.symbol.slice(0,2)}
          </div>
          <div>
            <div class="sc-symbol">${s.symbol}</div>
            <div class="sc-name">${s.name}</div>
          </div>
        </div>
        <span class="badge badge-${s.tag === 'buy' ? 'buy' : 'hold'}">${s.tag.toUpperCase()}</span>
      </div>
      <div class="sc-chart">${makeMiniPath(s.path, s.up)}</div>
      <div class="sc-price-row">
        <div class="sc-price">$${s.price}</div>
        <div class="sc-change ${s.up ? 'price-up' : 'price-down'}">${s.up ? '▲' : '▼'} ${s.pct}</div>
      </div>
      <div class="sc-footer">
        <span class="badge badge-halal">✓ Halal</span>
        <span style="font-family:var(--font-mono);font-size:0.75rem;color:var(--text-muted)">AI: ${s.score}%</span>
        <span class="tag">${s.sector}</span>
      </div>
    </div>
  `).join('');
}

window.filterPicks = function(tab, el) {
  document.querySelectorAll('.picks-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  renderStockCards(tab);
};

function skeletonStockCard() {
  return `
    <div class="stock-card skeleton-card">
      <div class="sc-header">
        <div class="sc-identity">
          ${window.HalalStocks.skeleton.avatar()}
          <div style="display:flex;flex-direction:column;gap:6px">
            ${window.HalalStocks.skeleton.text('50px')}
            ${window.HalalStocks.skeleton.text('90px')}
          </div>
        </div>
        ${window.HalalStocks.skeleton.badge()}
      </div>
      <div class="sc-chart" style="display:flex;align-items:center;justify-content:center">
        ${window.HalalStocks.skeleton.text('80%')}
      </div>
      <div class="sc-price-row">
        ${window.HalalStocks.skeleton.value('70px')}
        ${window.HalalStocks.skeleton.text('55px')}
      </div>
      <div class="sc-footer">
        ${window.HalalStocks.skeleton.badge()}
        ${window.HalalStocks.skeleton.text('45px')}
        ${window.HalalStocks.skeleton.tag()}
      </div>
    </div>`;
}

const stockGrid = document.getElementById('stockGrid');
if (stockGrid) stockGrid.innerHTML = Array.from({ length: 6 }, skeletonStockCard).join('');

setTimeout(() => renderStockCards('buy'), 350);

// ── Animate score bars on scroll ─────────────────────────────
const barObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.score-fill[data-width]').forEach(bar => {
        setTimeout(() => { bar.style.width = bar.dataset.width + '%'; }, 200);
      });
      entry.target.querySelectorAll('.confidence-fill').forEach(bar => {
        setTimeout(() => { bar.style.width = '87%'; }, 1000);
      });
      barObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });

document.querySelectorAll('.ai-visual-card, .hero-card-main').forEach(el => barObserver.observe(el));

// ── Animate compliance ring ───────────────────────────────────
const ringObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const ring = document.getElementById('ringFill');
      if (ring) {
        const score = 96;
        const circumference = 2 * Math.PI * 80;
        const offset = circumference - (score / 100) * circumference;
        setTimeout(() => { ring.style.strokeDashoffset = offset; }, 300);
      }
      ringObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.4 });

document.querySelectorAll('.shariah-visual').forEach(el => ringObserver.observe(el));

// ── Animate hero price ────────────────────────────────────────
setTimeout(() => {
  const conf = document.getElementById('heroConf');
  if (conf) conf.style.width = '87%';
}, 1200);

// ── Live price simulation ─────────────────────────────────────
const heroPrice = document.getElementById('heroPrice');
let basePrice = 189.45;
setInterval(() => {
  basePrice += (Math.random() - 0.48) * 0.5;
  if (heroPrice) heroPrice.textContent = '$' + basePrice.toFixed(2);
}, 2500);