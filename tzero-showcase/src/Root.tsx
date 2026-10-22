import React from 'react';
import { Composition, Series } from 'remotion';
import { Background } from './Background';
import { NineStarsHookScene } from './scenes/NineStarsHookScene';
import { MetricsScene } from './scenes/MetricsScene';
import { McpGridScene } from './scenes/McpGridScene';
import { CausalHudScene } from './scenes/CausalHudScene';
import { RoiOutroScene } from './scenes/RoiOutroScene';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TZeroPromo"
        component={() => (
          <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
            <Background />
            <Series>
              {/* Scene 1: The Viral "9 Stars" Reality Check Hook (8.0s / 240 frames) */}
              <Series.Sequence durationInFrames={240}>
                <NineStarsHookScene />
              </Series.Sequence>

              {/* Scene 2: AST Codebase Optimization & -94.4% Slasher (7.0s / 210 frames) */}
              <Series.Sequence durationInFrames={176}>
                <MetricsScene />
              </Series.Sequence>

              {/* Scene 3: 37 Autonomous MCP Tools Grid (7.0s / 210 frames) */}
              <Series.Sequence durationInFrames={140}>
                <McpGridScene />
              </Series.Sequence>

              {/* Scene 4: 4D Causal-Temporal Graph & PBFT Swarm Radar (7.0s / 210 frames) */}
              <Series.Sequence durationInFrames={136}>
                <CausalHudScene />
              </Series.Sequence>

              {/* Scene 5: $419k Financial ROI & "Don't let it stay at 9 stars" CTA (9.0s / 270 frames) */}
              <Series.Sequence durationInFrames={235}>
                <RoiOutroScene />
              </Series.Sequence>
            </Series>
          </div>
        )}
        durationInFrames={1140}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
