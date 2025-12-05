import { useEffect, useState } from 'react';
import { searchMarketplace, MarketplaceListing } from '../../utils/marketplaceApi';
import { MarketplaceCard } from './MarketplaceCard';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';

interface MarketplaceBrowserProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCloneSuccess?: () => void;
}

export function MarketplaceBrowser({ open, onOpenChange, onCloneSuccess }: MarketplaceBrowserProps) {
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 12;

  const fetchListings = async (query: string = '', page: number = 1) => {
    setIsLoading(true);
    try {
      const response = await searchMarketplace(query || undefined, page, pageSize);
      setListings(response.listings);
      setTotal(response.total);
      setTotalPages(Math.ceil(response.total / pageSize));
      setCurrentPage(page);
    } catch (error) {
      console.error('Failed to fetch marketplace:', error);
      toast.error('Failed to load marketplace');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      fetchListings();
    }
  }, [open]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchListings(searchQuery, 1);
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      fetchListings(searchQuery, newPage);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] bg-gray-900 border-gray-800">
        <DialogHeader>
          <DialogTitle className="text-gray-100">Agent Marketplace</DialogTitle>
          <DialogDescription className="text-gray-400">
            Discover and clone pre-built agents from the community
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                type="text"
                placeholder="Search blueprints..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-gray-800 border-gray-700"
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              Search
            </Button>
          </form>

          {/* Results */}
          <div className="overflow-y-auto max-h-[50vh] pr-2">
            {isLoading ? (
              <div className="text-center py-8 text-gray-400">
                Loading marketplace...
              </div>
            ) : listings.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p className="text-sm">No blueprints found</p>
                {searchQuery && (
                  <p className="text-xs mt-2">Try a different search term</p>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {listings.map((listing) => (
                  <MarketplaceCard
                    key={listing.id}
                    listing={listing}
                    onCloneSuccess={() => {
                      onCloneSuccess?.();
                      fetchListings(searchQuery, currentPage);
                    }}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-gray-800">
              <div className="text-sm text-gray-400">
                Showing {(currentPage - 1) * pageSize + 1}-
                {Math.min(currentPage * pageSize, total)} of {total}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1 || isLoading}
                  className="bg-gray-800 border-gray-700"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <span className="text-sm text-gray-400">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages || isLoading}
                  className="bg-gray-800 border-gray-700"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
