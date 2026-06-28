// Guard: Check authentication
if (!localStorage.getItem('token')) {
  window.location.href = 'login.html';
}

let portfolio = []; // Will store holdings list returned from API
let pieChart = null;

async function loadPortfolio() {
  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/portfolio/summary`, {
      headers: window.HalalStocks.getAuthHeaders()
    });

    if (res.status === 401) {
      window.location.href = 'login.html';
      return;
    }

    if (!res.ok) {
      window.HalalStocks.showToast('Failed to load portfolio details.', 'error');
      return;
    }

    const data = await res.json();
    portfolio = data.holdings;
    
    updateSummaryUI(data);
    renderPortfolioTable();
    renderPieChart();
    updateZakatUI();

    // Fetch and render watchlist
    try {
      const watchRes = await fetch(`${window.HalalStocks.API_BASE}/watchlist/`, {
        headers: window.HalalStocks.getAuthHeaders()
      });
      if (watchRes.ok) {
        const watchData = await watchRes.json();
        renderWatchlistTable(watchData);
      }
    } catch (e) {
      console.error('Error loading watchlist:', e);
    }
  } catch (err) {
    console.error('Error loading portfolio:', err);
    window.HalalStocks.showToast('Backend connection error. Is the server running?', 'error');
  }
}

function updateSummaryUI(data) {
  const fmt = n => '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  
  const valEl = document.getElementById('totalValue');
  if (valEl) valEl.textContent = fmt(data.total_value);
  
  const gainEl = document.getElementById('totalGainAbs');
  if (gainEl) {
    const sign = data.total_gain_abs >= 0 ? '+' : '-';
    gainEl.textContent = `${sign}${fmt(data.total_gain_abs)} (${data.total_gain_pct.toFixed(2)}%)`;
    gainEl.className = 'summary-card-sub ' + (data.total_gain_abs >= 0 ? 'price-up' : 'price-down');
  }
  
  const todayEl = document.getElementById('todayGain');
  if (todayEl) {
    const sign = data.today_gain_abs >= 0 ? '+' : '-';
    todayEl.textContent = `${sign}${fmt(data.today_gain_abs)}`;
    todayEl.className = 'summary-card-sub ' + (data.today_gain_abs >= 0 ? 'price-up' : 'price-down');
  }
  
  const countEl = document.getElementById('holdingsCount');
  if (countEl) countEl.textContent = data.holdings_count;
}

function renderPortfolioTable() {
  const body = document.getElementById('holdingsBody');
  const empty = document.getElementById('emptyPortfolio');
  if (!body) return;

  if (portfolio.length === 0) {
    body.innerHTML = '';
    if (empty) empty.style.display = 'block';
    return;
  }
  if (empty) empty.style.display = 'none';

  body.innerHTML = portfolio.map((h) => {
    const plClass = h.pl_abs >= 0 ? 'price-up' : 'price-down';
    const plSign = h.pl_abs >= 0 ? '+' : '';
    const scoreClass = h.ai_score >= 80 ? 'high' : h.ai_score >= 65 ? 'mid' : 'low';
    
    return `
      <tr onclick="location.href='stock.html?sym=${h.symbol}'" style="cursor:pointer">
        <td><div class="td-stock">
          <div class="td-avatar" style="background:linear-gradient(135deg,${h.color}55,${h.color})">${h.symbol.slice(0,2)}</div>
          <div><div class="td-symbol">${h.symbol}</div><div class="td-name">${h.company_name}</div></div>
        </div></td>
        <td style="font-family:var(--font-mono);color:var(--white)">${h.shares}</td>
        <td style="font-family:var(--font-mono);color:var(--text-muted)">$${h.avg_price.toFixed(2)}</td>
        <td style="font-family:var(--font-mono);color:var(--white)">$${h.current_price.toFixed(2)}</td>
        <td style="font-family:var(--font-mono);font-weight:700;color:var(--white)">$${h.total_value.toFixed(0)}</td>
        <td class="${plClass}" style="font-family:var(--font-mono);font-weight:700">${h.pl_abs >= 0 ? '▲' : '▼'} ${plSign}${h.pl_pct.toFixed(2)}%</td>
        <td><span class="ai-score-pill ${scoreClass}">${h.ai_score}%</span></td>
        <td onclick="event.stopPropagation()"><div class="remove-btn" onclick="removeStock('${h.id}', '${h.symbol}')"><i class="fa fa-trash"></i></div></td>
      </tr>`;
  }).join('');
}

function renderPieChart() {
  const canvas = document.getElementById('pieChart');
  const legend = document.getElementById('pieLegend');
  if (!canvas) return;

  if (portfolio.length === 0) {
    if (legend) legend.innerHTML = '<div style="font-size:0.82rem;color:var(--text-muted);text-align:center">Add stocks to see allocation</div>';
    if (pieChart) { pieChart.destroy(); pieChart = null; }
    return;
  }

  // Group by sector
  const sectors = {};
  portfolio.forEach(h => {
    sectors[h.sector] = (sectors[h.sector] || 0) + h.total_value;
  });

  const colors = ['#0ea5e9','#10b981','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#f97316'];
  const labels = Object.keys(sectors);
  const values = Object.values(sectors);
  const total = values.reduce((a, b) => a + b, 0);

  if (pieChart) pieChart.destroy();
  pieChart = new Chart(canvas.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 2, borderColor: '#0a1628', hoverBorderColor: '#0a1628' }]
    },
    options: {
      responsive: false,
      cutout: '68%',
      plugins: { legend: { display: false }, tooltip: {
        backgroundColor: '#0a1628',
        borderColor: 'rgba(99,179,237,0.2)',
        borderWidth: 1,
        bodyColor: '#e2e8f0',
        callbacks: { label: (item) => ' ' + item.label + ': ' + ((item.raw / total) * 100).toFixed(1) + '%' }
      }}
    }
  });

  if (legend) {
    legend.innerHTML = labels.map((l, i) => `
      <div class="legend-item">
        <div class="legend-dot" style="background:${colors[i]}"></div>
        <span class="legend-name">${l}</span>
        <span class="legend-pct">${((values[i] / total) * 100).toFixed(1)}%</span>
      </div>`).join('');
  }
}

// ── Modal ─────────────────────────────────────────────────────
window.openModal = function() {
  document.getElementById('modalOverlay').classList.add('open');
  document.getElementById('modalSymbol').focus();
};
window.closeModal = function() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.getElementById('modalSymbol').value = '';
  document.getElementById('modalShares').value = '';
  document.getElementById('modalPrice').value = '';
  document.querySelectorAll('.field-error').forEach(e => e.classList.remove('show'));
};
window.closeModalOutside = function(e) {
  if (e.target === document.getElementById('modalOverlay')) closeModal();
};

window.addStock = async function() {
  const sym = document.getElementById('modalSymbol').value.trim().toUpperCase();
  const shares = parseFloat(document.getElementById('modalShares').value);
  const price = parseFloat(document.getElementById('modalPrice').value);
  let valid = true;

  const showErr = (id, show) => {
    const el = document.getElementById(id);
    el?.classList.toggle('show', show);
    const input = el?.previousElementSibling?.querySelector('input');
    input?.classList.toggle('error', show);
    input?.classList.toggle('success', !show && input.value);
  };

  if (!sym || sym.length < 1 || sym.length > 5) { showErr('symbolErr', true); valid = false; } else showErr('symbolErr', false);
  if (!shares || shares <= 0) { showErr('sharesErr', true); valid = false; } else showErr('sharesErr', false);
  if (!price || price <= 0) { showErr('priceErr', true); valid = false; } else showErr('priceErr', false);

  if (!valid) return;

  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/portfolio/`, {
      method: 'POST',
      headers: window.HalalStocks.getAuthHeaders(),
      body: JSON.stringify({ symbol: sym, shares, avg_price: price })
    });

    if (res.ok) {
      window.HalalStocks?.showToast(`${sym} added to portfolio!`, 'success');
      closeModal();
      loadPortfolio();
    } else {
      const err = await res.json();
      window.HalalStocks?.showToast(err.detail || 'Could not add holding. Verify ticker.', 'error');
    }
  } catch (err) {
    window.HalalStocks?.showToast('Error connecting to backend.', 'error');
  }
};

window.removeStock = async function(holdingId, sym) {
  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/portfolio/${holdingId}`, {
      method: 'DELETE',
      headers: window.HalalStocks.getAuthHeaders()
    });

    if (res.ok) {
      window.HalalStocks?.showToast(`${sym} removed from portfolio`, 'error');
      loadPortfolio();
    } else {
      window.HalalStocks?.showToast('Failed to remove stock', 'error');
    }
  } catch (err) {
    window.HalalStocks?.showToast('Error connecting to backend.', 'error');
  }
};

window.exportPortfolio = function() {
  if (portfolio.length === 0) { window.HalalStocks?.showToast('Nothing to export yet!', 'error'); return; }
  
  fetch(`${window.HalalStocks.API_BASE}/portfolio/export`, {
    headers: window.HalalStocks.getAuthHeaders()
  })
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'NoorInvest-Portfolio.csv';
    document.body.appendChild(a);
    a.click();    
    a.remove();
    window.HalalStocks?.showToast('Portfolio exported as CSV!', 'success');
  })
  .catch(err => {
    window.HalalStocks?.showToast('Could not download CSV export.', 'error');
  });
};

// ── Zakat Calculator Logic ────────────────────────────────────
let currentZakatMethod = 'nav';

window.setZakatMethod = function(method) {
  currentZakatMethod = method;
  const btnNav = document.getElementById('btnZakatNav');
  const btnTrade = document.getElementById('btnZakatTrade');
  
  if (method === 'nav') {
    btnNav.classList.add('active');
    btnNav.style.borderColor = 'var(--primary)';
    btnNav.style.color = 'var(--primary)';
    
    btnTrade.classList.remove('active');
    btnTrade.style.borderColor = '';
    btnTrade.style.color = '';
  } else {
    btnTrade.classList.add('active');
    btnTrade.style.borderColor = 'var(--primary)';
    btnTrade.style.color = 'var(--primary)';
    
    btnNav.classList.remove('active');
    btnNav.style.borderColor = '';
    btnNav.style.color = '';
  }
  updateZakatUI();
};

function updateZakatUI() {
  const totalVal = portfolio.reduce((sum, h) => sum + h.total_value, 0);
  const zakatableRatio = currentZakatMethod === 'nav' ? 0.25 : 1.0;
  const zakatableValue = totalVal * zakatableRatio;
  const ZakatDue = zakatableValue * 0.025;

  const zakatableValEl = document.getElementById('zakatableVal');
  const zakatDueEl = document.getElementById('zakatDue');

  if (zakatableValEl) {
    zakatableValEl.textContent = '$' + zakatableValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (zakatDueEl) {
    zakatDueEl.textContent = '$' + ZakatDue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
}

function renderWatchlistTable(items) {
  const body = document.getElementById('watchlistBody');
  const empty = document.getElementById('emptyWatchlist');
  if (!body) return;

  if (!items || items.length === 0) {
    body.innerHTML = '';
    if (empty) empty.style.display = 'block';
    return;
  }
  if (empty) empty.style.display = 'none';

  body.innerHTML = items.map((w) => {
    const isUp = w.change >= 0;
    const plClass = isUp ? 'price-up' : 'price-down';
    const plSign = isUp ? '+' : '';
    const scoreClass = w.ai_score >= 80 ? 'high' : w.ai_score >= 65 ? 'mid' : 'low';
    const verdictClass = w.verdict === 'BUY' ? 'buy' : w.verdict === 'HOLD' ? 'hold' : 'avoid';
    const shariahClass = w.shariah_status === 'Halal' ? 'halal' : 'doubtful';
    const color = w.color || '#0ea5e9';

    return `
      <tr onclick="location.href='stock.html?sym=${w.symbol}'" style="cursor:pointer">
        <td><div class="td-stock">
          <div class="td-avatar" style="background:linear-gradient(135deg,${color}55,${color})">${w.symbol.slice(0,2)}</div>
          <div><div class="td-symbol">${w.symbol}</div><div class="td-name">${w.name}</div></div>
        </div></td>
        <td style="font-family:var(--font-mono);color:var(--white)">$${w.price.toFixed(2)}</td>
        <td class="${plClass}" style="font-family:var(--font-mono);font-weight:700">${isUp ? '▲' : '▼'} ${plSign}${w.change.toFixed(2)}%</td>
        <td><span class="badge badge-${shariahClass}">${w.shariah_status === 'Halal' ? '✓' : '⚠'} ${w.shariah_status}</span></td>
        <td><span class="badge badge-${verdictClass}">${w.verdict}</span></td>
        <td><span class="ai-score-pill ${scoreClass}">${w.ai_score}%</span></td>
        <td onclick="event.stopPropagation()">
          <div style="display:flex;gap:0.75rem;align-items:center">
            <button onclick="toggleWatchlistAlert('${w.symbol}')" title="${w.email_alerts ? 'Mute Email Alerts' : 'Enable Email Alerts'}" style="background:none;border:none;cursor:pointer;color:${w.email_alerts ? 'var(--gold)' : 'var(--text-muted)'};transition:color 0.2s">
              <i class="${w.email_alerts ? 'fa-solid fa-bell' : 'fa-regular fa-bell'}"></i>
            </button>
            <div class="remove-btn" onclick="removeFromWatchlist('${w.symbol}')" title="Remove from Watchlist">
              <i class="fa fa-trash"></i>
            </div>
          </div>
        </td>
      </tr>`;
  }).join('');
}

window.toggleWatchlistAlert = async function(sym) {
  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/watchlist/${sym}/toggle-alert`, {
      method: 'POST',
      headers: window.HalalStocks.getAuthHeaders()
    });
    if (res.ok) {
      const data = await res.json();
      window.HalalStocks?.showToast(data.email_alerts ? `Alerts enabled for ${sym}` : `Alerts muted for ${sym}`, 'success');
      loadPortfolio();
    } else {
      window.HalalStocks?.showToast('Failed to toggle alert status', 'error');
    }
  } catch (err) {
    window.HalalStocks?.showToast('Error connecting to backend.', 'error');
  }
};

window.removeFromWatchlist = async function(sym) {
  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/watchlist/${sym}`, {
      method: 'DELETE',
      headers: window.HalalStocks.getAuthHeaders()
    });
    if (res.ok) {
      window.HalalStocks?.showToast(`${sym} removed from watchlist`, 'error');
      loadPortfolio();
    } else {
      window.HalalStocks?.showToast('Failed to remove from watchlist', 'error');
    }
  } catch (err) {
    window.HalalStocks?.showToast('Error connecting to backend.', 'error');
  }
};

// ── Init ──────────────────────────────────────────────────────
loadPortfolio();

// ── Live price updates ────────────────────────────────────────
setInterval(() => { loadPortfolio(); }, 5000);


