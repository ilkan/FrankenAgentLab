/**
 * Canvas with Creature - Main canvas area with Frankenstein creature visualization
 */

import { useCanvasStore } from '../stores/canvasStore';
import { useBlueprintStore } from '../stores/blueprintStore';

export const CanvasWithCreature = () => {
  const { nodes } = useCanvasStore();
  const { agentConfig } = useBlueprintStore();

  // Count parts by type
  const headCount = nodes.filter((n) => n.type === 'head').length;
  const armCount = nodes.filter((n) => n.type === 'arm').length;
  const legCount = nodes.filter((n) => n.type === 'leg').length;
  const heartCount = nodes.filter((n) => n.type === 'heart').length;
  const spineCount = nodes.filter((n) => n.type === 'spine').length;

  const isComplete = headCount > 0 && legCount > 0;

  return (
    <div className="flex-1 bg-bg-primary relative overflow-hidden">
      {/* Grid background */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: 'radial-gradient(circle, #39ff14 1px, transparent 1px)',
          backgroundSize: '30px 30px',
        }}
      />

      {/* Frankenstein Creature SVG */}
      <div className="absolute inset-0 flex items-center justify-center">
        <svg viewBox="0 0 600 800" className="w-full max-w-2xl h-full max-h-[800px]">
          {/* Spine (background) */}
          <g>
            <rect
              x="275"
              y="200"
              width="50"
              height="280"
              fill={spineCount > 0 ? '#78716c' : '#374151'}
              opacity="0.3"
              rx="8"
            />
            {spineCount > 0 && (
              <text x="300" y="340" textAnchor="middle" fill="white" fontSize="12">
                Spine
              </text>
            )}
          </g>

          {/* Head */}
          <g>
            <circle
              cx="300"
              cy="150"
              r="70"
              fill={headCount > 0 ? '#10a37f' : '#1f2937'}
              stroke="#4b5563"
              strokeWidth="3"
            />
            <circle cx="280" cy="140" r="8" fill="white" opacity="0.9" />
            <circle cx="320" cy="140" r="8" fill="white" opacity="0.9" />
            <circle cx="282" cy="142" r="4" fill="#1f2937" />
            <circle cx="322" cy="142" r="4" fill="#1f2937" />

            {/* Frankenstein bolts */}
            <rect x="225" y="145" width="12" height="20" fill="#6b7280" rx="2" />
            <rect x="363" y="145" width="12" height="20" fill="#6b7280" rx="2" />

            {/* Stitches */}
            <line x1="270" y1="100" x2="280" y2="100" stroke="#6b7280" strokeWidth="2" />
            <line x1="320" y1="100" x2="330" y2="100" stroke="#6b7280" strokeWidth="2" />

            {headCount > 0 && (
              <text x="300" y="190" textAnchor="middle" fill="white" fontSize="11">
                Head
              </text>
            )}
          </g>

          {/* Body/Torso */}
          <rect x="230" y="220" width="140" height="180" fill="#1f2937" stroke="#4b5563" strokeWidth="3" rx="10" />

          {/* Heart */}
          <g>
            <path
              d="M 300 280 L 320 300 L 300 330 L 280 300 Z"
              fill={heartCount > 0 ? '#ef4444' : '#374151'}
              stroke="#4b5563"
              strokeWidth="2"
            />
            <circle cx="288" cy="292" r="10" fill={heartCount > 0 ? '#ef4444' : '#374151'} stroke="#4b5563" strokeWidth="2" />
            <circle cx="312" cy="292" r="10" fill={heartCount > 0 ? '#ef4444' : '#374151'} stroke="#4b5563" strokeWidth="2" />

            {heartCount > 0 && (
              <text x="300" y="360" textAnchor="middle" fill="white" fontSize="10">
                Heart
              </text>
            )}
          </g>

          {/* Left Arm */}
          <g>
            <rect x="140" y="240" width="80" height="25" fill={armCount > 0 ? '#8b5cf6' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="8" />
            <rect x="100" y="265" width="40" height="80" fill={armCount > 0 ? '#8b5cf6' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="8" />
            <line x1="145" y1="252" x2="155" y2="252" stroke="#6b7280" strokeWidth="2" />
          </g>

          {/* Right Arm */}
          <g>
            <rect x="380" y="240" width="80" height="25" fill={armCount > 1 ? '#8b5cf6' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="8" />
            <rect x="460" y="265" width="40" height="80" fill={armCount > 1 ? '#8b5cf6' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="8" />
            <line x1="425" y1="252" x2="435" y2="252" stroke="#6b7280" strokeWidth="2" />
          </g>

          {/* Left Leg */}
          <g>
            <rect x="245" y="400" width="35" height="120" fill={legCount > 0 ? '#6366f1' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="8" />
            <rect x="245" y="520" width="40" height="25" fill={legCount > 0 ? '#6366f1' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="6" />
            <line x1="252" y1="410" x2="262" y2="410" stroke="#6b7280" strokeWidth="2" />
          </g>

          {/* Right Leg */}
          <g>
            <rect x="320" y="400" width="35" height="120" fill={legCount > 0 ? '#6366f1' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="8" />
            <rect x="315" y="520" width="40" height="25" fill={legCount > 0 ? '#6366f1' : '#374151'} stroke="#4b5563" strokeWidth="3" rx="6" />
            <line x1="328" y1="410" x2="338" y2="410" stroke="#6b7280" strokeWidth="2" />
          </g>

          {/* Animated electricity when complete */}
          {isComplete && (
            <g className="animate-pulse">
              <circle cx="300" cy="150" r="75" fill="none" stroke="#39ff14" strokeWidth="2" opacity="0.5" />
            </g>
          )}
        </svg>
      </div>

      {/* Status Indicator */}
      <div className="absolute top-8 right-8 p-4 bg-bg-secondary border border-bg-tertiary rounded-lg shadow-lg">
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-3 h-3 rounded-full ${isComplete ? 'bg-neon-green animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-sm text-text-primary font-medium">Agent Status</span>
        </div>
        <div className="text-xs text-text-secondary space-y-1">
          <div>Head: {headCount > 0 ? '✓' : '○'}</div>
          <div>Arms: {armCount}/6</div>
          <div>Heart: {heartCount > 0 ? '✓' : '○'}</div>
          <div>Legs: {legCount > 0 ? '✓' : '○'}</div>
          <div>Spine: {spineCount > 0 ? '✓' : '○'}</div>
        </div>
      </div>

      {/* Instructions */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center text-text-dim">
            <p className="text-lg mb-2">Drag body parts from the left sidebar</p>
            <p className="text-sm">to build your Frankenstein AI Agent</p>
          </div>
        </div>
      )}
    </div>
  );
};
