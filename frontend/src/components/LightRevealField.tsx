import { useRef, useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import * as THREE from 'three'

export interface Cluster {
  code: string
  name: string
  total: number
  coverage: number   // 0..1 — share of orgs made visible (mission + score)
}

interface Placed extends Cluster {
  cx: number   // normalized 0..1 (left→right)
  cy: number   // normalized 0..1 (top→bottom in DOM terms)
  points: number
}

const vertexShader = `
  attribute float aSize;
  attribute float aBrightness;
  attribute float aPhase;
  attribute float aSpeed;
  attribute float aAlwaysOn;     // 1 = the ~3% already visible before Daanaa

  uniform float uTime;
  uniform float uPixelRatio;
  uniform float uReveal;

  varying float vAlpha;
  varying float vGlow;

  void main() {
    vec3 p = position;            // x,y already normalized 0..1, z small depth jitter
    p.y += sin(uTime * aSpeed + aPhase) * 0.004;

    float nx = p.x;
    // 1.0 to the left of the lamp (lit), 0.0 to the right (still invisible)
    float reveal = 1.0 - smoothstep(uReveal - 0.04, uReveal + 0.04, nx);
    // the pre-visible 3% glow from the start; the invisible 97% wait for the lamp
    float lit = max(aAlwaysOn, reveal);
    vAlpha = aBrightness * lit;

    float dl = abs(nx - uReveal);
    vGlow = exp(-dl * dl * 500.0) * reveal;   // bright crest right at the lamp edge

    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = aSize * uPixelRatio;
  }
`

const fragmentShader = `
  varying float vAlpha;
  varying float vGlow;

  void main() {
    vec2 xy = gl_PointCoord.xy - vec2(0.5);
    float ll = length(xy);
    if (ll > 0.5) discard;

    float glow = exp(-ll * ll * 2.0);
    float alpha = (vAlpha + vGlow * 0.7) * glow;

    // warm gold, whitening at the lamp crest
    vec3 col = mix(vec3(1.0, 0.82, 0.5), vec3(1.0, 0.96, 0.82), vGlow);
    gl_FragColor = vec4(col, alpha * 0.95);
  }
`

function layout(clusters: Cluster[], aspect: number): Placed[] {
  const n = clusters.length
  const cols = Math.min(7, Math.max(3, Math.round(Math.sqrt(n * aspect))))
  const rows = Math.ceil(n / cols)
  const xPad = 0.08, yPad = 0.16
  const xSpan = 1 - xPad * 2, ySpan = 1 - yPad * 2
  return clusters.map((c, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    const jx = (Math.random() - 0.5) * (xSpan / cols) * 0.25
    const jy = (Math.random() - 0.5) * (ySpan / Math.max(1, rows)) * 0.25
    const cx = xPad + (cols === 1 ? 0.5 : (col / (cols - 1))) * xSpan + jx
    const cy = yPad + (rows === 1 ? 0.5 : (row / (rows - 1))) * ySpan + jy
    return { ...c, cx, cy, points: 0 }
  })
}

export default function LightRevealField({
  clusters,
  onComplete,
}: {
  clusters: Cluster[]
  onComplete?: () => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const materialRef = useRef<THREE.ShaderMaterial | null>(null)
  const revealRef = useRef(0.04)
  const draggingRef = useRef(false)
  const completedRef = useRef(false)
  const [placed, setPlaced] = useState<Placed[]>([])
  const [reveal, setReveal] = useState(0.04)
  const [dims, setDims] = useState({ w: 0, h: 0 })

  const setRevealValue = useCallback((v: number) => {
    const clamped = Math.max(0, Math.min(1, v))
    revealRef.current = clamped
    setReveal(clamped)
    if (materialRef.current) materialRef.current.uniforms.uReveal.value = clamped
    if (clamped > 0.985 && !completedRef.current) {
      completedRef.current = true
      onComplete?.()
    }
  }, [onComplete])

  // ── WebGL init ────────────────────────────────────────────────────────────
  useEffect(() => {
    const container = containerRef.current
    if (!container || clusters.length === 0) return

    const w = container.offsetWidth
    const h = container.offsetHeight
    const aspect = w / Math.max(1, h)
    setDims({ w, h })

    const placedClusters = layout(clusters, aspect)

    // Allocate point budget (~2400) weighted by sqrt(total) so big causes read bigger
    const BUDGET = 2400
    const weights = placedClusters.map(c => Math.sqrt(c.total))
    const wSum = weights.reduce((a, b) => a + b, 0)
    placedClusters.forEach((c, i) => {
      c.points = Math.max(18, Math.round((weights[i] / wSum) * BUDGET))
    })
    setPlaced(placedClusters)

    const total = placedClusters.reduce((a, c) => a + c.points, 0)
    const positions = new Float32Array(total * 3)
    const sizes = new Float32Array(total)
    const brightness = new Float32Array(total)
    const phases = new Float32Array(total)
    const speeds = new Float32Array(total)
    const alwaysOn = new Float32Array(total)

    const PRE_VISIBLE = 0.03   // the ~3% that already had attention before Daanaa

    let p = 0
    for (const c of placedClusters) {
      const radius = 0.05 + Math.sqrt(c.points) * 0.0016
      for (let k = 0; k < c.points; k++) {
        // gaussian-ish scatter around the centroid
        const g = () => (Math.random() + Math.random() + Math.random() - 1.5) / 1.5
        positions[p * 3] = c.cx + g() * radius * aspect
        positions[p * 3 + 1] = c.cy + g() * radius
        positions[p * 3 + 2] = (Math.random() - 0.5) * 0.02

        if (Math.random() < PRE_VISIBLE) {
          // already visible — glows from the start, brighter and a touch larger
          alwaysOn[p] = 1
          brightness[p] = 0.85 + Math.random() * 0.15
          sizes[p] = 3.0 + Math.random() * 1.8
        } else {
          // the invisible 97%: lit by the lamp, proportion bright == real coverage
          const visible = Math.random() < c.coverage
          alwaysOn[p] = 0
          brightness[p] = visible ? 0.7 + Math.random() * 0.3 : 0.06
          sizes[p] = (visible ? 2.2 : 1.6) + Math.random() * 2.0
        }
        phases[p] = Math.random() * Math.PI * 2
        speeds[p] = 0.2 + Math.random() * 0.9
        p++
      }
    }

    const scene = new THREE.Scene()
    // Orthographic camera spanning [0,1] x [0,1] → normalized layout maps 1:1
    const camera = new THREE.OrthographicCamera(0, 1, 1, 0, -10, 10)
    camera.position.z = 1

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(w, h)
    const pr = Math.min(2, window.devicePixelRatio)
    renderer.setPixelRatio(pr)
    container.appendChild(renderer.domElement)
    renderer.domElement.style.touchAction = 'none'

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1))
    geometry.setAttribute('aBrightness', new THREE.BufferAttribute(brightness, 1))
    geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1))
    geometry.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1))
    geometry.setAttribute('aAlwaysOn', new THREE.BufferAttribute(alwaysOn, 1))

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0 },
        uPixelRatio: { value: pr },
        uReveal: { value: revealRef.current },
      },
      transparent: true,
      depthTest: false,
      blending: THREE.AdditiveBlending,
    })
    materialRef.current = material

    scene.add(new THREE.Points(geometry, material))

    let visible = true
    const observer = new IntersectionObserver(
      ([e]) => { visible = e.isIntersecting },
      { threshold: 0.05 }
    )
    observer.observe(container)

    const clock = new THREE.Clock()
    let raf = 0
    const animate = () => {
      raf = requestAnimationFrame(animate)
      if (!visible) return
      material.uniforms.uTime.value = clock.getElapsedTime()
      renderer.render(scene, camera)
    }
    animate()

    const handleResize = () => {
      const nw = container.offsetWidth
      const nh = container.offsetHeight
      renderer.setSize(nw, nh)
      material.uniforms.uPixelRatio.value = Math.min(2, window.devicePixelRatio)
      setDims({ w: nw, h: nh })
    }
    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', handleResize)
      observer.disconnect()
      renderer.dispose()
      geometry.dispose()
      material.dispose()
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      materialRef.current = null
    }
  }, [clusters])

  // ── Drag the lamp ─────────────────────────────────────────────────────────
  const pointerToReveal = (clientX: number) => {
    const el = containerRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    setRevealValue((clientX - rect.left) / rect.width)
  }
  const onPointerDown = (e: React.PointerEvent) => {
    draggingRef.current = true
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    pointerToReveal(e.clientX)
  }
  const onPointerMove = (e: React.PointerEvent) => {
    if (!draggingRef.current) return
    pointerToReveal(e.clientX)
  }
  const endDrag = () => { draggingRef.current = false }

  // Animate the lamp the rest of the way (tap-to-finish / "reveal all")
  const revealAll = useCallback(() => {
    const step = () => {
      const next = revealRef.current + 0.018
      setRevealValue(next)
      if (next < 1) requestAnimationFrame(step)
    }
    step()
  }, [setRevealValue])

  return (
    <div className="absolute inset-0 select-none">
      <div
        ref={containerRef}
        className="absolute inset-0 z-0 cursor-ew-resize"
        style={{ background: '#0A1628', touchAction: 'none' }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      />

      {/* Category label hotspots — focusable links, clickable only once lit */}
      {placed.map(c => {
        const lit = c.cx <= reveal
        const left = c.cx * dims.w
        const top = c.cy * dims.h
        return (
          <Link
            key={c.code}
            to={`/directory?category=${c.code}`}
            aria-label={`Browse ${c.total.toLocaleString()} ${c.name} nonprofits`}
            tabIndex={lit ? 0 : -1}
            className="absolute z-10 -translate-x-1/2 -translate-y-1/2 rounded-full px-2.5 py-1 text-center transition-all duration-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
            style={{
              left, top,
              opacity: lit ? 1 : 0,
              pointerEvents: lit ? 'auto' : 'none',
              background: 'rgba(10,22,40,0.55)',
              backdropFilter: 'blur(2px)',
            }}
          >
            <span className="block font-display text-[12px] sm:text-[13px] font-semibold text-warm-cream leading-tight">
              {c.name}
            </span>
            <span className="block font-body text-[10px] text-soft-gold">
              {c.total.toLocaleString()}
            </span>
          </Link>
        )
      })}

      {/* The lamp handle */}
      <div
        className="absolute top-0 bottom-0 z-20 pointer-events-none"
        style={{ left: `${reveal * 100}%`, transform: 'translateX(-50%)' }}
      >
        <div
          className="h-full w-px"
          style={{ background: 'linear-gradient(to bottom, transparent, rgba(212,184,122,0.55), transparent)' }}
        />
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-9 w-9 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(232,213,163,0.95) 0%, rgba(201,169,110,0.5) 45%, transparent 70%)',
            boxShadow: '0 0 24px 6px rgba(201,169,110,0.45)',
          }}
        />
      </div>

      {/* Reveal-all affordance */}
      {reveal < 0.985 && (
        <button
          onClick={revealAll}
          className="absolute bottom-5 left-1/2 z-20 -translate-x-1/2 rounded-full border border-soft-gold/40 bg-deep-navy/60 px-4 py-1.5 font-body text-[12px] text-warm-cream backdrop-blur-sm transition-colors hover:border-soft-gold"
        >
          Drag the lamp →  or  tap to reveal all
        </button>
      )}
    </div>
  )
}
