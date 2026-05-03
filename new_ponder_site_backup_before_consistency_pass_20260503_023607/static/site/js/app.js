(function () {
  const root = document.documentElement;
  const saved = JSON.parse(localStorage.getItem('ponderUi') || '{}');

  function applySettings(settings) {
    root.dataset.theme = settings.theme || 'black';
    root.dataset.colorblind = settings.colorblind ? 'true' : 'false';
    root.dataset.motion = settings.motion || 'calm';
    root.dataset.density = settings.density || 'normal';
  }

  window.ponderSettings = {
    get: () => JSON.parse(localStorage.getItem('ponderUi') || '{}'),
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

  applySettings(saved);

  window.copyPonderSnapshot = async function () {
    const r = await fetch('/api/snapshot', { cache: 'no-store' });
    const data = await r.json();
    await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    alert('Snapshot copied.');
  };

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

  refreshDashboard();
  setInterval(refreshDashboard, 15000);
})();
