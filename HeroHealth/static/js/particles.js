document.addEventListener('DOMContentLoaded', () => {
  const section = document.querySelector('.particles-section');
  const canvas = section.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  let W, H, DPR;

  function resize(){
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = section.clientWidth;
    H = section.clientHeight;
    canvas.width = W * DPR;
    canvas.height = H * DPR;
    ctx.setTransform(DPR,0,0,DPR,0,0);
    buildParticles();
  }

  function rand(a, b){ return a + Math.random() * (b - a); }

  let particles = [];
  let mouse = { x: -9999, y: -9999, active: false };
  let targetCount = 0;

  function spawnParticle(forceAge){
    return {
      x: Math.random() * W, y: Math.random() * H,
      vx: rand(-0.45, 0.45), vy: rand(-0.45, 0.45),
      r: rand(1.1, 2.4), baseR: 0, glow: 0,
      age: forceAge !== undefined ? forceAge : 0,
      life: rand(9000, 18000),
      fadeIn: rand(800, 1600),
      fadeOut: rand(1800, 3200),
      shade: rand(-0.25, 0.25)
    };
  }

  function buildParticles(){
    particles = [];
    targetCount = Math.round((W * H) / 1000);
    for (let i = 0; i < targetCount; i++){
      const p = spawnParticle(rand(0, 12000));
      p.baseR = p.r;
      particles.push(p);
    }
  }

  function shadeColor(shade){
    const base = [0, 242, 254];
    const lift = shade > 0 ? shade : 0;
    const drop = shade < 0 ? -shade : 0;
    const r = Math.min(255, base[0] + lift * 60);
    const g = Math.min(255, base[1] + lift * 90 - drop * 40);
    const b = Math.max(0, base[2] + lift * 40);
    return `${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)}`;
  }

  document.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const isOver = e.clientX >= rect.left && e.clientX <= rect.right && 
                   e.clientY >= rect.top && e.clientY <= rect.bottom;
    if (isOver) {
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
      mouse.active = true;
    } else {
      mouse.active = false;
    }
  });
  document.addEventListener('mouseleave', () => { mouse.active = false; });
  document.addEventListener('touchmove', (e) => {
    const t = e.touches[0];
    if (!t) return;
    const rect = canvas.getBoundingClientRect();
    const isOver = t.clientX >= rect.left && t.clientX <= rect.right && 
                   t.clientY >= rect.top && t.clientY <= rect.bottom;
    if (isOver) {
      mouse.x = t.clientX - rect.left;
      mouse.y = t.clientY - rect.top;
      mouse.active = true;
    } else {
      mouse.active = false;
    }
  }, { passive: true });
  document.addEventListener('touchend', () => { mouse.active = false; });

  const HOVER_RADIUS = 170, LINK_DIST = 45, ATTRACT = 0.25, FRICTION = 0.975;
  let lastTime = performance.now();

  function step(now){
    const dt = Math.min(50, now - lastTime);
    lastTime = now;

    for (let i = 0; i < particles.length; i++){
      const p = particles[i];
      p.age += dt;

      if (p.age >= p.life){
        particles[i] = spawnParticle(0);
        particles[i].baseR = particles[i].r;
        continue;
      }

      let lifeAlpha = 1;
      if (p.age < p.fadeIn) lifeAlpha = p.age / p.fadeIn;
      else if (p.age > p.life - p.fadeOut) lifeAlpha = Math.max(0, (p.life - p.age) / p.fadeOut);
      p.lifeAlpha = lifeAlpha;

      p.x += p.vx; p.y += p.vy;
      if (p.x < -10) p.x = W + 10;
      if (p.x > W + 10) p.x = -10;
      if (p.y < -10) p.y = H + 10;
      if (p.y > H + 10) p.y = -10;

      let targetGlow = 0;
      if (mouse.active){
        const dx = mouse.x - p.x, dy = mouse.y - p.y;
        const dist = Math.sqrt(dx*dx + dy*dy) || 0.0001;
        if (dist < HOVER_RADIUS){
          const pull = (1 - dist / HOVER_RADIUS);
          p.vx += (dx / dist) * pull * ATTRACT * 0.05;
          p.vy += (dy / dist) * pull * ATTRACT * 0.05;
          targetGlow = pull;
        }
      }

      p.glow += (targetGlow - p.glow) * 0.12;
      p.r = p.baseR + p.glow * 2.2;
      p.vx *= FRICTION; p.vy *= FRICTION;
      const speed = Math.sqrt(p.vx*p.vx + p.vy*p.vy);
      if (speed < 0.05){
        const a = Math.atan2(p.vy, p.vx) || rand(0, Math.PI*2);
        p.vx += Math.cos(a) * 0.01;
        p.vy += Math.sin(a) * 0.01;
      }
    }
  }

  function draw(){
    ctx.clearRect(0, 0, W, H);

    for (let i = 0; i < particles.length; i++){
      const a = particles[i];
      for (let j = i + 1; j < particles.length; j++){
        const b = particles[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < LINK_DIST){
          const lifeMin = Math.min(a.lifeAlpha ?? 1, b.lifeAlpha ?? 1);
          const alpha = (1 - dist / LINK_DIST) * 0.25 * (0.4 + Math.max(a.glow, b.glow)) * lifeMin;
          if (alpha <= 0.01) continue;
          ctx.strokeStyle = `rgba(0, 242, 254, ${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }

    if (mouse.active){
      for (const p of particles){
        const dx = p.x - mouse.x, dy = p.y - mouse.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < HOVER_RADIUS){
          const alpha = (1 - dist / HOVER_RADIUS) * 0.35 * (p.lifeAlpha ?? 1);
          ctx.strokeStyle = `rgba(0, 242, 254, ${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
        }
      }
    }

    for (const p of particles){
      const life = p.lifeAlpha ?? 1;
      if (life <= 0.01) continue;
      const base = (0.5 + p.glow * 0.5) * life;
      const tint = shadeColor(p.shade);
      ctx.fillStyle = `rgba(${tint}, ${Math.min(1, base)})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();

      if (p.glow > 0.05){
        ctx.beginPath();
        ctx.fillStyle = `rgba(${tint}, ${p.glow * 0.15 * life})`;
        ctx.arc(p.x, p.y, p.r + p.glow * 6, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    if (mouse.active){
      const grad = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, HOVER_RADIUS);
      grad.addColorStop(0, 'rgba(0, 242, 254, 0.07)');
      grad.addColorStop(1, 'rgba(0, 242, 254, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(mouse.x, mouse.y, HOVER_RADIUS, 0, Math.PI * 2); ctx.fill();
    }
  }

  function loop(now){ step(now); draw(); requestAnimationFrame(loop); }

  window.addEventListener('resize', resize);
  resize();
  lastTime = performance.now();
  requestAnimationFrame(loop);
});