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

  function ensureChartFrame(canvas) {
    if (canvas.parentElement && canvas.parentElement.classList.contains('chart-frame')) {
      return canvas.parentElement;
    }
    const frame = document.createElement('div');
    frame.className = 'chart-frame';
    canvas.parentNode.insertBefore(frame, canvas);
    frame.appendChild(canvas);
    return frame;
  }

  function chartData(points) {
    const labels = points.map((p, i) => p.label || p.date || `Point ${i + 1}`);
    return {
      labels,
      datasets: [
        {
          label: 'Portfolio Value',
          data: points.map(p => p.portfolio),
          borderColor: '#22c55e',
          backgroundColor: 'rgba(34,197,94,.10)',
          tension: 0.36,
          fill: true,
          yAxisID: 'dollars',
          pointRadius: 0,
          pointHoverRadius: 4
        },
        {
          label: 'Open P/L',
          data: points.map(p => p.openPl),
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245,158,11,.08)',
          tension: 0.36,
          yAxisID: 'dollars',
          pointRadius: 0,
          pointHoverRadius: 4
        },
        {
          label: 'Capital Used %',
          data: points.map(p => p.capitalUsed),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239,68,68,.08)',
          tension: 0.36,
          yAxisID: 'percent',
          pointRadius: 0,
          pointHoverRadius: 4
        }
      ]
    };
  }

  function renderChartJs(canvas, points) {
    if (!window.Chart) return false;
    const frame = ensureChartFrame(canvas);
    if (canvas.__ponderChartJs) {
      canvas.__ponderChartJs.data = chartData(points);
      canvas.__ponderChartJs.update('none');
      return true;
    }
    const grid = 'rgba(148,163,184,.14)';
    canvas.__ponderChartJs = new Chart(canvas, {
      type: 'line',
      data: chartData(points),
      options: {
        responsive: true,
        maintainAspectRatio: false,
        resizeDelay: 200,
        animation: { duration: 650, easing: 'easeOutQuart' },
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: {
            display: true,
            labels: { color: '#cbd5e1', usePointStyle: true, boxWidth: 8, boxHeight: 8 }
          },
          tooltip: {
            backgroundColor: 'rgba(5,5,7,.96)',
            borderColor: 'rgba(239,68,68,.45)',
            borderWidth: 1,
            titleColor: '#fee2e2',
            bodyColor: '#e5e7eb',
            padding: 12,
            displayColors: true,
            callbacks: {
              title: items => items[0]?.label || 'Point',
              label: item => {
                const suffix = item.dataset.yAxisID === 'percent' ? '%' : '';
                const prefix = item.dataset.yAxisID === 'dollars' ? '$' : '';
                return `${item.dataset.label}: ${numberLabel(item.parsed.y, prefix)}${suffix}`;
              },
              afterBody: items => {
                const p = points[items[0]?.dataIndex || 0];
                const start = points[0]?.portfolio || 0;
                const pct = start ? ((p.portfolio - start) / start) * 100 : null;
                return [`Change from start: ${pct === null ? 'unknown' : numberLabel(pct) + '%'}`];
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: '#94a3b8', maxTicksLimit: 6 }, grid: { color: grid } },
          dollars: { type: 'linear', position: 'left', ticks: { color: '#94a3b8' }, grid: { color: grid } },
          percent: { type: 'linear', position: 'right', ticks: { color: '#fca5a5' }, grid: { drawOnChartArea: false } }
        }
      }
    });
    frame.__ponderChartCanvas = canvas;
    return true;
  }

  function drawChart(canvas, hoverIndex = null, hoverSeries = null) {
    const points = normalizePoints(JSON.parse(canvas.dataset.points || '[]'));
    if (renderChartJs(canvas, points)) return;
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

  function drawSparklines() {
    document.querySelectorAll('canvas[data-sparkline]').forEach(canvas => {
      if (!window.Chart) return;
      const points = normalizePoints(JSON.parse(canvas.dataset.points || '[]'));
      if (points.length < 2) return;
      const key = canvas.dataset.sparkline;
      const color = key === 'openPl' ? '#f59e0b' : key === 'buyingPower' ? '#93c5fd' : '#22c55e';
      if (canvas.__sparkChart) {
        canvas.__sparkChart.data.labels = points.map((_, i) => i + 1);
        canvas.__sparkChart.data.datasets[0].data = points.map(p => p[key]);
        canvas.__sparkChart.update('none');
        return;
      }
      canvas.__sparkChart = new Chart(canvas, {
        type: 'line',
        data: {
          labels: points.map((_, i) => i + 1),
          datasets: [{ data: points.map(p => p[key]), borderColor: color, backgroundColor: 'transparent', tension: .35, pointRadius: 0, borderWidth: 2 }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          resizeDelay: 200,
          animation: { duration: 500 },
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false } }
        }
      });
    });
  }

  function initTradingViewPanels() {
    document.querySelectorAll('[data-tv-chart]').forEach(el => {
      if (el.__ponderTv || !window.LightweightCharts) return;
      el.__ponderTv = true;
      const chart = LightweightCharts.createChart(el, {
        autoSize: true,
        layout: { background: { color: '#050507' }, textColor: '#94a3b8' },
        grid: { vertLines: { color: 'rgba(148,163,184,.12)' }, horzLines: { color: 'rgba(148,163,184,.12)' } },
        rightPriceScale: { borderColor: 'rgba(148,163,184,.18)' },
        timeScale: { borderColor: 'rgba(148,163,184,.18)' },
        crosshair: { mode: 1 }
      });
      el.__ponderTvChart = chart;
      chart.timeScale().fitContent();
    });
  }

  function initExpandablePanels() {
    document.querySelectorAll('[data-expandable]').forEach(panel => {
      if (panel.__ponderExpandable) return;
      panel.__ponderExpandable = true;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'expand-button';
      button.innerHTML = '<i data-lucide="maximize-2"></i><span>Expand</span>';
      button.addEventListener('click', () => {
        const open = panel.classList.toggle(panel.dataset.expandable === 'chart' ? 'is-chart-full' : 'is-expanded-panel');
        panel.querySelectorAll('.chart-frame').forEach(frame => frame.classList.toggle('chart-expanded', open));
        button.innerHTML = open ? '<i data-lucide="minimize-2"></i><span>Collapse</span>' : '<i data-lucide="maximize-2"></i><span>Expand</span>';
        if (window.lucide) lucide.createIcons({ attrs: { width: 16, height: 16, strokeWidth: 2 } });
        setTimeout(() => {
          panel.querySelectorAll('canvas').forEach(canvas => {
            if (canvas.__ponderChartJs) canvas.__ponderChartJs.resize();
            if (canvas.__sparkChart) canvas.__sparkChart.resize();
          });
          panel.querySelectorAll('[data-tv-chart]').forEach(el => {
            if (el.__ponderTvChart && el.parentElement) {
              el.__ponderTvChart.resize(el.parentElement.clientWidth, el.parentElement.clientHeight);
            }
          });
        }, 240);
      });
      const head = panel.querySelector('.card-head');
      if (head) head.appendChild(button);
      else panel.insertBefore(button, panel.firstChild);
    });
  }

  function resizeExistingCharts() {
    document.querySelectorAll('canvas').forEach(canvas => {
      if (canvas.__ponderChartJs) canvas.__ponderChartJs.resize();
      if (canvas.__sparkChart) canvas.__sparkChart.resize();
    });
    document.querySelectorAll('[data-tv-chart]').forEach(el => {
      if (el.__ponderTvChart && el.parentElement) {
        el.__ponderTvChart.resize(el.parentElement.clientWidth, el.parentElement.clientHeight);
      }
    });
  }

  refreshDashboard();
  setInterval(refreshDashboard, 15000);
  document.documentElement.classList.add('fade-in-ready');
  document.querySelectorAll('.health-online, .status-pill').forEach((el, index) => {
    if (index < 3) el.classList.add('ai-pulse');
  });
  initExpandablePanels();
  if (window.lucide) lucide.createIcons({ attrs: { width: 18, height: 18, strokeWidth: 2 } });
  initTradingViewPanels();
  drawCharts();
  drawSparklines();
  window.addEventListener('resize', () => {
    clearTimeout(window.__ponderChartTimer);
    window.__ponderChartTimer = setTimeout(resizeExistingCharts, 200);
  });
})();
