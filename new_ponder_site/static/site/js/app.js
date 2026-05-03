(function () {
  const root = document.documentElement;
  const defaults = { theme: 'black', colorblind: true, motion: 'calm', density: 'normal' };

  function readSettings() {
    try {
      return Object.assign({}, defaults, JSON.parse(localStorage.getItem('ponderUi') || '{}'));
    } catch (_) {
      return Object.assign({}, defaults);
    }
  }

  function applySettings(settings) {
    const next = Object.assign({}, defaults, settings || {});
    root.dataset.theme = next.theme;
    root.dataset.colorblind = next.colorblind ? 'true' : 'false';
    root.dataset.motion = next.motion;
    root.dataset.density = next.density;
    updateSettingButtons(next);
  }

  function updateSettingButtons(settings) {
    document.querySelectorAll('[data-setting]').forEach(btn => {
      const [key, raw] = btn.dataset.setting.split(':');
      const value = raw === 'true' ? true : raw === 'false' ? false : raw;
      btn.classList.toggle('is-active', settings[key] === value);
    });
    const status = document.getElementById('settingsStatus');
    if (status) {
      status.textContent = `Active: ${settings.theme} theme, colorblind markers ${settings.colorblind ? 'on' : 'off'}, ${settings.motion} motion, ${settings.density} density.`;
    }
  }

  window.ponderSettings = {
    get: readSettings,
    set: (patch) => {
      const next = Object.assign({}, window.ponderSettings.get(), patch);
      localStorage.setItem('ponderUi', JSON.stringify(next));
      applySettings(next);
    },
    reset: () => {
      localStorage.removeItem('ponderUi');
      applySettings({});
    }
  };

  applySettings(readSettings());

  window.copyPonderSnapshot = async function () {
    try {
      const r = await fetch('/api/snapshot', { cache: 'no-store' });
      const data = await r.json();
      const text = JSON.stringify(data, null, 2);
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const box = document.createElement('textarea');
        box.value = text;
        box.style.position = 'fixed';
        box.style.left = '-9999px';
        document.body.appendChild(box);
        box.focus();
        box.select();
        document.execCommand('copy');
        box.remove();
      }
      alert('Snapshot copied.');
    } catch (err) {
      alert('Snapshot copy failed. Open the Snapshot page and copy manually.');
    }
  };

  function numberLabel(value, prefix = '') {
    if (value === undefined || value === null || value === '') return 'unknown';
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    return prefix + n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }

  async function refreshDashboard() {
    const fields = document.querySelectorAll('[data-live-field]');
    if (!fields.length) return;
    const r = await fetch('/api/dashboard-data', { cache: 'no-store' });
    if (!r.ok) return;
    const data = await r.json();
    const map = {
      bot_state: data.bot?.trading_state,
      why_not_trading: data.bot?.why_not_trading,
      portfolio_value: data.capital?.portfolio_value || data.capital?.equity,
      capital_used_pct: data.capital?.capital_used_pct,
      top_scanner: data.scanner_top?.[0]?.symbol,
      top_scanner_score: data.scanner_top?.[0]?.final_score,
      module_count: data.module_health?.filter(x => x.status === 'online').length
    };
    fields.forEach(el => {
      const value = map[el.dataset.liveField];
      if (value !== undefined && value !== null) el.textContent = value;
    });
  }

  function normalizePoints(points) {
    return (points || []).map((p, index) => ({
      x: index,
      label: p.timestamp || p.time || '',
      portfolio: Number(p.portfolio_value || p.equity || 0),
      buyingPower: Number(p.buying_power || 0),
      openPl: Number(p.open_pl || 0)
    })).filter(p => p.portfolio || p.buyingPower || p.openPl);
  }

  function drawChart(canvas) {
    const points = normalizePoints(JSON.parse(canvas.dataset.points || '[]'));
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(320, rect.width) * dpr;
    canvas.height = Math.max(260, rect.height) * dpr;
    ctx.scale(dpr, dpr);
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#020617';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(156,199,255,.16)';
    ctx.lineWidth = 1;
    const pad = { left: 54, right: 24, top: 24, bottom: 42 };
    for (let i = 0; i < 5; i++) {
      const y = pad.top + ((h - pad.top - pad.bottom) * i / 4);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(w - pad.right, y);
      ctx.stroke();
    }
    if (points.length < 2) {
      ctx.fillStyle = '#a8b3c7';
      ctx.font = '16px system-ui';
      ctx.fillText('Waiting for more chart data.', pad.left, h / 2);
      return;
    }
    const series = [
      { key: 'portfolio', color: '#93c5fd', label: 'Portfolio' },
      { key: 'buyingPower', color: '#f9a8d4', label: 'Buying Power' },
      { key: 'openPl', color: '#fbbf24', label: 'Open P/L' }
    ];
    const all = points.flatMap(p => series.map(s => p[s.key]).filter(Number.isFinite));
    const min = Math.min(...all);
    const max = Math.max(...all);
    const span = max - min || 1;
    const px = i => pad.left + ((w - pad.left - pad.right) * i / (points.length - 1));
    const py = value => pad.top + (h - pad.top - pad.bottom) * (1 - ((value - min) / span));
    series.forEach(s => {
      ctx.strokeStyle = s.color;
      ctx.lineWidth = s.key === 'openPl' ? 2 : 3;
      ctx.beginPath();
      points.forEach((p, i) => {
        const y = py(p[s.key]);
        if (i === 0) ctx.moveTo(px(i), y);
        else ctx.lineTo(px(i), y);
      });
      ctx.stroke();
    });
    ctx.fillStyle = '#dbeafe';
    ctx.font = '13px system-ui';
    series.forEach((s, i) => {
      ctx.fillStyle = s.color;
      ctx.fillRect(pad.left + i * 130, 8, 18, 4);
      ctx.fillStyle = '#cbd5e1';
      ctx.fillText(s.label, pad.left + 24 + i * 130, 14);
    });
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(numberLabel(max, '$'), 8, pad.top + 6);
    ctx.fillText(numberLabel(min, '$'), 8, h - pad.bottom);
  }

  function drawCharts() {
    document.querySelectorAll('canvas[data-chart="equity"]').forEach(drawChart);
  }

  refreshDashboard();
  setInterval(refreshDashboard, 15000);
  drawCharts();
  window.addEventListener('resize', () => {
    clearTimeout(window.__ponderChartTimer);
    window.__ponderChartTimer = setTimeout(drawCharts, 150);
  });
})();
