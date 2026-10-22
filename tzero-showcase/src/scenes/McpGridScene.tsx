import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { TZERO_COLORS } from '../types';

const HIGHLIGHTED_TOOLS = [
  { name: 'jarvis_orchestrate_goal', cat: 'Autonomous Goal Synthesis', badge: 'SWARM' },
  { name: 'get_project_context_tree', cat: 'AST Hierarchical Map (-95%)', badge: 'AST' },
  { name: 'jarvis_causal_chain_query', cat: '4D Temporal Deductions', badge: 'MEMORY' },
  { name: 'audit_codebase_quality', cat: 'Zero-Leak Hardcoded Secret Scan', badge: 'SECURITY' },
  { name: 'jarvis_bft_swarm_consensus', cat: 'Byzantine Fault-Tolerant Quorum', badge: 'CONSENSUS' },
  { name: 'verify_hallucination_guard', cat: 'Deterministic Output Shield', badge: 'GUARD' },
  { name: 'generate_architecture_blueprint', cat: 'Live Mermaid Topology Spec', badge: 'SPEC' },
  { name: 'analyze_change_impact', cat: 'Blast Radius Scoring (0-100)', badge: 'ANALYSIS' },
  { name: 'jarvis_hybrid_search', cat: 'BM25 + Semantic Private Index', badge: 'RETRIEVAL' },
];

export const McpGridScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, config: { damping: 14 } });

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
        padding: '0 80px',
        width: '100%',
        height: '100%',
      }}
    >
      <div
        style={{
          transform: `scale(${titleSpring})`,
          textAlign: 'center',
          marginBottom: 36,
        }}
      >
        <div
          style={{
            color: TZERO_COLORS.purple,
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: 4,
            marginBottom: 8,
          }}
        >
          AUTONOMOUS CAPABILITY PROTOCOL
        </div>
        <h2 style={{ fontSize: 60, fontWeight: 900, margin: 0 }}>
          37 Native Model Context Protocol (MCP) Tools
        </h2>
        <p style={{ color: TZERO_COLORS.textMuted, fontSize: 20, margin: '10px 0 0 0' }}>
          Instantly equips Claude, Cursor, Windsurf, Cline &amp; Antigravity with military-grade intelligence.
        </p>
      </div>

      {/* Grid of Tools */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 20,
          width: '100%',
          maxWidth: 1300,
        }}
      >
        {HIGHLIGHTED_TOOLS.map((tool, index) => {
          const delay = index * 2.5;
          const cardSpring = spring({
            frame: frame - delay,
            fps,
            config: { damping: 13, mass: 0.8 },
          });
          const opacity = interpolate(frame - delay, [0, 8], [0, 1], {
            extrapolateLeft: 'clamp',
          });

          return (
            <div
              key={tool.name}
              style={{
                transform: `scale(${cardSpring})`,
                opacity,
                background: 'rgba(10, 16, 30, 0.92)',
                border: '1px solid rgba(0, 240, 255, 0.25)',
                borderRadius: 12,
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.5)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span
                  style={{
                    color: TZERO_COLORS.cyan,
                    fontFamily: 'monospace',
                    fontSize: 16,
                    fontWeight: 700,
                  }}
                >
                  {tool.name}
                </span>
                <span
                  style={{
                    background: 'rgba(168, 85, 247, 0.2)',
                    color: '#c084fc',
                    padding: '3px 10px',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 800,
                    letterSpacing: 1,
                  }}
                >
                  {tool.badge}
                </span>
              </div>
              <span style={{ color: TZERO_COLORS.textMuted, fontSize: 14 }}>
                {tool.cat}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
