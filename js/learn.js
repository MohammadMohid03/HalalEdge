// ── FAQ Data ──────────────────────────────────────────────────
const faqs = [
  { q: 'Is HalalEdge completely free to use?', a: 'Yes — HalalEdge is 100% free. All AI predictions, Shariah screening, portfolio tracking and educational content are available at no cost. This platform was built as an open resource for the Muslim investing community.' },
  { q: 'How accurate are the AI stock predictions?', a: 'Our 4-model ensemble achieves approximately 71–78% directional accuracy on backtested data over 12-month horizons. However, no AI model can predict markets with certainty. Always treat predictions as one input among many and never invest more than you can afford to lose.' },
  { q: 'Which Shariah standard does HalalEdge follow?', a: 'We follow AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards — the globally recognized benchmark for Islamic financial products. Our filters check debt ratios, haram revenue percentages, and business activity classification.' },
  { q: 'Can I trust the Halal / Haram classification?', a: 'Our classifications are based on publicly available financial data and AAOIFI criteria. However, we strongly recommend consulting with a qualified Islamic finance scholar for personal fatwa on specific investment decisions. Different schools of thought may have slightly different thresholds.' },
  { q: 'Is investing in stocks halal at all?', a: 'Yes — the majority of contemporary Islamic scholars permit investing in stocks of permissible companies. You become a part-owner of a real business, sharing in its profits and losses, which is fundamentally different from interest-based transactions. The OIC Fiqh Academy and AAOIFI both permit equity investment under specific conditions.' },
  { q: 'Are ETFs and index funds halal?', a: 'Some ETFs and index funds are halal, but most conventional ones include non-compliant holdings. You need a Shariah-screened ETF (such as those from Wahed Invest or SP Funds) or use our screener to identify individual halal stocks. Standard S&P 500 ETFs include banks and other haram companies.' },
  { q: 'What about crypto — is it halal?', a: 'This is a contested area with no consensus. Some scholars permit Bitcoin and major cryptocurrencies as a store of value; others prohibit them due to excessive speculation (gharar). HalalEdge currently focuses on stocks and equities only. We recommend researching this separately with qualified scholars.' },
  { q: 'How often is the AI model updated?', a: 'Price data feeds update every minute during market hours. Sentiment analysis from news runs every 30 minutes. Financial statement data (used for Shariah compliance) is updated quarterly when companies report earnings. AI model weights are retrained monthly.' },
  { q: 'What markets does HalalEdge cover?', a: 'We currently cover NASDAQ, NYSE, LSE (London), Tadawul (Saudi Arabia), and Bursa Malaysia — over 2,400 halal-screened stocks across 47 markets. More markets are added continuously.' },
  { q: 'Is margin trading halal?', a: 'No — margin trading involves borrowing money with interest (riba) which is prohibited in Islam. HalalEdge strongly advises against margin trading. Only invest with funds you actually own.' },
  { q: 'Can I download my portfolio data?', a: 'Yes — on the Portfolio page, click "Export" to download your holdings as a CSV file that works with Excel or Google Sheets.' },
  { q: 'Who built HalalEdge?', a: 'HalalEdge was built as a web development course project by a passionate team of Muslim developers who wanted to solve a real problem — making halal investing accessible, intelligent, and free for everyone.' },
];

// ── Glossary Data ─────────────────────────────────────────────
const glossary = [
  { term: 'Riba', def: 'Prohibited interest or usury in Islamic law. Any guaranteed return on money lent.' },
  { term: 'Gharar', def: 'Excessive uncertainty or ambiguity in a contract. Excessive speculation is prohibited.' },
  { term: 'AAOIFI', def: 'Accounting and Auditing Organization for Islamic Financial Institutions — global Shariah standard setter.' },
  { term: 'Maysir', def: 'Gambling or games of chance. Strictly prohibited in Islam.' },
  { term: 'Halal', def: 'Permissible under Islamic Shariah law. In investing, refers to compliant stocks and instruments.' },
  { term: 'Haram', def: 'Prohibited under Islamic Shariah law. Companies in haram industries cannot be invested in.' },
  { term: 'Zakat', def: 'Obligatory alms on wealth. Muslim investors must calculate and pay Zakat on their investment portfolio annually.' },
  { term: 'Sukuk', def: 'Islamic bonds structured to comply with Shariah. Returns come from assets, not interest.' },
  { term: 'P/E Ratio', def: 'Price-to-Earnings ratio. Stock price divided by earnings per share. Measures valuation.' },
  { term: 'Market Cap', def: 'Total market value of a company. Share price × total shares outstanding.' },
  { term: 'Beta', def: 'Measure of a stock\'s volatility vs. the market. Beta > 1 means more volatile than market.' },
  { term: 'Dividend', def: 'A portion of profits paid to shareholders. Halal if the company itself is halal.' },
  { term: 'EPS', def: 'Earnings Per Share. Net income divided by total shares. Key profitability metric.' },
  { term: 'Bull Market', def: 'A sustained period of rising stock prices, typically 20%+ gain from recent lows.' },
  { term: 'Bear Market', def: 'A sustained period of falling stock prices, typically 20%+ decline from recent highs.' },
  { term: 'LSTM', def: 'Long Short-Term Memory neural network. Excels at learning patterns in sequential time-series data.' },
  { term: 'Sentiment', def: 'The overall attitude (positive/negative/neutral) of the market or news toward a stock.' },
  { term: 'XGBoost', def: 'Extreme Gradient Boosting. A powerful machine learning algorithm used in our ensemble scorer.' },
  { term: 'Ensemble', def: 'Combining multiple AI model predictions to produce a more accurate final result.' },
  { term: 'Shariah Screen', def: 'The process of filtering investments to ensure compliance with Islamic law.' },
];

// ── Render FAQ ────────────────────────────────────────────────
function renderFAQ() {
  const list = document.getElementById('faqList');
  if (!list) return;
  list.innerHTML = faqs.map((f, i) => `
    <div class="faq-item" id="faq-${i}">
      <div class="faq-question" onclick="toggleFAQ(${i})">
        <span>${f.q}</span>
        <i class="fa fa-chevron-down faq-icon"></i>
      </div>
      <div class="faq-answer">${f.a}</div>
    </div>
  `).join('');
}

window.toggleFAQ = function(i) {
  const item = document.getElementById('faq-' + i);
  const wasOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item').forEach(el => el.classList.remove('open'));
  if (!wasOpen) item.classList.add('open');
};

// ── Render Glossary ───────────────────────────────────────────
function renderGlossary() {
  const grid = document.getElementById('glossaryGrid');
  if (!grid) return;
  grid.innerHTML = glossary.map(g => `
    <div class="glossary-item">
      <div class="glossary-term">${g.term}</div>
      <div class="glossary-def">${g.def}</div>
    </div>
  `).join('');
}

// ── Article expand ────────────────────────────────────────────
window.expandArticle = function(card) {
  const expanded = card.querySelector('.article-expanded');
  const readMore = card.querySelector('.article-read');
  if (!expanded) return;
  const isOpen = expanded.style.display === 'block';
  expanded.style.display = isOpen ? 'none' : 'block';
  if (readMore) readMore.textContent = isOpen ? 'Read more →' : 'Read less ↑';
  card.style.borderColor = isOpen ? 'var(--border)' : 'var(--border-glow)';
};

// ── Sidebar nav scroll ────────────────────────────────────────
window.scrollToSection = function(id, el) {
  document.querySelectorAll('.learn-nav-item').forEach(n => n.classList.remove('active'));
  el.classList.add('active');
  const target = document.getElementById(id);
  if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
};

// ── Update active nav on scroll ───────────────────────────────
const sections = ['what-is-halal', 'shariah', 'how-ai', 'basics', 'faq', 'glossary'];
const navItems = document.querySelectorAll('.learn-nav-item');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el && window.scrollY >= el.offsetTop - 140) current = id;
  });
  const sectionMap = { 'what-is-halal': 0, 'shariah': 1, 'how-ai': 2, 'basics': 3, 'faq': 4, 'glossary': 5 };
  navItems.forEach(n => n.classList.remove('active'));
  if (current && sectionMap[current] !== undefined) {
    navItems[sectionMap[current]]?.classList.add('active');
  }
});

// ── Init ──────────────────────────────────────────────────────
renderFAQ();
renderGlossary();