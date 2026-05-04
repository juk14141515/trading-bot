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
      date: p.date || p.day || '',
      portfolio: Number(p.portfolio_value || p.equity || 0),
      buyingPower: Number(p.buying_power || 0),
      openPl: Number(p.open_pl || p.open_pnl || 0),
      drawdown: Number(p.drawdown || p.drawdown_pct || 0),
      capitalUsed: Number(p.capital_used_pct || p.capital_used || 0),
      capitalFree: Number(p.capital_free || p.free_cash || p.buying_power || 0)
    })).filter(p => p.portfolio || p.buyingPower || p.openPl);
  }

  function chartTooltip() {
    let tip = document.querySelector('.chart-tooltip');
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'chart-tooltip';
      document.body.appendChild(tip);
    }
    return tip;
  }

  function drawChart(canvas, hoverIndex = null, hoverSeries = null) {
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
      { key: 'portfolio', color: '#22c55e', label: 'Portfolio' },
      { key: 'buyingPower', color: '#93c5fd', label: 'Buying Power' },
      { key: 'openPl', color: '#f59e0b', label: 'Open P/L' }
    ];
    const all = points.flatMap(p => series.map(s => p[s.key]).filter(Number.isFinite));
    const min = Math.min(...all);
    const max = Math.max(...all);
    const span = max - min || 1;
    const px = i => pad.left + ((w - pad.left - pad.right) * i / (points.length - 1));
    const py = value => pad.top + (h - pad.top - pad.bottom) * (1 - ((value - min) / span));
    function linePath(values, key) {
      values.forEach((p, i) => {
        const x = px(i);
        const y = py(p[key]);
        if (i === 0) ctx.moveTo(x, y);
        else {
          const prevX = px(i - 1);
          const prevY = py(values[i - 1][key]);
          const midX = (prevX + x) / 2;
          ctx.quadraticCurveTo(prevX, prevY, midX, (prevY + y) / 2);
          ctx.quadraticCurveTo(midX, (prevY + y) / 2, x, y);
        }
      });
    }
    series.forEach(s => {
      ctx.strokeStyle = s.color;
      ctx.globalAlpha = hoverSeries && hoverSeries !== s.key ? 0.28 : 1;
      ctx.lineWidth = hoverSeries === s.key ? 5 : (s.key === 'openPl' ? 2 : 3);
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      if (hoverSeries === s.key) {
        ctx.shadowColor = s.color;
        ctx.shadowBlur = 14;
      } else {
        ctx.shadowBlur = 0;
      }
      ctx.beginPath();
      linePath(points, s.key);
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
    if (hoverIndex !== null && points[hoverIndex]) {
      const x = px(hoverIndex);
      ctx.strokeStyle = 'rgba(239,68,68,.75)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, pad.top);
      ctx.lineTo(x, h - pad.bottom);
      ctx.stroke();
      series.forEach(s => {
        ctx.fillStyle = s.color;
        ctx.beginPath();
        ctx.arc(x, py(points[hoverIndex][s.key]), 4, 0, Math.PI * 2);
        ctx.fill();
      });
    }
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
    canvas.__ponderChart = { points, pad, w, h };
  }

  function bindChartHover(canvas) {
    if (canvas.__ponderHoverBound) return;
    canvas.__ponderHoverBound = true;
    const tip = chartTooltip();
    canvas.addEventListener('mousemove', event => {
      const meta = canvas.__ponderChart;
      if (!meta || !meta.points || meta.points.length < 2) return;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const span = rect.width - meta.pad.left - meta.pad.right;
      const raw = Math.round(((x - meta.pad.left) / Math.max(span, 1)) * (meta.points.length - 1));
      const index = Math.max(0, Math.min(meta.points.length - 1, raw));
      const p = meta.points[index];
      const scaleY = value => {
        const values = meta.points.flatMap(point => ['portfolio','buyingPower','openPl'].map(key => point[key]).filter(Number.isFinite));
        const min = Math.min(...values);
        const max = Math.max(...values);
        const span = max - min || 1;
        return meta.pad.top + (meta.h - meta.pad.top - meta.pad.bottom) * (1 - ((value - min) / span));
      };
      const y = event.clientY - rect.top;
      const nearest = [
        ['portfolio', Math.abs(y - scaleY(p.portfolio))],
        ['buyingPower', Math.abs(y - scaleY(p.buyingPower))],
        ['openPl', Math.abs(y - scaleY(p.openPl))]
      ].sort((a, b) => a[1] - b[1])[0][0];
      const start = meta.points[0]?.portfolio || 0;
      const pctChange = start ? ((p.portfolio - start) / start) * 100 : null;
      drawChart(canvas, index, nearest);
      tip.innerHTML = `
        <strong>${p.label || p.date || `Point ${index + 1}`}</strong>
        <span><em>Portfolio</em><b>${numberLabel(p.portfolio, '$')}</b></span>
        <span><em>Buying power</em><b>${numberLabel(p.buyingPower, '$')}</b></span>
        <span><em>Open P/L</em><b>${numberLabel(p.openPl, '$')}</b></span>
        <span><em>Change from start</em><b>${pctChange === null ? 'unknown' : numberLabel(pctChange) + '%'}</b></span>
        <span><em>Drawdown</em><b>${numberLabel(p.drawdown)}%</b></span>
        <span><em>Capital used</em><b>${numberLabel(p.capitalUsed)}%</b></span>
        <span><em>Capital free</em><b>${numberLabel(p.capitalFree, '$')}</b></span>
      `;
      tip.style.display = 'block';
      tip.style.left = Math.min(event.clientX + 16, window.innerWidth - 300) + 'px';
      tip.style.top = Math.min(event.clientY + 16, window.innerHeight - 240) + 'px';
    });
    canvas.addEventListener('mouseleave', () => {
      tip.style.display = 'none';
      drawChart(canvas);
    });
  }

  function drawCharts() {
    document.querySelectorAll('canvas[data-chart="equity"]').forEach(canvas => {
      drawChart(canvas);
      bindChartHover(canvas);
    });
  }

  refreshDashboard();
  setInterval(refreshDashboard, 15000);
  drawCharts();
  window.addEventListener('resize', () => {
    clearTimeout(window.__ponderChartTimer);
    window.__ponderChartTimer = setTimeout(drawCharts, 150);
  });
})();
