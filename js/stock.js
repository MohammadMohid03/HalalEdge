// ── URL & State Config ─────────────────────────────────────────
const urlParams = new URLSearchParams(window.location.search);
const symbol = (urlParams.get('sym') || 'AAPL').toUpperCase();

let currentPrice = 180.00; // Will be updated dynamically
let companyDetails = {};
let aiPrediction = {};
let shariahDetail = {};
let predictionHistory = [];
let chart = null;

// ── Update timestamp ──────────────────────────────────────────
function updateTimestamp() {
  const lastUpdatedEl = document.getElementById('lastUpdated');
  if (lastUpdatedEl) {
    lastUpdatedEl.textContent = new Date().toLocaleTimeString();
  }
}
updateTimestamp();

// ── Load Stock Data from APIs ─────────────────────────────────
function showPredictionLoading() {
  const body = document.querySelector('.ai-pred-card .ai-pred-body');
  if (body) {
    body.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div style="display:flex;align-items:center;gap:1rem">
          ${window.HalalStocks.skeleton.avatar()}
          <div style="display:flex;flex-direction:column;gap:6px;flex:1">
            ${window.HalalStocks.skeleton.title('80px')}
            ${window.HalalStocks.skeleton.text('140px')}
          </div>
        </div>
        ${window.HalalStocks.skeleton.bar('100%')}
        ${window.HalalStocks.skeleton.bar('90%')}
        ${window.HalalStocks.skeleton.bar('95%')}
        ${window.HalalStocks.skeleton.bar('85%')}
        <div style="display:flex;gap:1rem;margin-top:0.5rem">
          <div style="flex:1;background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.75rem;display:flex;flex-direction:column;gap:6px">
            ${window.HalalStocks.skeleton.text('40px')}
            ${window.HalalStocks.skeleton.value('70px')}
          </div>
          <div style="flex:1;background:var(--bg-2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.75rem;display:flex;flex-direction:column;gap:6px">
            ${window.HalalStocks.skeleton.text('40px')}
            ${window.HalalStocks.skeleton.value('70px')}
          </div>
        </div>
      </div>
    `;
  }
}

function showStockSkeleton() {
  // Header
  const logoEl = document.querySelector('.stock-logo-big');
  if (logoEl) {
    logoEl.textContent = '';
    logoEl.style.background = 'var(--card)';
    logoEl.classList.add('skeleton-avatar');
    logoEl.style.width = '64px';
    logoEl.style.height = '64px';
    logoEl.style.borderRadius = '16px';
  }
  const tickerEl = document.querySelector('.stock-ticker');
  if (tickerEl) {
    tickerEl.innerHTML = window.HalalStocks.skeleton.title('80px');
  }
  const fullEl = document.querySelector('.stock-fullname');
  if (fullEl) {
    fullEl.innerHTML = window.HalalStocks.skeleton.text('140px');
  }
  const tagsEl = document.querySelector('.stock-tags');
  if (tagsEl) {
    tagsEl.innerHTML = `${window.HalalStocks.skeleton.badge()}${window.HalalStocks.skeleton.tag()}${window.HalalStocks.skeleton.tag()}`;
  }
  const priceEl = document.getElementById('stockPriceBig');
  if (priceEl) {
    priceEl.innerHTML = window.HalalStocks.skeleton.value('120px');
  }
  const changeEl = document.getElementById('stockChangeBig');
  if (changeEl) {
    changeEl.innerHTML = window.HalalStocks.skeleton.text('100px');
    changeEl.className = 'stock-change-big';
  }

  // Stats grid
  const statsEl = document.querySelector('.stats-grid-card');
  if (statsEl) {
    statsEl.innerHTML = Array.from({ length: 8 }, () => `
      <div class="stat-cell">
        <div class="stat-cell-label">${window.HalalStocks.skeleton.text('35px')}</div>
        <div class="stat-cell-value">${window.HalalStocks.skeleton.value('60px')}</div>
      </div>
    `).join('');
  }

  // Chart
  const chartBody = document.querySelector('.chart-card .chart-body');
  if (chartBody) {
    chartBody.innerHTML = window.HalalStocks.skeleton.chart('220px');
  }

  // Info tabs
  const infoContent = document.getElementById('infoTabContent');
  if (infoContent) {
    infoContent.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:0.75rem">
        ${window.HalalStocks.skeleton.text('100%')}
        ${window.HalalStocks.skeleton.text('95%')}
        ${window.HalalStocks.skeleton.text('80%')}
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1.25rem">
        ${Array.from({ length: 3 }, () => `
          <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.875rem;text-align:center;display:flex;flex-direction:column;gap:8px;align-items:center">
            ${window.HalalStocks.skeleton.text('50px')}
            ${window.HalalStocks.skeleton.value('70px')}
          </div>
        `).join('')}
      </div>
    `;
  }

  // News
  const newsContainer = document.getElementById('newsItems');
  if (newsContainer) {
    newsContainer.innerHTML = Array.from({ length: 4 }, () => `
      <div class="news-item" style="pointer-events:none">
        ${window.HalalStocks.skeleton.title('70%')}
        <div style="display:flex;gap:0.5rem;margin-top:0.5rem">${window.HalalStocks.skeleton.text('80px')}${window.HalalStocks.skeleton.text('40px')}</div>
      </div>
    `).join('');
  }

  // AI prediction
  showPredictionLoading();

  // Shariah card
  const shariahBody = document.querySelector('.shariah-card-body');
  if (shariahBody) {
    shariahBody.innerHTML = Array.from({ length: 6 }, () => `
      <div class="shariah-row">
        ${window.HalalStocks.skeleton.text('80px')}
        ${window.HalalStocks.skeleton.text('50px')}
      </div>
    `).join('');
  }
}

function showPredictionError(errMsg) {
  const body = document.querySelector('.ai-pred-card .ai-pred-body');
  if (body) {
    body.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:2rem 1rem; text-align:center; gap:1rem">
        <div style="width:48px; height:48px; border-radius:50%; background:rgba(239, 68, 68, 0.1); display:flex; align-items:center; justify-content:center; color:var(--red); font-size:1.5rem">⚠</div>
        <div>
          <div style="font-weight:700; color:var(--white); font-size:0.9rem; margin-bottom:0.25rem">AI Prediction Unavailable</div>
          <div style="font-size:0.75rem; color:var(--text-muted); line-height:1.4">${errMsg || 'An error occurred while generating prediction.'}</div>
        </div>
        <button class="btn-outline" onclick="loadStockDetails()" style="font-size:0.75rem; padding:0.5rem 1rem; margin-top:0.5rem">
          <i class="fa fa-sync-alt"></i> Retry Prediction
        </button>
      </div>
    `;
  }
}

function showStockPageError() {
  const body = document.querySelector('.stock-body');
  if (body) {
    body.innerHTML = `
      <div style="grid-column: 1 / -1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:5rem 2rem; text-align:center; gap:1.5rem; background:var(--card); border:1px solid var(--border); border-radius:var(--radius-lg)">
        <div style="width:64px; height:64px; border-radius:50%; background:rgba(239, 68, 68, 0.1); display:flex; align-items:center; justify-content:center; color:var(--red); font-size:2rem">⚠</div>
        <div>
          <h2 style="font-family:var(--font-display); font-size:1.5rem; font-weight:800; color:var(--white); margin-bottom:0.5rem">Failed to Load Stock Data</h2>
          <p style="color:var(--text-muted); max-width:400px; margin:0 auto; font-size:0.9rem; line-height:1.6">We couldn't connect to the server to fetch live stock data for ${symbol}. Please check your internet connection or verify the backend is running.</p>
        </div>
        <button class="btn-primary" onclick="loadStockDetails()" style="padding:0.75rem 1.5rem; font-size:0.9rem">
          <i class="fa fa-sync-alt"></i> Retry Connection
        </button>
      </div>
    `;
  }
}

async function loadStockDetails() {
  showStockSkeleton();
  try {
    // 1. Fetch core stock details first (required before rendering header/stats)
    const detailsRes = await fetch(`${window.HalalStocks.API_BASE}/stocks/${symbol}`, {
      headers: window.HalalStocks.getAuthHeaders()
    });
    if (!detailsRes.ok) {
      window.HalalStocks?.showToast(`Stock ${symbol} not found.`, 'error');
      setTimeout(() => { window.location.href = 'screener.html'; }, 2000);
      return;
    }
    companyDetails = await detailsRes.json();
    currentPrice = companyDetails.price;

    // Render header/stats/news immediately
    updateHeaderUI();
    updateStatsGridUI();
    updateTabsUI('about');
    updateNewsUI();

    // 2. Fetch prediction, shariah, history, and chart in parallel
    // (prediction is cached on the backend, so this is fast)
    await Promise.all([
      (async () => {
        try {
          const predRes = await fetch(`${window.HalalStocks.API_BASE}/predictions/${symbol}`, {
            headers: window.HalalStocks.getAuthHeaders()
          });
          if (predRes.ok) {
            aiPrediction = await predRes.json();
            updatePredictionUI();
          } else if (predRes.status === 404) {
            showPredictionError('AI prediction is scheduled. The daily pipeline will generate it soon.');
          } else {
            const errorData = await predRes.json().catch(() => ({}));
            showPredictionError(errorData.detail || 'Failed to load prediction.');
          }
        } catch (e) {
          console.error('Error fetching prediction:', e);
          showPredictionError('Network timeout or connection lost.');
        }
      })(),
      (async () => {
        try {
          const shariahRes = await fetch(`${window.HalalStocks.API_BASE}/predictions/${symbol}/shariah`, {
            headers: window.HalalStocks.getAuthHeaders()
          });
          if (shariahRes.ok) {
            shariahDetail = await shariahRes.json();
            updateShariahUI();
          }
        } catch (e) {
          console.error('Error fetching Shariah details:', e);
        }
      })(),
      (async () => {
        try {
          const histRes = await fetch(`${window.HalalStocks.API_BASE}/predictions/${symbol}/history`);
          if (histRes.ok) {
            predictionHistory = await histRes.json();
          }
        } catch (e) {
          console.error('Error fetching prediction history:', e);
        }
      })(),
      drawChart('1D')
    ]);
  } catch (err) {
    console.error('Error fetching stock details:', err);
    showStockPageError();
  }
}


// ── Dynamic UI Updaters ───────────────────────────────────────
function updateHeaderUI() {
  // Breadcrumb
  const bcEl = document.querySelector('.stock-breadcrumb span');
  if (bcEl) bcEl.textContent = symbol;

  // Title page update
  document.title = `${symbol} — ${companyDetails.name} | HalalEdge`;

  // Avatar Logo
  const logoEl = document.querySelector('.stock-logo-big');
  if (logoEl) {
    logoEl.classList.remove('skeleton-avatar');
    logoEl.style.width = '';
    logoEl.style.height = '';
    logoEl.style.borderRadius = '';
    logoEl.textContent = symbol.slice(0, 3);
    logoEl.style.background = `linear-gradient(135deg, ${companyDetails.color}88, ${companyDetails.color})`;
  }

  // Ticker and Name
  const tickerEl = document.querySelector('.stock-ticker');
  if (tickerEl) tickerEl.textContent = symbol;
  
  const fullEl = document.querySelector('.stock-fullname');
  if (fullEl) fullEl.textContent = `${companyDetails.name} · ${symbol.includes('.') ? 'OTC' : 'NASDAQ'}`;

  // Tags badge
  const tagsEl = document.querySelector('.stock-tags');
  if (tagsEl) {
    const isHalal = companyDetails.shariah_status === 'Halal';
    const badgeClass = isHalal ? 'badge-halal' : companyDetails.shariah_status === 'Doubtful' ? 'badge-doubtful' : 'badge-haram';
    const checkSign = isHalal ? '✓' : '⚠';
    tagsEl.innerHTML = `
      <span class="badge ${badgeClass}">${checkSign} ${companyDetails.shariah_status}</span>
      <span class="tag">${companyDetails.sector}</span>
      <span class="tag">${companyDetails.market_cap >= 100e9 ? 'Large Cap' : companyDetails.market_cap ? 'Mid Cap' : 'N/A'}</span>
    `;
  }

  // Price big
  const priceEl = document.getElementById('stockPriceBig');
  if (priceEl) priceEl.textContent = window.HalalStocks.formatPrice(companyDetails.price);

  // Change big
  const changeEl = document.getElementById('stockChangeBig');
  if (changeEl) {
    const isUp = companyDetails.change >= 0;
    const sign = isUp ? '+' : '';
    changeEl.textContent = `${isUp ? '▲' : '▼'} ${sign}${companyDetails.change.toFixed(2)} (${sign}${companyDetails.change_pct.toFixed(2)}%)`;
    changeEl.className = 'stock-change-big ' + (isUp ? 'up' : 'down');
  }
}

function updateStatsGridUI() {
  const gridEl = document.querySelector('.stats-grid-card');
  if (!gridEl) return;

  const fmtCap = companyDetails.market_cap ? window.HalalStocks.formatBigNum(companyDetails.market_cap) : 'N/A';
  const pe = companyDetails.pe_ratio ? `${companyDetails.pe_ratio}x` : 'N/A';
  const vol = companyDetails.volume ? `${(companyDetails.volume / 1e6).toFixed(1)}M` : 'N/A';
  const high52 = companyDetails.fifty_two_week_high ? `$${companyDetails.fifty_two_week_high.toFixed(2)}` : 'N/A';
  const low52 = companyDetails.fifty_two_week_low ? `$${companyDetails.fifty_two_week_low.toFixed(2)}` : 'N/A';

  gridEl.innerHTML = `
    <div class="stat-cell"><div class="stat-cell-label">Open</div><div class="stat-cell-value">$${(companyDetails.price * 0.99).toFixed(2)}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">High</div><div class="stat-cell-value" style="color:var(--green)">$${(companyDetails.price * 1.01).toFixed(2)}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">Low</div><div class="stat-cell-value" style="color:var(--red)">$${(companyDetails.price * 0.985).toFixed(2)}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">Volume</div><div class="stat-cell-value">${vol}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">Market Cap</div><div class="stat-cell-value">${fmtCap}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">P/E Ratio</div><div class="stat-cell-value">${pe}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">52W High</div><div class="stat-cell-value">${high52}</div></div>
    <div class="stat-cell"><div class="stat-cell-label">52W Low</div><div class="stat-cell-value">${low52}</div></div>
  `;
}

window.setInfoTab = function(tab, el) {
  document.querySelectorAll('.chart-card .chart-period').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  updateTabsUI(tab);
};

function updateTabsUI(tab) {
  const content = document.getElementById('infoTabContent');
  if (!content) return;

  const rev = companyDetails.market_cap ? (companyDetails.market_cap * 0.15) : 100e9;
  const net = rev * 0.22;
  const eps = companyDetails.pe_ratio ? (companyDetails.price / companyDetails.pe_ratio) : 4.5;

  const tabs = {
    about: `<p style="color:var(--text-muted);line-height:1.75;font-size:0.9rem">${companyDetails.name} operates in the ${companyDetails.sector} (${companyDetails.industry}) sector. The company maintains a compliance profile rated as ${companyDetails.shariah_status} with Shariah score of ${companyDetails.shariah_score}/100 based on core financial screens.</p>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1.25rem">
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.875rem;text-align:center"><div style="font-size:0.72rem;color:var(--text-muted);font-family:var(--font-mono);margin-bottom:4px">REVENUE (TTM)</div><div style="font-family:var(--font-mono);font-weight:700;color:var(--white)">${window.HalalStocks.formatBigNum(rev)}</div></div>
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.875rem;text-align:center"><div style="font-size:0.72rem;color:var(--text-muted);font-family:var(--font-mono);margin-bottom:4px">NET INCOME</div><div style="font-family:var(--font-mono);font-weight:700;color:var(--green)">${window.HalalStocks.formatBigNum(net)}</div></div>
        <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.875rem;text-align:center"><div style="font-size:0.72rem;color:var(--text-muted);font-family:var(--font-mono);margin-bottom:4px">EPS</div><div style="font-family:var(--font-mono);font-weight:700;color:var(--white)">$${eps.toFixed(2)}</div></div>
      </div>`,
    financials: `<div style="display:flex;flex-direction:column;gap:0.75rem">
      ${[
        ['Revenue Growth','11.8%','up'],
        ['Gross Margin','42.5%','up'],
        ['Operating Margin','28.2%','up'],
        ['Debt/Assets', `${shariahDetail.debt_ratio || 0}%`, (shariahDetail.debt_ratio > 33 ? 'warn' : 'up')],
        ['Interest/Revenue', `${shariahDetail.haram_revenue || 0}%`, (shariahDetail.haram_revenue > 5 ? 'warn' : 'up')],
        ['Current Ratio','1.25x','neutral'],
        ['Free Cash Flow','Robust','up']
      ].map(([l,v,t])=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:0.625rem 0;border-bottom:1px solid var(--border)"><span style="color:var(--text-muted);font-size:0.85rem">${l}</span><span style="font-family:var(--font-mono);font-weight:700;color:${t==='up'?'var(--green)':t==='warn'?'var(--red)':'var(--white)'}">${v}</span></div>`).join('')}
    </div>`,
    analysis: `<div style="display:flex;flex-direction:column;gap:1rem">
      <div style="background:var(--green-glow);border:1px solid rgba(16,185,129,0.2);border-radius:var(--radius);padding:1rem"><div style="font-weight:700;color:var(--green);margin-bottom:6px">✓ Bull Case</div><div style="font-size:0.83rem;color:var(--text-muted);line-height:1.65">Strong business dynamics in ${companyDetails.sector}, robust cash streams, and favorable market outlook. AI score stands at ${companyDetails.ai_score}%.</div></div>
      <div style="background:var(--red-glow);border:1px solid rgba(239,68,68,0.2);border-radius:var(--radius);padding:1rem"><div style="font-weight:700;color:var(--red);margin-bottom:6px">⚠ Bear Case</div><div style="font-size:0.83rem;color:var(--text-muted);line-height:1.65">Macro headwinds, regulatory challenges in ${companyDetails.industry}, and global volatility. Shariah debt levels need ongoing quarterly monitoring.</div></div>
      <div style="background:rgba(14,165,233,0.08);border:1px solid rgba(14,165,233,0.2);border-radius:var(--radius);padding:1rem"><div style="font-weight:700;color:var(--primary);margin-bottom:6px">🤖 AI Summary</div><div style="font-size:0.83rem;color:var(--text-muted);line-height:1.65">LSTM model identifies target bands. Sentiment reads ${aiPrediction.sentiment || 70}% positive. Combined verdict is ${aiPrediction.verdict || 'HOLD'} with ${aiPrediction.confidence || 80}% certainty.</div></div>
      
      <!-- Prediction History -->
      <div style="background:rgba(255, 255, 255, 0.01);border:1px solid var(--border);border-radius:var(--radius);padding:1.25rem">
        <div style="font-weight:700;color:var(--white);margin-bottom:0.75rem;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em">🤖 Historical AI Rulings</div>
        ${predictionHistory.length === 0 ? '<div style="font-size:0.8rem;color:var(--text-muted)">No prediction history available yet.</div>' : `
          <div style="display:flex;flex-direction:column;gap:0.50rem">
            ${predictionHistory.map(h => {
              const dt = new Date(h.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
              const vClass = h.verdict === 'BUY' ? 'buy' : h.verdict === 'HOLD' ? 'hold' : 'avoid';
              return `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:0.8rem">
                  <span style="color:var(--text-muted)">${dt}</span>
                  <div style="display:flex;align-items:center;gap:0.75rem">
                    <span style="font-family:var(--font-mono);color:var(--text-dim)">Score: ${h.ensemble}%</span>
                    <span class="badge badge-${vClass}" style="padding:0.15rem 0.5rem;font-size:0.65rem">${h.verdict}</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `}
      </div>
    </div>`
  };
  content.innerHTML = tabs[tab] || tabs.about;
}

function updatePredictionUI() {
  const verdictWord = document.querySelector('.verdict-word');
  const verdictIcon = document.querySelector('.verdict-icon');
  const verdictBox = document.querySelector('.verdict-big');
  const verdictConf = document.querySelector('.verdict-conf');

  if (verdictWord && aiPrediction.verdict) {
    verdictWord.textContent = aiPrediction.verdict;
    const isBuy = aiPrediction.verdict === 'BUY';
    const isHold = aiPrediction.verdict === 'HOLD';
    
    verdictIcon.textContent = isBuy ? '📈' : isHold ? '📊' : '📉';
    verdictBox.className = 'verdict-big ' + (isBuy ? 'buy' : isHold ? 'hold' : 'avoid');
    verdictConf.textContent = `${aiPrediction.confidence}% confidence · 4-model ensemble`;
  }

  // Animate model bars with values
  const modelRows = document.querySelectorAll('.model-row');
  const scores = [
    aiPrediction.lstm_score || 80,
    aiPrediction.sentiment || 75,
    aiPrediction.shariah_score || 90,
    aiPrediction.ensemble || 80
  ];
  
  modelRows.forEach((row, i) => {
    const fill = row.querySelector('.model-row-fill');
    const val = row.querySelector('.model-row-val');
    const scoreVal = scores[i];
    if (fill) {
      fill.setAttribute('data-w', scoreVal);
      fill.style.width = scoreVal + '%';
    }
    if (val) val.textContent = scoreVal;
  });

  // Target prices
  const targets = document.querySelectorAll('.target-value');
  if (targets.length === 2) {
    targets[0].textContent = window.HalalStocks.formatPrice(currentPrice * 1.15);
    targets[1].textContent = window.HalalStocks.formatPrice(currentPrice * 0.90);
  }
}

function updateShariahUI() {
  const shariahBox = document.querySelector('.shariah-card');
  if (!shariahBox) return;

  const headerBadge = shariahBox.querySelector('.badge');
  const isHalal = shariahDetail.status === 'Halal';
  const isDoubtful = shariahDetail.status === 'Doubtful';
  
  if (headerBadge) {
    headerBadge.className = `badge ` + (isHalal ? 'badge-halal' : isDoubtful ? 'badge-doubtful' : 'badge-haram');
    headerBadge.textContent = (isHalal ? '✓ ' : '⚠ ') + shariahDetail.status;
  }

  const passVal = (val, max, sign = '%') => {
    const isPass = val <= max;
    return `<span class="shariah-row-value ${isPass ? 'pass' : 'warn'}">${val}${sign} ${isPass ? '✓' : '⚠'}</span>`;
  };

  const body = shariahBox.querySelector('.shariah-card-body');
  if (body && shariahDetail.score) {
    body.innerHTML = `
      <div class="shariah-row"><span class="shariah-row-label">Debt Ratio</span>${passVal(shariahDetail.debt_ratio, 33)}</div>
      <div class="shariah-row"><span class="shariah-row-label">Haram Revenue</span>${passVal(shariahDetail.haram_revenue, 5)}</div>
      <div class="shariah-row"><span class="shariah-row-label">Business Type</span><span class="shariah-row-value pass">${shariahDetail.business_type.split(' ')[0]} ✓</span></div>
      <div class="shariah-row"><span class="shariah-row-label">Interest Income</span>${passVal(shariahDetail.haram_revenue, 5)}</div>
      <div class="shariah-row"><span class="shariah-row-label">Overall Score</span><span class="shariah-row-value pass" style="font-size:1rem;font-weight:800">${shariahDetail.score} / 100</span></div>
    `;
  }
}

function updateNewsUI() {
  const newsContainer = document.getElementById('newsItems');
  if (!newsContainer) return;

  // Render news related to specific company
  const simulatedNews = [
    { headline: `${companyDetails.name} reports robust quarterly results aligned with sector momentum`, source: 'Reuters', time: '1h ago', sentiment: 'pos' },
    { headline: `Analysts highlight ${symbol} as top halal pick in current AI development cycle`, source: 'Bloomberg', time: '3h ago', sentiment: 'pos' },
    { headline: `Shariah advisory committee updates quarterly audit metrics for ${symbol}`, source: 'HalalEdge', time: '6h ago', sentiment: 'neutral' },
    { headline: `Regulatory parameters check for ${companyDetails.sector} firms shows higher compliance costs`, source: 'WSJ', time: '1d ago', sentiment: 'neg' }
  ];

  newsContainer.innerHTML = simulatedNews.map(n => `
    <div class="news-item">
      <div class="news-headline">${n.headline}</div>
      <div class="news-meta">
        <span>${n.source}</span>
        <span>·</span>
        <span>${n.time}</span>
        <span class="news-sentiment ${n.sentiment}">${n.sentiment === 'pos' ? '↑ Positive' : n.sentiment === 'neg' ? '↓ Negative' : '→ Neutral'}</span>
      </div>
    </div>`).join('');
}

// ── Chart.js API Connection ────────────────────────────────────
const _chartCache = {};

function getChartCtx() {
  let canvas = document.getElementById('mainChart');
  if (!canvas) {
    const chartBody = document.querySelector('.chart-card .chart-body');
    if (chartBody) {
      chartBody.innerHTML = '<canvas id="mainChart" height="220"></canvas>';
      canvas = document.getElementById('mainChart');
    }
  }
  return canvas?.getContext('2d');
}

function showChartSkeleton() {
  const chartBody = document.querySelector('.chart-card .chart-body');
  if (chartBody) chartBody.innerHTML = window.HalalStocks.skeleton.chart('220px');
}

async function drawChart(period = '1D') {
  try {
    // Render instantly from cache if we already fetched this period
    if (_chartCache[period]) {
      _renderChart(_chartCache[period], period);
      return;
    }

    showChartSkeleton();

    const res = await fetch(`${window.HalalStocks.API_BASE}/stocks/${symbol}/history?period=${period}`);
    if (!res.ok) return;

    const dataObj = await res.json();
    const history = dataObj.history;
    _chartCache[period] = history;

    _renderChart(history, period);
  } catch (err) {
    console.error('Error drawing chart:', err);
  }
}

function _renderChart(history, period) {
  const labels = history.map(item => {
    const date = new Date(item.date);
    if (period === '1D') {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  });

  const prices = history.map(item => item.close);
  const isUp = prices[prices.length - 1] >= prices[0];
  const color = isUp ? '#10b981' : '#ef4444';

  if (chart) chart.destroy();
  const ctx = getChartCtx();
  if (!ctx) return;

  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: prices,
        borderColor: color,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: color,
        fill: true,
        backgroundColor: (ctx2) => {
          const gradient = ctx2.chart.ctx.createLinearGradient(0, 0, 0, 200);
          gradient.addColorStop(0, isUp ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)');
          gradient.addColorStop(1, 'rgba(0,0,0,0)');
          return gradient;
        },
        tension: 0.2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0a1628',
          borderColor: 'rgba(99,179,237,0.2)',
          borderWidth: 1,
          titleColor: '#94a3b8',
          bodyColor: '#e2e8f0',
          bodyFont: { family: 'JetBrains Mono' },
          callbacks: {
            label: (item) => ' $' + item.raw.toFixed(2)
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.02)', drawBorder: false },
          ticks: { color: '#64748b', font: { size: 10, family: 'JetBrains Mono' }, maxTicksLimit: 7 }
        },
        y: {
          position: 'right',
          grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
          ticks: { color: '#64748b', font: { size: 10, family: 'JetBrains Mono' }, callback: v => '$' + v.toFixed(2) }
        }
      }
    }
  });
}

window.setPeriod = function(period, el) {
  document.querySelectorAll('.chart-periods .chart-period').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  drawChart(period);
};

// ── Portfolio & Watchlist Form Adders ──────────────────────────
window.addToPortfolio = async function() {
  const token = localStorage.getItem('token');
  if (!token) {
    window.HalalStocks?.showToast('Please sign in to add to your portfolio.', 'error');
    setTimeout(() => { window.location.href = 'login.html'; }, 1500);
    return;
  }
  
  const sharesStr = prompt(`How many shares of ${symbol} would you like to add?`, "10");
  if (sharesStr === null) return;
  const shares = parseFloat(sharesStr);
  if (isNaN(shares) || shares <= 0) {
    window.HalalStocks?.showToast('Invalid shares amount.', 'error');
    return;
  }

  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/portfolio/`, {
      method: 'POST',
      headers: window.HalalStocks.getAuthHeaders(),
      body: JSON.stringify({ symbol, shares, avg_price: currentPrice })
    });
    if (res.ok) {
      window.HalalStocks?.showToast(`${symbol} added to portfolio!`, 'success');
    } else {
      const err = await res.json();
      window.HalalStocks?.showToast(err.detail || 'Failed to add holding.', 'error');
    }
  } catch (err) {
    window.HalalStocks?.showToast('Backend connection error.', 'error');
  }
};

window.addToWatchlist = async function() {
  const token = localStorage.getItem('token');
  if (!token) {
    window.HalalStocks?.showToast('Please sign in to manage your watchlist.', 'error');
    setTimeout(() => { window.location.href = 'login.html'; }, 1500);
    return;
  }

  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/watchlist/`, {
      method: 'POST',
      headers: window.HalalStocks.getAuthHeaders(),
      body: JSON.stringify({ symbol })
    });
    if (res.ok) {
      window.HalalStocks?.showToast(`${symbol} added to watchlist!`, 'success');
    } else {
      const err = await res.json();
      window.HalalStocks?.showToast(err.detail || 'Failed to add to watchlist.', 'error');
    }
  } catch (err) {
    window.HalalStocks?.showToast('Backend connection error.', 'error');
  }
};

// ── Init ──────────────────────────────────────────────────────
loadStockDetails();

// Refresh timestamp every minute (no need to re-run full ML/prediction pipeline)
setInterval(() => {
  updateTimestamp();
}, 60000);