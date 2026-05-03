(() => {
  const canvas = document.getElementById('momentumChart');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    const points = [35, 52, 47, 63, 58, 71, 69, 74, 83, 78, 88, 93];
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h); ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = '#22d3ee'; ctx.lineWidth = 4; ctx.beginPath();
    points.forEach((p, i) => { const x = (i/(points.length-1))*(w-80)+40; const y = h-(p/100)*(h-60)-30; i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
    ctx.stroke();
  }

  document.querySelectorAll('[data-copy-target]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const id = btn.getAttribute('data-copy-target');
      const target = document.getElementById(id);
      if (!target) return;
      await navigator.clipboard.writeText(target.innerText);
      btn.textContent = 'Copied';
      setTimeout(() => btn.textContent = id === 'cloudPrompt' ? 'Copy Cloud Prompt' : 'Copy Snapshot', 1200);
    });
  });

  const save = document.getElementById('saveSettings');
  if (save) {
    const dense = document.getElementById('denseMode');
    const contrast = document.getElementById('highContrast');
    const status = document.getElementById('settingsStatus');
    dense.checked = localStorage.getItem('ponder_dense') === '1';
    contrast.checked = localStorage.getItem('ponder_contrast') === '1';
    save.addEventListener('click', () => {
      localStorage.setItem('ponder_dense', dense.checked ? '1' : '0');
      localStorage.setItem('ponder_contrast', contrast.checked ? '1' : '0');
      status.textContent = 'Settings saved.';
    });
  }
})();
