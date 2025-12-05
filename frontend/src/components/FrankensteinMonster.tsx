import { AgentConfiguration } from '../types/agent-parts';
import { Wrench } from 'lucide-react';

interface FrankensteinMonsterProps {
  config: AgentConfiguration;
}

export function FrankensteinMonster({ config }: FrankensteinMonsterProps) {
  const isComplete = config.head && config.leg;
  const toolCount = config.arms.length;

  return (
    <div className="relative w-[500px] h-[600px]">
      {/* Outer glow when complete */}
      {isComplete && (
        <div className="absolute inset-0 bg-green-500 opacity-20 blur-3xl rounded-full animate-pulse" />
      )}
      
      {/* Frame/Platform */}
      <div className="absolute -inset-8 border-2 border-gray-800 rounded-xl opacity-30" />
      
      <svg viewBox="0 0 400 500" className="w-full h-full drop-shadow-2xl">
        {/* Lightning bolts when complete */}
        {isComplete && (
          <>
            <g className="animate-pulse">
              <path
                d="M 180 20 L 160 50 L 180 50 L 160 80"
                stroke="#fbbf24"
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
              />
              <circle cx="180" cy="20" r="3" fill="#fbbf24" />
            </g>
            <g className="animate-pulse" style={{ animationDelay: '0.3s' }}>
              <path
                d="M 220 20 L 240 50 L 220 50 L 240 80"
                stroke="#fbbf24"
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
              />
              <circle cx="220" cy="20" r="3" fill="#fbbf24" />
            </g>
          </>
        )}

        {/* Spine/Back (behind body) */}
        <g opacity={config.spine ? "1" : "0.3"}>
          <rect
            x="180"
            y="190"
            width="40"
            height="160"
            fill={config.spine ? config.spine.color : '#57534e'}
            opacity="0.4"
            rx="6"
          />
          {config.spine && (
            <g>
              <circle cx="200" cy="220" r="3" fill="#2d3d2e" />
              <circle cx="200" cy="260" r="3" fill="#2d3d2e" />
              <circle cx="200" cy="300" r="3" fill="#2d3d2e" />
            </g>
          )}
        </g>

        {/* Head - Frankenstein style with flat top */}
        <g opacity={config.head ? "1" : "0.4"}>
          {/* Flat-top head shape */}
          <rect
            x="140"
            y="80"
            width="120"
            height="80"
            fill={config.head ? config.head.color : '#7c9d7f'}
            stroke="#2d3d2e"
            strokeWidth="3"
            rx="5"
          />
          
          {/* Hair/Top of head - darker */}
          <rect
            x="140"
            y="80"
            width="120"
            height="15"
            fill="#1a1a1a"
            rx="5"
          />

          {/* Forehead scar */}
          <path
            d="M 160 105 L 170 110 L 180 105 L 190 110 L 200 105 L 210 110 L 220 105 L 230 110 L 240 105"
            stroke="#2d3d2e"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
          />

          {/* Eyes - hollow and scary */}
          <ellipse cx="170" cy="125" rx="12" ry="15" fill="#1a1a1a" />
          <ellipse cx="230" cy="125" rx="12" ry="15" fill="#1a1a1a" />
          <circle cx="170" cy="125" r="6" fill={isComplete ? '#fbbf24' : '#4b5563'} className={isComplete ? 'animate-pulse' : ''} />
          <circle cx="230" cy="125" r="6" fill={isComplete ? '#fbbf24' : '#4b5563'} className={isComplete ? 'animate-pulse' : ''} />

          {/* Nose - flat and wide */}
          <ellipse cx="200" cy="138" rx="8" ry="6" fill="#5a755c" />

          {/* Mouth - stitched */}
          <path
            d="M 175 150 Q 200 155 225 150"
            stroke="#2d3d2e"
            strokeWidth="2"
            fill="none"
          />
          <line x1="180" y1="148" x2="180" y2="153" stroke="#2d3d2e" strokeWidth="2" />
          <line x1="190" y1="150" x2="190" y2="155" stroke="#2d3d2e" strokeWidth="2" />
          <line x1="200" y1="151" x2="200" y2="156" stroke="#2d3d2e" strokeWidth="2" />
          <line x1="210" y1="150" x2="210" y2="155" stroke="#2d3d2e" strokeWidth="2" />
          <line x1="220" y1="148" x2="220" y2="153" stroke="#2d3d2e" strokeWidth="2" />

          {/* Neck bolts - iconic Frankenstein feature */}
          <g>
            <rect x="125" y="145" width="15" height="25" fill="#6b7280" rx="2" />
            <rect x="128" y="148" width="9" height="6" fill="#9ca3af" rx="1" />
            <circle cx="132" cy="151" r="2" fill="#4b5563" />
          </g>
          <g>
            <rect x="260" y="145" width="15" height="25" fill="#6b7280" rx="2" />
            <rect x="263" y="148" width="9" height="6" fill="#9ca3af" rx="1" />
            <circle cx="267" cy="151" r="2" fill="#4b5563" />
          </g>
        </g>

        {/* Neck */}
        <rect
          x="170"
          y="160"
          width="60"
          height="30"
          fill={config.head ? config.head.color : '#7c9d7f'}
          opacity={config.head ? "0.9" : "0.4"}
        />

        {/* Body/Torso - muscular and stitched */}
        <g>
          <rect
            x="130"
            y="190"
            width="140"
            height="160"
            fill="#6b8a6e"
            stroke="#2d3d2e"
            strokeWidth="3"
            rx="10"
          />

          {/* Chest muscles definition */}
          <path
            d="M 200 210 L 200 280"
            stroke="#5a755c"
            strokeWidth="2"
            opacity="0.5"
          />
          <ellipse cx="165" cy="240" rx="25" ry="30" fill="#5a755c" opacity="0.3" />
          <ellipse cx="235" cy="240" rx="25" ry="30" fill="#5a755c" opacity="0.3" />

          {/* Center scar/stitches */}
          <line x1="200" y1="200" x2="200" y2="340" stroke="#2d3d2e" strokeWidth="2" strokeDasharray="5,5" />
        </g>

        {/* Tool Belt - Conceptual representation of arms/tools */}
        <g>
          {/* Belt */}
          <rect
            x="140"
            y="280"
            width="120"
            height="30"
            fill="#4a4a4a"
            stroke="#2d2d2d"
            strokeWidth="2"
            rx="5"
            opacity="0.8"
          />
          <rect
            x="185"
            y="283"
            width="30"
            height="24"
            fill="#6b6b6b"
            stroke="#2d2d2d"
            strokeWidth="1"
            rx="3"
          />
          
          {/* Tool slots on belt */}
          {[0, 1, 2, 3, 4, 5].map((index) => {
            const hasTool = index < toolCount;
            const x = 145 + (index % 3) * 35;
            const y = 285 + Math.floor(index / 3) * 12;
            
            return (
              <g key={index}>
                <rect
                  x={x}
                  y={y}
                  width={index % 3 === 1 ? 0 : 20}
                  height="8"
                  fill={hasTool ? config.arms[index]?.color || '#9ca3af' : '#2d2d2d'}
                  stroke="#1a1a1a"
                  strokeWidth="1"
                  rx="2"
                  opacity={hasTool ? "0.9" : "0.3"}
                />
              </g>
            );
          })}
        </g>

        {/* Heart position */}
        <g opacity={config.heart ? "1" : "0.3"}>
          <path
            d="M 200 230 L 220 250 L 200 275 L 180 250 Z"
            fill={config.heart ? config.heart.color : '#374151'}
            stroke="#2d3d2e"
            strokeWidth="2"
          />
          <circle cx="188" cy="243" r="10" fill={config.heart ? config.heart.color : '#374151'} stroke="#2d3d2e" strokeWidth="2" />
          <circle cx="212" cy="243" r="10" fill={config.heart ? config.heart.color : '#374151'} stroke="#2d3d2e" strokeWidth="2" />
          
          {config.heart && (
            <animateTransform
              attributeName="transform"
              type="scale"
              values="1;1.05;1"
              dur="0.8s"
              repeatCount="indefinite"
              additive="sum"
            />
          )}
        </g>

        {/* Single Leg - centered, more powerful */}
        <g opacity={config.leg ? "1" : "0.4"}>
          <rect
            x="170"
            y="350"
            width="60"
            height="110"
            fill={config.leg ? config.leg.color : '#6b8a6e'}
            stroke="#2d3d2e"
            strokeWidth="3"
            rx="10"
          />
          {/* Boot */}
          <rect
            x="160"
            y="460"
            width="80"
            height="30"
            fill="#1a1a1a"
            stroke="#2d3d2e"
            strokeWidth="3"
            rx="8"
          />
          {/* Stitches */}
          <line x1="180" y1="360" x2="190" y2="360" stroke="#2d3d2e" strokeWidth="2" />
          <line x1="210" y1="360" x2="220" y2="360" stroke="#2d3d2e" strokeWidth="2" />
          
          {/* Muscle definition */}
          <ellipse cx="200" cy="400" rx="20" ry="35" fill="#5a755c" opacity="0.3" />
        </g>
      </svg>

      {/* Tool count indicator */}
      {toolCount > 0 && (
        <div className="absolute bottom-32 left-1/2 transform -translate-x-1/2 bg-gray-900 border border-gray-700 rounded-full px-3 py-1 flex items-center gap-2">
          <Wrench className="w-4 h-4 text-purple-400" />
          <span className="text-sm text-gray-300">{toolCount} Tool{toolCount !== 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  );
}
