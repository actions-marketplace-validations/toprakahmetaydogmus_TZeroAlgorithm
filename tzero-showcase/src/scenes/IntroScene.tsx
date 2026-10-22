import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { TZERO_COLORS } from '../types';

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Alert entrance (spring)
  const alertScale = spring({ frame, fps, config: { damping: 12 } });
  const alertOpacity = interpolate(frame, [0, 10, 45, 55], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Main logo reveal starts after alert
  const logoSpring = spring({
    frame: frame - 40,
    fps,
    config: { damping: 14, mass: 0.8 },
  });

  const subtitleOpacity = interpolate(frame - 65, [0, 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const badgesY = spring({
    frame: frame - 90,
    fps,
    config: { damping: 15 },
  });

  // Shockwave ring expansion
  const shockwave = interpolate(frame - 40, [0, 40], [0, 800], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const shockwaveOpacity = interpolate(frame - 40, [0, 30], [0.8, 0], {
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
        position: 'relative',
        width: '100%',
        height: '100%',
      }}
    >
      {/* Shockwave circle */}
      {frame >= 40 && (
        <div
          style={{
            position: 'absolute',
            width: shockwave,
            height: shockwave,
            borderRadius: '50%',
            border: `2px solid ${TZERO_COLORS.cyan}`,
            opacity: shockwaveOpacity,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Warning Phase (0-55 frames) */}
      {frame < 60 && (
        <div
          style={{
            position: 'absolute',
            transform: `scale(${alertScale})`,
            opacity: alertOpacity,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              background: 'rgba(244, 63, 94, 0.15)',
              border: `1px solid ${TZERO_COLORS.rose}`,
              padding: '10px 24px',
              borderRadius: 30,
              color: TZERO_COLORS.rose,
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: 3,
              boxShadow: '0 0 30px rgba(244, 63, 94, 0.4)',
            }}
          >
            ⚠️ WARNING: CONTEXT WINDOW OVERFLOW
          </div>
          <div style={{ fontSize: 44, fontWeight: 800, color: '#f8fafc' }}>
            Are Your AI Prompts Bleeding Money?
          </div>
        </div>
      )}

      {/* T-Zero Hero Reveal (frame 40+) */}
      {frame >= 40 && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            transform: `scale(${logoSpring})`,
          }}
        >
          {/* Cyan Pill Tag */}
          <div
            style={{
              background: 'rgba(0, 240, 255, 0.12)',
              border: `1px solid ${TZERO_COLORS.cyan}`,
              padding: '8px 22px',
              borderRadius: 24,
              color: TZERO_COLORS.cyan,
              fontSize: 18,
              fontWeight: 700,
              letterSpacing: 4,
              marginBottom: 16,
              boxShadow: '0 0 20px rgba(0, 240, 255, 0.3)',
            }}
          >
            NEXT-GEN REVOLUTION
          </div>

          {/* Hero Title */}
          <h1
            style={{
              fontSize: 120,
              fontWeight: 900,
              letterSpacing: '-2px',
              margin: '0 0 10px 0',
              lineHeight: 1,
              background: 'linear-gradient(135deg, #ffffff 30%, #00f0ff 70%, #a855f7 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              textShadow: '0 0 40px rgba(0, 240, 255, 0.5)',
            }}
          >
            T-ZERO v6.1
          </h1>

          <h2
            style={{
              fontSize: 38,
              fontWeight: 700,
              color: '#e2e8f0',
              margin: '0 0 24px 0',
              opacity: subtitleOpacity,
              letterSpacing: '1px',
            }}
          >
            Enterprise AST Context Architect &amp; Swarm MCP
          </h2>

          <p
            style={{
              fontSize: 24,
              color: TZERO_COLORS.textMuted,
              maxWidth: 900,
              textAlign: 'center',
              lineHeight: 1.5,
              opacity: subtitleOpacity,
              margin: '0 0 40px 0',
            }}
          >
            Cut codebase context ingestion by up to <strong style={{ color: TZERO_COLORS.cyan }}>95%</strong> with mathematical AST precision.
          </p>

          {/* Floating Language Badges */}
          <div
            style={{
              display: 'flex',
              gap: 14,
              transform: `translateY(${(1 - badgesY) * 40}px)`,
              opacity: badgesY,
            }}
          >
            {['Python', 'TypeScript', 'Rust', 'Go', 'C++', 'Solidity', 'Java'].map((lang) => (
              <div
                key={lang}
                style={{
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: 10,
                  padding: '8px 18px',
                  fontSize: 16,
                  fontWeight: 600,
                  color: '#94a3b8',
                }}
              >
                {lang}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
