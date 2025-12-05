import { BODY_PARTS_LIBRARY } from '../types/agent-parts';
import { Brain, Wrench, Footprints, Heart, Shield } from 'lucide-react';
import { DraggableBodyPart } from './DraggableBodyPart';

// CSS to hide scrollbar
const hideScrollbarStyle = `
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
`;

export function BodyPartLibrary() {
  // Hidden items - not ready for production
  const HIDDEN_TOOLS = ['rag-knowledge', 'python-executor', 'groq-llama', 'kb-embeddings'];

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'heads':
        return (
          <div className="w-10 h-10 bg-purple-600/30 rounded-xl flex items-center justify-center flex-shrink-0">
            <Brain className="w-5 h-5 text-purple-400" />
          </div>
        );
      case 'arms':
        return (
          <div className="w-10 h-10 bg-blue-600/30 rounded-xl flex items-center justify-center flex-shrink-0">
            <Wrench className="w-5 h-5 text-blue-400" />
          </div>
        );
      case 'legs':
        return (
          <div className="w-10 h-10 bg-orange-600/30 rounded-xl flex items-center justify-center flex-shrink-0">
            <Footprints className="w-5 h-5 text-orange-400" />
          </div>
        );
      case 'hearts':
        return (
          <div className="w-10 h-10 bg-pink-600/30 rounded-xl flex items-center justify-center flex-shrink-0">
            <Heart className="w-5 h-5 text-pink-400" />
          </div>
        );
      case 'spines':
        return (
          <div className="w-10 h-10 bg-cyan-600/30 rounded-xl flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-cyan-400" />
          </div>
        );
      default:
        return null;
    }
  };

  // Filter out hidden tools from the library
  const filterParts = (parts: typeof BODY_PARTS_LIBRARY[keyof typeof BODY_PARTS_LIBRARY]) => {
    return parts.filter(part => !HIDDEN_TOOLS.includes(part.id));
  };

  return (
    <div className="w-full border-r border-gray-800 bg-gray-950 flex flex-col h-full overflow-hidden">
      <style>{hideScrollbarStyle}</style>
      <div className="p-6 border-b border-gray-800 flex-shrink-0">
        <h2 className="text-gray-100 mb-1">Body Part Library</h2>
        <p className="text-gray-400 text-sm">Drag parts onto the canvas</p>
      </div>
      
      <div className="flex-1 overflow-y-auto hide-scrollbar" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' } as React.CSSProperties}>
        <div className="p-4 space-y-6 pb-16">
          {Object.entries(BODY_PARTS_LIBRARY).map(([category, parts]) => {
            const filteredParts = filterParts(parts);
            return (
              <div key={category}>
                <div className="flex items-center gap-3 mb-3 text-gray-300">
                  {getCategoryIcon(category)}
                  <h3 className="capitalize font-medium">{category}</h3>
                </div>
                <div className="space-y-2">
                  {filteredParts.map((part) => (
                    <DraggableBodyPart key={part.id} part={part} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
