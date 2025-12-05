import { useDrag } from 'react-dnd';
import { BodyPart } from '../types/agent-parts';
import { Badge } from './ui/badge';
import { GripVertical } from 'lucide-react';

interface DraggableBodyPartProps {
  part: BodyPart;
}

export function DraggableBodyPart({ part }: DraggableBodyPartProps) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'BODY_PART',
    item: part,
    canDrag: !part.comingSoon,
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  return (
    <div
      ref={part.comingSoon ? null : drag}
      className={`w-full p-3 rounded-lg border transition-all ${
        part.comingSoon 
          ? 'border-gray-800 bg-gray-900/50 opacity-60 cursor-not-allowed' 
          : 'border-gray-700 bg-gray-900 hover:bg-gray-800 hover:border-gray-600 cursor-move group'
      } ${isDragging ? 'opacity-50' : ''}`}
    >
      <div className="flex items-center gap-2">
        {!part.comingSoon && (
          <GripVertical className="w-4 h-4 text-gray-600 group-hover:text-gray-400" />
        )}
        <div className="flex-1 min-w-0">
          <span className={`text-sm truncate block ${part.comingSoon ? 'text-gray-500' : 'text-gray-200'}`}>
            {part.name}
          </span>
        </div>
        {part.comingSoon ? (
          <Badge 
            variant="outline"
            className="text-xs flex-shrink-0 font-medium"
            style={{ 
              borderColor: 'rgba(202, 138, 4, 0.5)', 
              color: '#eab308', 
              backgroundColor: 'rgba(113, 63, 18, 0.2)' 
            }}
          >
            Soon
          </Badge>
        ) : (
          <Badge 
            className="text-xs flex-shrink-0"
            style={{ backgroundColor: part.color, borderColor: part.color }}
          >
            {part.category}
          </Badge>
        )}
      </div>
    </div>
  );
}
