import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { TZERO_COLORS } from '../types';

interface SwarmNode {
  id: string;
  name: string;
  angle: number;
  radius: number;
  color: string;
}

const NODES: SwarmNode[] = [
  { id: 'ast', name: 'AST Optimizer', angle: 0, radius: 240, color: '#00f0ff' },
  { id: 'sec', name: 'Security Sentinel', angle: 72, radius: 240, color: '#10b981' },
  { id: 'veto', name: 'Consensus Veto', angle: 144, radius: 240, color: '#f43f5e' },
  { id: 'mem', name: 'Hippocampus Memory', angle: 216, radius: 240, color: '#a855f7' },
  { id: 'ops', name: 'DevOps Orchestrator', angle: 288, radius: 240, color: '#f59e0b' },
];

export const CausalHudScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 14 } });

  // Rotating swarm orbit
  const orbitRotation = (frame * 0.8) % 360;

  // Expanding PBFT consensus wave
  const waveRadius = interpolate(frame % 60, [0, 60], [40, 380]);
  const waveOpacity = interpolate(frame % 60, [0, 60], [0.8, 0]);

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Outfit', 'Inter', sans-serif",
        color: TZERO_COLORS.textMain,
        position: 'relative',
        width: '100%',
        height: '100%',
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: 20, transform: `scale(${titleSpring})` }}>
        <div style={{ color: TZERO_COLORS.emerald, fontSize: 18, fontWeight: 700, letterSpacing: 4, textTransform: 'uppercase' }}>
          MULTI-AGENT RESILIENCE
        </div>
        <h2 style={{ fontSize: 56, fontWeight: 900, margin: '6px 0 0 0' }}>
          4D Causal Graph &amp; PBFT Swarm Radar
        </h2>
        <p style={{ color: TZERO_COLORS.textMuted, fontSize: 18, margin: '8px 0 0 0' }}>
          Byzantine Fault Tolerant Quorum (f &lt; 2) • Zero Hallucination Veto Mechanism
        </p>
      </div>

      {/* Radar Container */}
      <div
        style={{
          position: 'relative',
          width: 600,
          height: 480,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Radar Rings */}
        {[100, 200, 300].map((r) => (
          <div
            key={r}
            style={{
              position: 'absolute',
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              border: '1px solid rgba(0, 240, 255, 0.15)',
            }}
          />
        ))}

        {/* Dynamic Expanding PBFT Wave */}
        <div
          style={{
            position: 'absolute',
            width: waveRadius * 2,
            height: waveRadius * 2,
            borderRadius: '50%',
            border: `2px solid ${TZERO_COLORS.emerald}`,
            opacity: waveOpacity,
            pointerEvents: 'none',
          }}
        />

        {/* Center Core Node */}
        <div
          style={{
            position: 'absolute',
            width: 70,
            height: 70,
            borderRadius: '50%',
            background: 'radial-gradient(circle, #00f0ff 0%, #030712 90%)',
            border: `2px solid ${TZERO_COLORS.cyan}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 30px rgba(0, 240, 255, 0.8)',
            zIndex: 10,
          }}
        >
          <span style={{ fontSize: 24 }}>⚡</span>
        </div>

        {/* Orbiting Swarm Nodes */}
        {NODES.map((node) => {
          const currentAngleRad = ((node.angle + orbitRotation) * Math.PI) / 180;
          const x = Math.cos(currentAngleRad) * node.radius;
          const y = Math.sin(currentAngleRad) * (node.radius * 0.7); // Perspective oval

          return (
            <div
              key={node.id}
              style={{
                position: 'absolute',
                transform: `translate(${x}px, ${y}px)`,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                background: 'rgba(10, 16, 30, 0.95)',
                border: `1.5px solid ${node.color}`,
                borderRadius: 24,
                padding: '8px 16px',
                boxShadow: `0 0 20px ${node.color}40`,
                zIndex: 5,
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: node.color,
                  boxShadow: `0 0 10px ${node.color}`,
                }}
              />
              <span style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap' }}>
                {node.name}
              </span>
            </div>
          );
        })}
      </div>

      {/* Status Footer Badge */}
      <div
        style={{
          display: 'flex',
          gap: 24,
          background: 'rgba(15, 23, 42, 0.9)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '12px 28px',
          borderRadius: 30,
        }}
      >
        <div style={{ color: TZERO_COLORS.emerald, fontWeight: 700 }}>
          ✓ BFT Quorum: 5/5 Active
        </div>
        <div style={{ color: '#94a3b8' }}>•</div>
        <div style={{ color: TZERO_COLORS.cyan, fontWeight: 700 }}>
          ⚡ Latency: &lt; 0.84 ms
        </div>
        <div style={{ color: '#94a3b8' }}>•</div>
        <div style={{ color: '#f8fafc', fontWeight: 600 }}>
          🛡️ Hallucination Veto: ACTIVE
        </div>
      </div>
    </div>
  );
};
