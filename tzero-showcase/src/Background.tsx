import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

export const Background: React.FC = () => {
  const frame = useCurrentFrame();

  // Pulse grid opacity
  const gridOpacity = interpolate(Math.sin(frame / 20), [-1, 1], [0.15, 0.35]);
  
  // Floating orb motion
  const orb1X = 200 + Math.sin(frame / 45) * 80;
  const orb1Y = 300 + Math.cos(frame / 40) * 60;
  
  const orb2X = 1600 + Math.cos(frame / 50) * 90;
  const orb2Y = 700 + Math.sin(frame / 45) * 70;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#020617',
        overflow: 'hidden',
      }}
    >
      {/* Radial glow 1 (Cyan) */}
      <div
        style={{
          position: 'absolute',
          left: orb1X,
          top: orb1Y,
          width: 700,
          height: 700,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0, 240, 255, 0.12) 0%, transparent 70%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />

      {/* Radial glow 2 (Purple) */}
      <div
        style={{
          position: 'absolute',
          left: orb2X - 350,
          top: orb2Y - 350,
          width: 800,
          height: 800,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.14) 0%, transparent 70%)',
          filter: 'blur(80px)',
          pointerEvents: 'none',
        }}
      />

      {/* Cyberpunk Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(0, 240, 255, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
          opacity: gridOpacity,
        }}
      />

      {/* Subtle vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at center, transparent 40%, rgba(2, 6, 23, 0.85) 100%)',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};
