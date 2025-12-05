import { AgentConfiguration } from '../types/agent-parts';
import { Sparkles } from 'lucide-react';

interface FrankensteinAgentProps {
  config: AgentConfiguration;
  onSlotClick: (slot: keyof AgentConfiguration) => void;
}

export function FrankensteinAgent({ config, onSlotClick }: FrankensteinAgentProps) {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {/* Background grid */}
      <div className="absolute inset-0 opacity-10">
        <div className="w-full h-full" style={{
          backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)',
          backgroundSize: '30px 30px'
        }} />
      </div>

      {/* Frankenstein Agent */}
      <svg viewBox="0 0 600 800" className="w-full max-w-2xl h-full max-h-[800px]">
        {/* Spine (background) */}
        <g>
          <rect
            x="275"
            y="200"
            width="50"
            height="280"
            fill={config.spine ? config.spine.color : '#374151'}
            opacity="0.3"
            rx="8"
            className="cursor-pointer hover:opacity-50 transition-opacity"
            onClick={() => onSlotClick('spine')}
          />
          {config.spine && (
            <text x="300" y="340" textAnchor="middle" fill="white" fontSize="12" className="pointer-events-none">
              {config.spine.name}
            </text>
          )}
          {!config.spine && (
            <text x="300" y="340" textAnchor="middle" fill="#9ca3af" fontSize="10" className="pointer-events-none">
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
            fill={config.head ? config.head.color : '#1f2937'}
            stroke="#4b5563"
            strokeWidth="3"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('head')}
          />
          <circle cx="280" cy="140" r="8" fill="white" opacity="0.9" />
          <circle cx="320" cy="140" r="8" fill="white" opacity="0.9" />
          <circle cx="282" cy="142" r="4" fill="#1f2937" />
          <circle cx="322" cy="142" r="4" fill="#1f2937" />
          
          {/* Frankenstein bolts */}
          <rect x="225" y="145" width="12" height="20" fill="#6b7280" rx="2" />
          <rect x="363" y="145" width="12" height="20" fill="#6b7280" rx="2" />
          
          {/* Stitches on head */}
          <line x1="270" y1="100" x2="280" y2="100" stroke="#6b7280" strokeWidth="2" />
          <line x1="320" y1="100" x2="330" y2="100" stroke="#6b7280" strokeWidth="2" />
          <line x1="285" y1="105" x2="315" y2="105" stroke="#6b7280" strokeWidth="2" strokeDasharray="5,5" />
          
          {config.head && (
            <text x="300" y="190" textAnchor="middle" fill="white" fontSize="11" className="pointer-events-none">
              {config.head.name}
            </text>
          )}
          {!config.head && (
            <text x="300" y="155" textAnchor="middle" fill="#9ca3af" fontSize="10" className="pointer-events-none">
              Head (LLM)
            </text>
          )}
        </g>

        {/* Body/Torso */}
        <rect
          x="230"
          y="220"
          width="140"
          height="180"
          fill="#1f2937"
          stroke="#4b5563"
          strokeWidth="3"
          rx="10"
        />

        {/* Heart */}
        <g>
          <path
            d="M 300 280 L 320 300 L 300 330 L 280 300 Z"
            fill={config.heart ? config.heart.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="2"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('heart')}
          />
          <circle cx="288" cy="292" r="10" fill={config.heart ? config.heart.color : '#374151'} stroke="#4b5563" strokeWidth="2" />
          <circle cx="312" cy="292" r="10" fill={config.heart ? config.heart.color : '#374151'} stroke="#4b5563" strokeWidth="2" />
          
          {config.heart && (
            <>
              <animateTransform
                attributeName="transform"
                type="scale"
                values="1;1.1;1"
                dur="1s"
                repeatCount="indefinite"
                additive="sum"
              />
              <text x="300" y="360" textAnchor="middle" fill="white" fontSize="10" className="pointer-events-none">
                {config.heart.name}
              </text>
            </>
          )}
          {!config.heart && (
            <text x="300" y="350" textAnchor="middle" fill="#9ca3af" fontSize="10" className="pointer-events-none">
              Heart
            </text>
          )}
        </g>

        {/* Left Arm */}
        <g>
          <rect
            x="140"
            y="240"
            width="80"
            height="25"
            fill={config.armLeft ? config.armLeft.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="8"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('armLeft')}
          />
          <rect
            x="100"
            y="265"
            width="40"
            height="80"
            fill={config.armLeft ? config.armLeft.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="8"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('armLeft')}
          />
          {/* Stitches */}
          <line x1="145" y1="252" x2="155" y2="252" stroke="#6b7280" strokeWidth="2" />
          <line x1="165" y1="252" x2="175" y2="252" stroke="#6b7280" strokeWidth="2" />
          
          {config.armLeft && (
            <text x="120" y="310" textAnchor="middle" fill="white" fontSize="9" className="pointer-events-none">
              {config.armLeft.name.split(' ')[0]}
            </text>
          )}
          {!config.armLeft && (
            <text x="120" y="310" textAnchor="middle" fill="#9ca3af" fontSize="9" className="pointer-events-none">
              Left Tool
            </text>
          )}
        </g>

        {/* Right Arm */}
        <g>
          <rect
            x="380"
            y="240"
            width="80"
            height="25"
            fill={config.armRight ? config.armRight.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="8"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('armRight')}
          />
          <rect
            x="460"
            y="265"
            width="40"
            height="80"
            fill={config.armRight ? config.armRight.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="8"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('armRight')}
          />
          {/* Stitches */}
          <line x1="425" y1="252" x2="435" y2="252" stroke="#6b7280" strokeWidth="2" />
          <line x1="445" y1="252" x2="455" y2="252" stroke="#6b7280" strokeWidth="2" />
          
          {config.armRight && (
            <text x="480" y="310" textAnchor="middle" fill="white" fontSize="9" className="pointer-events-none">
              {config.armRight.name.split(' ')[0]}
            </text>
          )}
          {!config.armRight && (
            <text x="480" y="310" textAnchor="middle" fill="#9ca3af" fontSize="9" className="pointer-events-none">
              Right Tool
            </text>
          )}
        </g>

        {/* Left Leg */}
        <g>
          <rect
            x="245"
            y="400"
            width="35"
            height="120"
            fill={config.legLeft ? config.legLeft.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="8"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('legLeft')}
          />
          <rect
            x="245"
            y="520"
            width="40"
            height="25"
            fill={config.legLeft ? config.legLeft.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="6"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('legLeft')}
          />
          {/* Stitches */}
          <line x1="252" y1="410" x2="262" y2="410" stroke="#6b7280" strokeWidth="2" />
          
          {config.legLeft && (
            <text x="262" y="465" textAnchor="middle" fill="white" fontSize="9" className="pointer-events-none">
              {config.legLeft.name}
            </text>
          )}
          {!config.legLeft && (
            <text x="262" y="465" textAnchor="middle" fill="#9ca3af" fontSize="9" className="pointer-events-none">
              Left Leg
            </text>
          )}
        </g>

        {/* Right Leg */}
        <g>
          <rect
            x="320"
            y="400"
            width="35"
            height="120"
            fill={config.legRight ? config.legRight.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="8"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('legRight')}
          />
          <rect
            x="315"
            y="520"
            width="40"
            height="25"
            fill={config.legRight ? config.legRight.color : '#374151'}
            stroke="#4b5563"
            strokeWidth="3"
            rx="6"
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSlotClick('legRight')}
          />
          {/* Stitches */}
          <line x1="328" y1="410" x2="338" y2="410" stroke="#6b7280" strokeWidth="2" />
          
          {config.legRight && (
            <text x="337" y="465" textAnchor="middle" fill="white" fontSize="9" className="pointer-events-none">
              {config.legRight.name}
            </text>
          )}
          {!config.legRight && (
            <text x="337" y="465" textAnchor="middle" fill="#9ca3af" fontSize="9" className="pointer-events-none">
              Right Leg
            </text>
          )}
        </g>

        {/* Animated electricity bolts when agent is complete */}
        {config.head && config.heart && (
          <g className="animate-pulse">
            <Sparkles className="w-6 h-6" style={{ x: 260, y: 80 }} />
          </g>
        )}
      </svg>

      {/* Agent status indicator */}
      <div className="absolute top-8 right-8 p-4 bg-gray-900 border border-gray-700 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-3 h-3 rounded-full ${config.head && config.heart ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-sm text-gray-300">Agent Status</span>
        </div>
        <div className="text-xs text-gray-500 space-y-1">
          <div>Head: {config.head ? '✓' : '○'}</div>
          <div>Arms: {config.armLeft || config.armRight ? '✓' : '○'}</div>
          <div>Heart: {config.heart ? '✓' : '○'}</div>
          <div>Legs: {config.legLeft || config.legRight ? '✓' : '○'}</div>
          <div>Spine: {config.spine ? '✓' : '○'}</div>
        </div>
      </div>
    </div>
  );
}
