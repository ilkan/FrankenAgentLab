/**
 * Sidebar - Body parts library for drag-and-drop
 */

import { BODY_PARTS_LIBRARY } from '../types/agent-parts';
import { Brain, Zap, Footprints, Heart, Bone } from 'lucide-react';

const Sidebar = () => {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'heads':
        return <Brain className="w-5 h-5" />;
      case 'arms':
        return <Zap className="w-5 h-5" />;
      case 'legs':
        return <Footprints className="w-5 h-5" />;
      case 'hearts':
        return <Heart className="w-5 h-5" />;
      case 'spines':
        return <Bone className="w-5 h-5" />;
      default:
        return null;
    }
  };

  return (
    <div className="p-4 space-y-6">
      <div>
        <h2 className="text-sm font-bold text-neon-green mb-2">Body Parts Library</h2>
        <p className="text-xs text-text-dim">Drag parts onto the canvas</p>
      </div>

      {Object.entries(BODY_PARTS_LIBRARY).map(([category, parts]) => (
        <div key={category}>
          <div className="flex items-center gap-2 mb-3 text-text-secondary">
            {getCategoryIcon(category)}
            <h3 className="text-sm font-medium capitalize">{category}</h3>
          </div>
          <div className="space-y-2">
            {parts.map((part) => (
              <div
                key={part.id}
                draggable
                className="p-3 bg-bg-tertiary rounded border border-bg-tertiary hover:border-neon-green cursor-move transition-all hover:shadow-[0_0_10px_rgba(57,255,20,0.3)]"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: part.color }}
                  />
                  <span className="text-sm text-text-primary">{part.name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Sidebar;
