import React from 'react';
import { Composition, Series } from 'remotion';
import { Background } from './Background';
import { IntroScene } from './scenes/IntroScene';
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
              {/* Scene 1: High-Voltage Cyber Intro & Problem Hook (6s / 180 frames) */}
              <Series.Sequence durationInFrames={180}>
                <IntroScene />
              </Series.Sequence>

              {/* Scene 2: AST Codebase Optimization & -94.4% Slasher (7s / 210 frames) */}
              <Series.Sequence durationInFrames={210}>
                <MetricsScene />
              </Series.Sequence>

              {/* Scene 3: 37 Autonomous MCP Tools Grid (7s / 210 frames) */}
              <Series.Sequence durationInFrames={210}>
                <McpGridScene />
              </Series.Sequence>

              {/* Scene 4: 4D Causal-Temporal Graph & PBFT Swarm Radar (7s / 210 frames) */}
              <Series.Sequence durationInFrames={210}>
                <CausalHudScene />
              </Series.Sequence>

              {/* Scene 5: $419k Financial ROI & Terminal Call To Action (8s / 240 frames) */}
              <Series.Sequence durationInFrames={240}>
                <RoiOutroScene />
              </Series.Sequence>
            </Series>
          </div>
        )}
        durationInFrames={1050}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
