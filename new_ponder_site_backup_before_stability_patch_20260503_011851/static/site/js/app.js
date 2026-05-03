async function getJson(path) {
  const r = await fetch(path + '?ts=' + Date.now(), { cache: 'no-store' });
  return r.ok ? await r.json() : {};
}

function esc(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }[c]));
}

function money(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }) : '--';
}

function pct(v) {
  const n = Number(v);
  return Number.isFinite(n) ? `${n.toFixed(1)}%` : '--';
}

function num(v, digits = 1) {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(digits) : '--';
}

function card(title, value, note = '', tone = '') {
  return `<article class="card ${tone}"><h3>${esc(title)}</h3><div class="big">${esc(value ?? '--')}</div><p class="muted">${esc(note)}</p></article>`;
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? '';
}

function cleanLabel(value) {
  return String(value ?? '--').replace(/[^\w\s./%-]/g, '').replace(/\s+/g, ' ').trim() || '--';
}

function renderChart(history) {
  const svg = document.getElementById('capitalChart');
  if (!svg) return;
  const points = (history || [])
    .map(x => ({ t: x.timestamp, equity: Number(x.portfolio_value ?? x.equity), openPl: Number(x.open_pl ?? 0) }))
    .filter(x => Number.isFinite(x.equity));

  if (points.length < 2) {
    svg.innerHTML = '<text x="24" y="92" fill="#a8b3c7">Waiting for more capital history.</text>';
    return;
  }

  const width = 640;
  const height = 180;
  const pad = 16;
  const values = points.map(x => x.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1);
  const path = points.map((p, i) => {
    const x = pad + (i / Math.max(points.length - 1, 1)) * (width - pad * 2);
    const y = height - pad - ((p.equity - min) / span) * (height - pad * 2);
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(' ');

  svg.innerHTML = `
    <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" class="chart-axis"></line>
    <path d="${path}" class="chart-line"></path>
    <circle cx="${width - pad}" cy="${height - pad - ((points.at(-1).equity - min) / span) * (height - pad * 2)}" r="4" class="chart-dot"></circle>
  `;
}

function rows(items) {
  if (!items || !items.length) {
    return '<tr><td colspan="4" class="muted">No scanner candidates yet.</td></tr>';
  }
  return items.map(x => `
    <tr>
      <td><strong>${esc(x.symbol)}</strong></td>
      <td>${num(x.final_score)}</td>
      <td>${num(x.entry_score, 0)} <span class="muted">${esc(cleanLabel(x.entry_zone))}</span></td>
      <td>${esc(cleanLabel(x.label))}</td>
    </tr>
  `).join('');
}

function renderRotation(item) {
  if (!item || !item.buy_symbol) return '<p class="muted">No rotation suggestion yet.</p>';
  const why = (item.why || []).slice(0, 4).map(x => `<li>${esc(cleanLabel(x))}</li>`).join('');
  return `
    <div class="callout">
      <strong>${esc(item.sell_symbol)} to ${esc(item.buy_symbol)}</strong>
      <span>${esc(cleanLabel(item.action))}</span>
    </div>
    <div class="metric-row stacked">
      <span>Score <strong>${num(item.rotation_score)}</strong></span>
      <span>Edge <strong>${num(item.expected_edge)}</strong></span>
      <span>Confidence <strong>${esc(item.confidence || '--')}</strong></span>
    </div>
    <ul>${why}</ul>
  `;
}

function renderSell(item) {
  if (!item || !item.symbol) return '<p class="muted">No sell pressure candidate yet.</p>';
  const reasons = (item.reasons || []).slice(0, 4).map(x => `<li>${esc(cleanLabel(x))}</li>`).join('');
  return `
    <div class="callout">
      <strong>${esc(item.symbol)}</strong>
      <span>${esc(cleanLabel(item.verdict))}</span>
    </div>
    <div class="metric-row stacked">
      <span>Price <strong>${money(item.price)}</strong></span>
      <span>Pressure <strong>${num(item.sell_pressure, 0)}</strong></span>
      <span>Pullback <strong>${pct(item.pullback_from_high_pct)}</strong></span>
    </div>
    <ul>${reasons || '<li class="muted">No sell reasons listed.</li>'}</ul>
  `;
}

function renderShadow(item) {
  if (!item || !item.buy_symbol) return '<p class="muted">No shadow allocation yet.</p>';
  return `
    <div class="callout">
      <strong>${esc(item.sell_symbol)} to ${esc(item.buy_symbol)}</strong>
      <span>${esc(cleanLabel(item.recommendation))}</span>
    </div>
    <div class="metric-row stacked">
      <span>Allocation <strong>${pct(item.shadow_allocation_pct)}</strong></span>
      <span>Score <strong>${num(item.rotation_score)}</strong></span>
      <span>Edge <strong>${num(item.expected_edge)}</strong></span>
    </div>
  `;
}

function actionItems(data) {
  const items = data.ai?.action_items || [];
  const botReason = data.bot?.why_not_trading;
  const capitalAction = data.capital?.next_money_action;
  return [botReason, capitalAction, ...items].filter(Boolean).slice(0, 8);
}

async function loadOverview() {
  const data = await getJson('/api/dashboard-data');
  const bot = data.bot || {};
  const capital = data.capital || {};
  const market = data.market || {};
  const alerts = data.alerts || {};
  const rotation = data.top_rotation || {};
  const sell = data.top_exit || {};
  const shadow = data.top_shadow || {};

  setText('lastUpdated', `Updated ${bot.status_updated_at || capital.updated_at || market.updated_at || 'unknown'}`);
  setText('tradingState', cleanLabel(bot.trading_state || market.status || 'unknown'));
  setText('marketTrend', cleanLabel(bot.market_trend || rotation.regime || 'unknown'));
  setText('whyNotTrading', bot.why_not_trading || 'Waiting for bot status.');
  setText('lastSkipReason', bot.last_skip_reason || '');
  setText('capitalMode', cleanLabel(capital.capital_mode || capital.capital_efficiency || 'unknown'));
  setText('portfolioValue', money(capital.portfolio_value || capital.equity));
  setText('openPl', money(capital.open_pl));
  setText('capitalUsed', pct(capital.capital_used_pct));
  setText('scannerCount', String((data.scanner_top || []).length));
  setText('rotationStatus', cleanLabel(rotation.status || data.rotation_suggestions?.[0]?.status || 'research'));
  setText('sellPressure', sell.sell_pressure == null ? '--' : num(sell.sell_pressure, 0));
  setText('shadowConfidence', shadow.confidence || '--');

  const overview = document.getElementById('overviewCards');
  if (overview) {
    overview.innerHTML = [
      card('Bot State', cleanLabel(bot.trading_state || 'unknown'), bot.why_not_trading || ''),
      card('Portfolio', money(capital.portfolio_value || capital.equity), `${pct(capital.capital_used_pct)} deployed`),
      card('Top Scanner', data.scanner_top?.[0]?.symbol || '--', `score ${num(data.scanner_top?.[0]?.final_score)}`),
      card('Top Rotation', rotation.buy_symbol ? `${rotation.sell_symbol} to ${rotation.buy_symbol}` : '--', cleanLabel(rotation.action || rotation.confidence)),
      card('Sell Watch', sell.symbol || '--', `pressure ${sell.sell_pressure ?? '--'}`),
      card('Alerts', alerts.summary?.total ?? 0, `${alerts.summary?.critical ?? 0} critical`)
    ].join('');
  }

  const scannerRows = document.getElementById('scannerRows');
  if (scannerRows) scannerRows.innerHTML = rows(data.scanner_top || []);

  const rotationCard = document.getElementById('rotationCard');
  if (rotationCard) rotationCard.innerHTML = renderRotation(rotation);

  const sellCard = document.getElementById('sellCard');
  if (sellCard) sellCard.innerHTML = renderSell(sell);

  const shadowCard = document.getElementById('shadowCard');
  if (shadowCard) shadowCard.innerHTML = renderShadow(shadow);

  const actions = document.getElementById('actionItems');
  if (actions) {
    const items = actionItems(data);
    actions.innerHTML = items.length ? items.map(x => `<li>${esc(cleanLabel(x))}</li>`).join('') : '<li class="muted">No action items yet.</li>';
  }

  renderChart(data.capital_history || capital.history || []);
  window.__ponderDebug = data;
}

async function openPonder() {
  const p = document.getElementById('ponderPanel');
  if (!p) return;
  const data = window.__ponderDebug || await getJson('/api/dashboard-data');
  p.style.display = p.style.display === 'block' ? 'none' : 'block';
  p.innerHTML = `<h2>Ask Ponder</h2>
    <button data-q="why">Why no trade?</button>
    <button data-q="action">What should I do?</button>
    <button data-q="risk">Biggest risk?</button>
    <div id="ponderAnswer" class="assistant-answer">Select a question.</div>`;
  p.querySelectorAll('[data-q]').forEach(b => b.onclick = () => {
    const answers = {
      why: [data.bot?.why_not_trading, data.bot?.last_skip_reason].filter(Boolean),
      action: actionItems(data),
      risk: [
        data.top_exit?.symbol ? `${data.top_exit.symbol}: sell pressure ${data.top_exit.sell_pressure}` : '',
        data.capital?.next_money_action || ''
      ].filter(Boolean)
    };
    const items = answers[b.dataset.q] || ['No answer yet.'];
    document.getElementById('ponderAnswer').innerHTML = '<ul>' + items.map(x => `<li>${esc(cleanLabel(x))}</li>`).join('') + '</ul>';
  });
}

function copyDebug() {
  const data = window.__ponderDebug || {};
  const snapshot = {
    time: new Date().toISOString(),
    bot: data.bot,
    capital: data.capital,
    topScanner: data.scanner_top?.[0],
    topRotation: data.top_rotation,
    topExit: data.top_exit,
    topShadow: data.top_shadow
  };
  navigator.clipboard.writeText(JSON.stringify(snapshot, null, 2));
}

document.getElementById('ponderAssistantBtn')?.addEventListener('click', openPonder);
loadOverview();
setInterval(loadOverview, 45000);
