import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { MarketplaceListing, cloneBlueprint, rateBlueprint } from '../../utils/marketplaceApi';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Star, Copy, User } from 'lucide-react';
import { toast } from 'sonner';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '../ui/popover';

interface MarketplaceCardProps {
  listing: MarketplaceListing;
  onCloneSuccess?: () => void;
}

export function MarketplaceCard({ listing, onCloneSuccess }: MarketplaceCardProps) {
  const { token, isAuthenticated } = useAuth();
  const [isCloning, setIsCloning] = useState(false);
  const [isRating, setIsRating] = useState(false);
  const [showRating, setShowRating] = useState(false);

  const handleClone = async () => {
    if (!isAuthenticated || !token) {
      toast.error('Please log in to clone blueprints');
      return;
    }

    setIsCloning(true);
    try {
      await cloneBlueprint(token, listing.id);
      toast.success('Blueprint cloned to your collection');
      onCloneSuccess?.();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to clone blueprint';
      toast.error(message);
    } finally {
      setIsCloning(false);
    }
  };

  const handleRate = async (rating: number) => {
    if (!isAuthenticated || !token) {
      toast.error('Please log in to rate blueprints');
      return;
    }

    setIsRating(true);
    try {
      await rateBlueprint(token, listing.id, rating);
      toast.success('Rating submitted');
      setShowRating(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to rate blueprint';
      toast.error(message);
    } finally {
      setIsRating(false);
    }
  };

  const renderStars = (rating: number, interactive: boolean = false) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => interactive && handleRate(star)}
            disabled={!interactive || isRating}
            className={`${
              interactive ? 'cursor-pointer hover:scale-110 transition-transform' : 'cursor-default'
            }`}
          >
            <Star
              className={`w-4 h-4 ${
                star <= rating
                  ? 'fill-yellow-500 text-yellow-500'
                  : 'text-gray-600'
              }`}
            />
          </button>
        ))}
      </div>
    );
  };

  return (
    <Card className="p-4 bg-gray-800 border-gray-700 hover:border-gray-600 transition-colors">
      <div className="space-y-3">
        <div>
          <h3 className="text-base font-medium text-gray-200">
            {listing.name}
          </h3>
          {listing.description && (
            <p className="text-sm text-gray-400 mt-1 line-clamp-2">
              {listing.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-500">
          {listing.author_name && (
            <>
              <User className="w-3 h-3" />
              <span>{listing.author_name}</span>
              <span>•</span>
            </>
          )}
          <Copy className="w-3 h-3" />
          <span>{listing.clone_count} clones</span>
        </div>

        <div className="flex items-center justify-between">
          <Popover open={showRating} onOpenChange={setShowRating}>
            <PopoverTrigger asChild>
              <button className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                {renderStars(Math.round(listing.average_rating))}
                <span className="text-xs text-gray-400">
                  ({listing.rating_count})
                </span>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-3 bg-gray-900 border-gray-800">
              <div className="space-y-2">
                <p className="text-xs text-gray-400">Rate this blueprint</p>
                {renderStars(0, true)}
              </div>
            </PopoverContent>
          </Popover>

          <Button
            onClick={handleClone}
            disabled={isCloning}
            size="sm"
            className="gap-2"
          >
            <Copy className="w-3 h-3" />
            {isCloning ? 'Cloning...' : 'Clone'}
          </Button>
        </div>
      </div>
    </Card>
  );
}
