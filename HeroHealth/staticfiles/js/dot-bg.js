(function () {
  const SPACING = 14, DOT_RADIUS = 0.75
  const INTERACTION_RADIUS = 120, SHAPE_RADIUS = 38
  const SPRING = 0.09, DAMPING = 0.74, DRIFT_MAX = 3.5

  function hexPoints(cx, cy, r, angle) {
    const pts = []
    for (let i = 0; i < 6; i++) {
      const a = angle + (Math.PI * 2 * i) / 6 - Math.PI / 2
      pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r])
    }
    return pts
  }

  function sampleShape(pts, count) {
    const result = [], perSeg = Math.ceil(count / pts.length)
    for (let s = 0; s < pts.length; s++) {
      const [x1, y1] = pts[s], [x2, y2] = pts[(s + 1) % pts.length]
      for (let i = 0; i < perSeg; i++)
        result.push([x1 + (x2 - x1) * (i / perSeg), y1 + (y2 - y1) * (i / perSeg)])
    }
    return result.slice(0, count)
  }

  function init(canvas) {
    const ctx = canvas.getContext('2d')
    let dots = [], mouse = { x: -9999, y: -9999, active: false }, angle = 0, raf

    function build() {
      dots = []
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
      const cols = Math.ceil(canvas.width / SPACING) + 2
      const rows = Math.ceil(canvas.height / SPACING) + 2
      for (let r = 0; r < rows; r++)
        for (let c = 0; c < cols; c++) {
          const x = c * SPACING, y = r * SPACING
          dots.push({ x, y, homeX: x, homeY: y, vx: 0, vy: 0,
            driftAmp: 1 + Math.random() * DRIFT_MAX,
            driftFreqX: 0.0003 + Math.random() * 0.0004,
            driftFreqY: 0.0003 + Math.random() * 0.0004,
            driftPhaseX: Math.random() * Math.PI * 2,
            driftPhaseY: Math.random() * Math.PI * 2,
          })
        }
    }

    function draw(time) {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      angle += 0.006
      const { x: mx, y: my, active } = mouse
      const shapePts = hexPoints(mx, my, SHAPE_RADIUS, angle)
      const inRange = dots.reduce((acc, d, i) => {
        if (active && Math.hypot(d.homeX - mx, d.homeY - my) < INTERACTION_RADIUS) acc.push(i)
        return acc
      }, [])
      const targets = sampleShape(shapePts, inRange.length)
      inRange.sort((a, b) => Math.atan2(dots[a].homeY - my, dots[a].homeX - mx) - Math.atan2(dots[b].homeY - my, dots[b].homeX - mx))
      const assigned = new Map(inRange.map((idx, i) => [idx, targets[i]]))

      dots.forEach((d, i) => {
        let tx = d.homeX, ty = d.homeY, blend = 0
        if (active && assigned.has(i)) {
          const [ax, ay] = assigned.get(i)
          blend = Math.max(0, 1 - Math.hypot(d.homeX - mx, d.homeY - my) / INTERACTION_RADIUS)
          tx = d.homeX + (ax - d.homeX) * blend
          ty = d.homeY + (ay - d.homeY) * blend
        } else {
          tx = d.homeX + Math.sin(time * d.driftFreqX + d.driftPhaseX) * d.driftAmp
          ty = d.homeY + Math.sin(time * d.driftFreqY + d.driftPhaseY) * d.driftAmp
        }
        d.vx = (d.vx + (tx - d.x) * SPRING) * DAMPING
        d.vy = (d.vy + (ty - d.y) * SPRING) * DAMPING
        d.x += d.vx; d.y += d.vy

        const alpha = 0.3 + blend * 0.6
        if (blend > 0.12) {
          const h = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, DOT_RADIUS * 7)
          h.addColorStop(0, `rgba(0, 242, 254, ${0.4 * blend})`)
          h.addColorStop(1, 'rgba(0, 242, 254, 0)')
          ctx.beginPath(); ctx.arc(d.x, d.y, DOT_RADIUS * 7, 0, Math.PI * 2)
          ctx.fillStyle = h; ctx.fill()
        }
        const g = ctx.createRadialGradient(d.x - DOT_RADIUS * 0.35, d.y - DOT_RADIUS * 0.35, 0, d.x, d.y, DOT_RADIUS)
        g.addColorStop(0, `rgba(0, 242, 254, ${alpha})`)
        g.addColorStop(0.6, `rgba(79, 172, 254, ${alpha})`)
        g.addColorStop(1, `rgba(0, 120, 255, ${alpha * 0.75})`)
        ctx.beginPath(); ctx.arc(d.x, d.y, DOT_RADIUS, 0, Math.PI * 2)
        ctx.fillStyle = g; ctx.fill()
      })
      raf = requestAnimationFrame(draw)
    }

    // Listen to document level mouse events so they work even when hovering over content
    document.addEventListener('mousemove', e => {
      const r = canvas.getBoundingClientRect()
      const isOverCanvas = e.clientX >= r.left && e.clientX <= r.right && 
                           e.clientY >= r.top && e.clientY <= r.bottom
      if (isOverCanvas) {
        mouse = { x: e.clientX - r.left, y: e.clientY - r.top, active: true }
      } else {
        mouse = { x: -9999, y: -9999, active: false }
      }
    })
    document.addEventListener('mouseleave', () => { mouse = { x: -9999, y: -9999, active: false } })
    window.addEventListener('resize', build)
    build()
    raf = requestAnimationFrame(draw)
  }

  document.addEventListener('DOMContentLoaded', () => {
    const canvases = document.querySelectorAll('.dot-bg-canvas')
    canvases.forEach(canvas => {
      init(canvas)
    })

    const canvas = document.getElementById('dot-bg')
    if (canvas && !canvas.classList.contains('dot-bg-canvas')) {
      init(canvas)
    }
  })
})()