// ── Shared Utilities ──────────────────────────────────────────
function showErr(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  if (msg) { const span = el.querySelector('span'); if (span) span.textContent = msg; }
  el.classList.add('show');
}
function hideErr(id) {
  document.getElementById(id)?.classList.remove('show');
}
function markInput(id, valid) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('error', !valid);
  el.classList.toggle('success', valid);
}

window.togglePw = function(id, iconEl) {
  const input = document.getElementById(id);
  if (!input) return;
  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';
  const icon = iconEl.querySelector('i');
  if (icon) { icon.className = isHidden ? 'fa fa-eye-slash' : 'fa fa-eye'; }
};

window.socialLogin = function(provider) {
  window.HalalStocks?.showToast(`${provider} login coming soon — use email for now!`, 'error');
};

// ══════════════════════════════════════════════
// ── LOGIN PAGE ────────────────────────────────
// ══════════════════════════════════════════════
function validateLoginEmail() {
  const val = document.getElementById('loginEmail')?.value.trim();
  if (!val) return false;
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
  markInput('loginEmail', valid);
  if (valid) hideErr('emailErr'); else showErr('emailErr');
  return valid;
}

function validateLoginPassword() {
  const val = document.getElementById('loginPassword')?.value;
  if (!val) return false;
  const valid = val.length >= 6;
  markInput('loginPassword', valid);
  if (valid) hideErr('passwordErr'); else showErr('passwordErr', 'Password must be at least 6 characters');
  return valid;
}

window.handleLogin = async function(e) {
  e.preventDefault();
  const emailOk = validateLoginEmail();
  const pwOk = validateLoginPassword();
  if (!emailOk || !pwOk) return;

  const email = document.getElementById('loginEmail')?.value.trim();
  const password = document.getElementById('loginPassword')?.value;

  const btn = document.getElementById('loginBtn');
  btn.classList.add('loading');
  btn.textContent = 'Signing in…';

  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await res.json();
    btn.classList.remove('loading');
    
    if (!res.ok) {
      btn.textContent = 'Sign In';
      window.HalalStocks?.showToast(data.detail || 'Failed to sign in. Please try again.', 'error');
      return;
    }
    
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      btn.innerHTML = '<i class="fa fa-check"></i> Success!';
      btn.style.background = 'linear-gradient(135deg,var(--halal-green),var(--green))';
      window.HalalStocks?.showToast('Welcome back to HalalEdge!', 'success');
      setTimeout(() => { window.location.href = 'index.html'; }, 1200);
    }
  } catch (err) {
    btn.classList.remove('loading');
    btn.textContent = 'Sign In';
    window.HalalStocks?.showToast('Backend connection error. Is the server running?', 'error');
  }
};

// ══════════════════════════════════════════════
// ── SIGNUP PAGE ───────────────────────────────
// ══════════════════════════════════════════════

// Password rule checker
const rules = {
  length:  { id: 'rule-length',  test: pw => pw.length >= 8 },
  upper:   { id: 'rule-upper',   test: pw => /[A-Z]/.test(pw) },
  lower:   { id: 'rule-lower',   test: pw => /[a-z]/.test(pw) },
  number:  { id: 'rule-number',  test: pw => /\d/.test(pw) },
  special: { id: 'rule-special', test: pw => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pw) },
};

function applyRule(id, passing) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.color = passing ? 'var(--green)' : 'var(--text-muted)';
  const icon = el.querySelector('i');
  if (icon) {
    icon.className = passing ? 'fa fa-check-circle' : 'fa fa-circle';
    icon.style.color = passing ? 'var(--green)' : 'var(--text-muted)';
  }
}

window.validatePassword = function() {
  const pw = document.getElementById('signupPassword')?.value || '';
  let score = 0;

  Object.entries(rules).forEach(([key, rule]) => {
    const passes = rule.test(pw);
    if (passes) score++;
    applyRule(rule.id, passes);
  });

  // Strength bars
  const bars = ['sb1','sb2','sb3','sb4'];
  const strengthLabel = document.getElementById('strengthLabel');
  const levels = [
    { color: 'var(--red)',  label: 'Weak',   class: 'weak' },
    { color: 'var(--red)',  label: 'Weak',   class: 'weak' },
    { color: 'var(--gold)', label: 'Fair',   class: 'medium' },
    { color: 'var(--gold)', label: 'Good',   class: 'medium' },
    { color: 'var(--green)',label: 'Strong', class: 'strong' },
  ];

  bars.forEach((bid, i) => {
    const bar = document.getElementById(bid);
    if (!bar) return;
    bar.className = 'strength-bar';
    if (i < score) {
      const lvl = levels[score - 1];
      bar.classList.add(lvl.class);
    }
  });

  if (pw && strengthLabel) {
    const lvl = levels[Math.min(score, 4)];
    strengthLabel.textContent = lvl.label;
    strengthLabel.className = 'strength-label ' + lvl.class;
  } else if (strengthLabel) {
    strengthLabel.textContent = '';
  }

  const valid = score >= 4;
  markInput('signupPassword', pw.length > 0 && valid);
  if (pw.length > 0 && !valid) {
    showErr('signupPwErr', 'Password must meet all requirements below');
  } else {
    hideErr('signupPwErr');
  }

  // Re-validate confirm if it has content
  const confirm = document.getElementById('confirmPassword');
  if (confirm?.value) validateConfirm();

  return valid && pw.length >= 8;
};

window.validateConfirm = function() {
  const pw = document.getElementById('signupPassword')?.value || '';
  const cpw = document.getElementById('confirmPassword')?.value || '';
  if (!cpw) return false;
  const valid = pw === cpw;
  markInput('confirmPassword', valid);
  if (valid) hideErr('confirmErr'); else showErr('confirmErr');
  return valid;
};

window.validateName = function() {
  const val = document.getElementById('fullName')?.value.trim() || '';
  const valid = val.length >= 2;
  markInput('fullName', val.length > 0 && valid);
  if (val.length > 0 && !valid) showErr('nameErr', 'Name must be at least 2 characters');
  else hideErr('nameErr');
  return valid;
};

window.validateEmail = function() {
  const val = document.getElementById('signupEmail')?.value.trim() || '';
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
  if (val) markInput('signupEmail', valid);
  if (val && valid) hideErr('signupEmailErr');
  else if (val) showErr('signupEmailErr');
  return valid;
};

window.handleSignup = async function(e) {
  e.preventDefault();

  // Run all validations
  const nameOk    = validateName();
  const emailOk   = validateEmail();
  const pwOk      = validatePassword();
  const confirmOk = validateConfirm();

  // Terms checkbox
  const terms = document.getElementById('agreeTerms');
  const termsOk = terms?.checked;
  if (!termsOk) showErr('termsErr'); else hideErr('termsErr');

  if (!nameOk || !emailOk || !pwOk || !confirmOk || !termsOk) {
    // Scroll to first error
    const firstErr = document.querySelector('.form-input.error');
    firstErr?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  const fullName = document.getElementById('fullName')?.value.trim();
  const email = document.getElementById('signupEmail')?.value.trim();
  const password = document.getElementById('signupPassword')?.value;
  const country = document.getElementById('country')?.value || null;

  // All good — submit to backend
  const btn = document.getElementById('signupBtn');
  btn.classList.add('loading');
  btn.innerHTML = 'Creating your account…';
  btn.disabled = true;

  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, email, password, country })
    });
    
    const data = await res.json();
    btn.classList.remove('loading');
    btn.disabled = false;
    
    if (!res.ok) {
      btn.innerHTML = 'Create Account <i class="fa fa-arrow-right"></i>';
      window.HalalStocks?.showToast(data.detail || 'Failed to create account.', 'error');
      if (data.detail && data.detail.includes('email')) {
        showErr('signupEmailErr');
        const errEl = document.getElementById('signupEmailErr');
        if (errEl) {
          errEl.innerHTML = '<i class="fa fa-exclamation-circle"></i> This email is already registered. <a href="login.html" style="color:var(--primary)">Sign in instead?</a>';
        }
        markInput('signupEmail', false);
      }
      return;
    }
    
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      btn.innerHTML = '<i class="fa fa-check"></i> Account Created!';
      btn.style.background = 'linear-gradient(135deg,var(--primary),var(--primary-dark))';
      window.HalalStocks?.showToast('Welcome to HalalEdge! Your account is ready.', 'success');
      setTimeout(() => { window.location.href = 'index.html'; }, 1500);
    }
  } catch (err) {
    btn.classList.remove('loading');
    btn.disabled = false;
    btn.innerHTML = 'Create Account <i class="fa fa-arrow-right"></i>';
    window.HalalStocks?.showToast('Backend connection error. Is the server running?', 'error');
  }
};

// ── Real-time login field validation ──────────────────────────
document.getElementById('loginEmail')?.addEventListener('blur', validateLoginEmail);
document.getElementById('loginPassword')?.addEventListener('blur', validateLoginPassword);

// ── Signup field style updates ────────────────────────────────
document.getElementById('fullName')?.addEventListener('blur', validateName);
document.getElementById('signupEmail')?.addEventListener('blur', validateEmail);
document.getElementById('confirmPassword')?.addEventListener('blur', validateConfirm);

// ── Forgot Password Flow ──────────────────────────────────────
window.openForgotModal = function(e) {
  if (e) e.preventDefault();
  const modal = document.getElementById('forgotPasswordModal');
  if (modal) modal.style.display = 'flex';
};

window.closeForgotModal = function() {
  const modal = document.getElementById('forgotPasswordModal');
  if (modal) modal.style.display = 'none';
};

window.handleForgotPassword = async function(e) {
  e.preventDefault();
  const email = document.getElementById('forgotEmail')?.value.trim();
  if (!email) return;

  const btn = document.getElementById('forgotBtn');
  btn.disabled = true;
  btn.textContent = 'Sending…';

  try {
    const res = await fetch(`${window.HalalStocks.API_BASE}/auth/forgot-password?email=${encodeURIComponent(email)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    btn.disabled = false;
    btn.textContent = 'Send Reset Link';

    if (res.ok) {
      window.HalalStocks?.showToast('If the email exists, a reset link has been sent. Check simulated_emails.log.', 'success');
      closeForgotModal();
    } else {
      window.HalalStocks?.showToast(data.detail || 'Failed to send reset link.', 'error');
    }
  } catch (err) {
    btn.disabled = false;
    btn.textContent = 'Send Reset Link';
    window.HalalStocks?.showToast('Error connecting to backend.', 'error');
  }
};