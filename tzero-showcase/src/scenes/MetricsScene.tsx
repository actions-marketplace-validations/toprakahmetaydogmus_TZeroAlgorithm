import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { TZERO_COLORS } from '../types';

export const MetricsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring
  const containerScale = spring({ frame, fps, config: { damping: 14 } });

  // Reduction counter animation from 0 to 94.4%
  const reductionValue = interpolate(frame, [15, 75], [0, 94.4], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const rawTokens = interpolate(frame, [15, 75], [0, 67842], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const prunedTokens = interpolate(frame, [15, 75], [0, 3800], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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
        transform: `scale(${containerScale})`,
        padding: '0 80px',
        width: '100%',
        height: '100%',
      }}
    >
      <div
        style={{
          color: TZERO_COLORS.cyan,
          fontSize: 18,
          fontWeight: 700,
          letterSpacing: 4,
          textTransform: 'uppercase',
          marginBottom: 12,
        }}
      >
        BENCHMARK PROVEN AST OPTIMIZATION
      </div>

      <h2
        style={{
          fontSize: 64,
          fontWeight: 900,
          margin: '0 0 40px 0',
          textAlign: 'center',
        }}
      >
        Slashes Prompt Context by{' '}
        <span style={{ color: TZERO_COLORS.cyan, textShadow: '0 0 30px rgba(0, 240, 255, 0.6)' }}>
          {reductionValue.toFixed(1)}%
        </span>
      </h2>

      {/* Side-by-side Dual Cards */}
      <div
        style={{
          display: 'flex',
          gap: 32,
          width: '100%',
          maxWidth: 1200,
          marginBottom: 36,
        }}
      >
        {/* Left: Raw Code */}
        <div
          style={{
            flex: 1,
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(244, 63, 94, 0.35)',
            borderRadius: 16,
            padding: 32,
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <span style={{ fontSize: 20, fontWeight: 700, color: '#f8fafc' }}>Raw Source Code</span>
            <span style={{ background: 'rgba(244, 63, 94, 0.15)', color: TZERO_COLORS.rose, padding: '4px 12px', borderRadius: 8, fontSize: 14, fontWeight: 700 }}>
              BLOATED
            </span>
          </div>
          <div style={{ fontSize: 44, fontWeight: 800, color: TZERO_COLORS.rose, marginBottom: 8, fontFamily: 'monospace' }}>
            {Math.round(rawTokens).toLocaleString()} tokens
          </div>
          <p style={{ color: TZERO_COLORS.textMuted, fontSize: 16, margin: 0 }}>
            6,008 raw Python lines (tzero_v3.py). Redundant comments, imports &amp; whitespace choking the context window.
          </p>
        </div>

        {/* Right: T-Zero Ultra AST */}
        <div
          style={{
            flex: 1,
            background: 'rgba(10, 25, 45, 0.9)',
            border: `1px solid ${TZERO_COLORS.cyan}`,
            borderRadius: 16,
            padding: 32,
            boxShadow: '0 0 40px rgba(0, 240, 255, 0.25)',
            position: 'relative',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <span style={{ fontSize: 20, fontWeight: 700, color: '#ffffff' }}>T-Zero Ultra AST</span>
            <span style={{ background: 'rgba(0, 240, 255, 0.2)', color: TZERO_COLORS.cyan, padding: '4px 12px', borderRadius: 8, fontSize: 14, fontWeight: 700 }}>
              OPTIMIZED
            </span>
          </div>
          <div style={{ fontSize: 44, fontWeight: 800, color: TZERO_COLORS.cyan, marginBottom: 8, fontFamily: 'monospace' }}>
            {Math.round(prunedTokens).toLocaleString()} tokens
          </div>
          <p style={{ color: '#cbd5e1', fontSize: 16, margin: 0 }}>
            100% signature topology preserved. Zero hallucination risk. Ready for instant LLM ingestion.
          </p>
        </div>
      </div>

      {/* Progress Bar Strip */}
      <div
        style={{
          width: '100%',
          maxWidth: 1200,
          background: 'rgba(15, 23, 42, 0.9)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 14,
          padding: 24,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14, fontSize: 18 }}>
          <span style={{ fontWeight: 600 }}>AST SIGNATURE TOKEN ELIMINATION</span>
          <span style={{ color: TZERO_COLORS.cyan, fontWeight: 800, fontFamily: 'monospace' }}>
            -{reductionValue.toFixed(2)}% SAVED
          </span>
        </div>
        <div style={{ width: '100%', height: 18, background: '#020617', borderRadius: 10, overflow: 'hidden' }}>
          <div
            style={{
              width: `${reductionValue}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #00f0ff 0%, #a855f7 60%, #10b981 100%)',
              boxShadow: '0 0 20px rgba(0, 240, 255, 0.8)',
            }}
          />
        </div>
      </div>
    </div>
  );
};
