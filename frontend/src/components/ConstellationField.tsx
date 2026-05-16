import { useRef, useEffect, useCallback } from 'react'
import * as THREE from 'three'

const vertexShader = `
  attribute float aSize;
  attribute float aPhase;
  attribute float aSpeed;
  attribute float aBrightness;

  uniform float uTime;
  uniform float uPixelRatio;
  uniform vec2 uHover;

  varying float vAlpha;
  varying float vGlow;

  void main() {
    vec3 vPosition = position;

    float t = uTime * aSpeed + aPhase;
    float d = distance(vPosition.xz, uHover);

    vec3 toHover = vec3(uHover.x, 0.0, uHover.y) - vPosition;
    toHover.y = 0.0;
    vec3 dir = normalize(toHover);

    float attractStrength = smoothstep(50.0, 0.0, d) * 15.0;
    float lift = smoothstep(15.0, 0.0, d) * 8.0;
    float wobble = sin(t * 2.0) * 0.5;

    vPosition.xz += (dir * attractStrength + wobble) * 0.02;
    vPosition.y += lift * 0.02;

    float depth = smoothstep(300.0, 0.0, length(vPosition.xyz));
    vAlpha = depth * aBrightness;

    float cursorGlow = exp(-d * d * 0.001) * 0.8;
    vGlow = cursorGlow;

    vec4 mvPosition = modelViewMatrix * vec4(vPosition, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    gl_PointSize = aSize * uPixelRatio * (300.0 / -mvPosition.z);
  }
`

const fragmentShader = `
  varying float vAlpha;
  varying float vGlow;
  uniform vec3 uColor;

  void main() {
    vec2 xy = gl_PointCoord.xy - vec2(0.5);
    float ll = length(xy);
    if (ll > 0.5) discard;

    float glow = exp(-ll * ll * 2.0);
    float alpha = (vAlpha + vGlow) * glow;

    gl_FragColor = vec4(vec3(1.0, 0.9, 0.75), alpha * 0.9);
  }
`

function gaussianRandom(): number {
  let sum = 0
  for (let i = 0; i < 6; i++) {
    sum += Math.random()
  }
  return (sum - 3) * 20 + 200
}

export default function ConstellationField() {
  const containerRef = useRef<HTMLDivElement>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const materialRef = useRef<THREE.ShaderMaterial | null>(null)
  const rafRef = useRef<number>(0)
  const clockRef = useRef<THREE.Clock>(new THREE.Clock())
  const isVisibleRef = useRef(true)

  const init = useCallback(() => {
    const container = containerRef.current
    if (!container) return

    // Scene setup
    const scene = new THREE.Scene()
    sceneRef.current = scene

    const camera = new THREE.PerspectiveCamera(
      60,
      container.offsetWidth / container.offsetHeight,
      1,
      1000
    )
    camera.position.set(0, 0, 400)
    camera.lookAt(0, 0, 0)
    cameraRef.current = camera

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(container.offsetWidth, container.offsetHeight)
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio))
    container.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Particle geometry
    const PARTICLE_COUNT = 3000
    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const sizes = new Float32Array(PARTICLE_COUNT)
    const phases = new Float32Array(PARTICLE_COUNT)
    const speeds = new Float32Array(PARTICLE_COUNT)
    const brightness = new Float32Array(PARTICLE_COUNT)

    // Ring layout (80%)
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const radius = gaussianRandom()
      const angle = Math.random() * Math.PI * 2
      positions[i * 3] = Math.cos(angle) * radius
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20
      positions[i * 3 + 2] = Math.sin(angle) * radius

      sizes[i] = 2.0 + Math.random() * 6.0
      phases[i] = Math.random() * Math.PI * 2
      speeds[i] = 0.1 + Math.random() * 0.7
      brightness[i] = 0.2 + Math.random() * 0.8
    }

    // Disc fill (20%)
    const discCount = Math.floor(PARTICLE_COUNT * 0.2)
    for (let i = 0; i < discCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 600
      positions[i * 3 + 1] = (Math.random() - 0.5) * 200
      positions[i * 3 + 2] = (Math.random() - 0.5) * 600
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1))
    geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1))
    geometry.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1))
    geometry.setAttribute('aBrightness', new THREE.BufferAttribute(brightness, 1))

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0.0 },
        uPixelRatio: { value: Math.min(2, window.devicePixelRatio) },
        uColor: { value: new THREE.Color(1.0, 1.0, 1.0) },
        uHover: { value: new THREE.Vector2(9999, 9999) },
      },
      transparent: true,
      depthTest: false,
      blending: THREE.AdditiveBlending,
    })
    materialRef.current = material

    const points = new THREE.Points(geometry, material)
    scene.add(points)

    // Invisible plane for raycasting
    const planeGeometry = new THREE.PlaneGeometry(2000, 2000)
    const planeMaterial = new THREE.MeshBasicMaterial({ visible: false })
    const planeMesh = new THREE.Mesh(planeGeometry, planeMaterial)
    planeMesh.rotation.x = -Math.PI / 2
    scene.add(planeMesh)

    // Raycaster
    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    // Mouse move handler
    const handleMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

      raycaster.setFromCamera(mouse, camera)
      const intersects = raycaster.intersectObject(planeMesh)

      if (intersects.length > 0) {
        material.uniforms.uHover.value.set(
          intersects[0].point.x,
          intersects[0].point.z
        )
      }
    }

    const handleMouseLeave = () => {
      material.uniforms.uHover.value.set(9999, 9999)
    }

    const canvas = renderer.domElement
    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseleave', handleMouseLeave)

    // Visibility observer
    const observer = new IntersectionObserver(
      ([entry]) => {
        isVisibleRef.current = entry.isIntersecting
      },
      { threshold: 0.1 }
    )
    observer.observe(container)

    // Animation loop
    const clock = clockRef.current
    clock.start()

    const animate = () => {
      rafRef.current = requestAnimationFrame(animate)

      if (!isVisibleRef.current) return

      const elapsed = clock.getElapsedTime()
      material.uniforms.uTime.value = elapsed + 0.01

      renderer.render(scene, camera)
    }
    animate()

    // Resize handler
    const handleResize = () => {
      if (!container) return
      const w = container.offsetWidth
      const h = container.offsetHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
      material.uniforms.uPixelRatio.value = Math.min(2, window.devicePixelRatio)
    }

    window.addEventListener('resize', handleResize)

    // Cleanup ref
    return () => {
      cancelAnimationFrame(rafRef.current)
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseleave', handleMouseLeave)
      window.removeEventListener('resize', handleResize)
      observer.disconnect()
      renderer.dispose()
      geometry.dispose()
      material.dispose()
      planeGeometry.dispose()
      planeMaterial.dispose()
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [])

  useEffect(() => {
    const cleanup = init()
    return () => {
      cleanup?.()
    }
  }, [init])

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-0"
      style={{ background: '#0A1628' }}
    />
  )
}
