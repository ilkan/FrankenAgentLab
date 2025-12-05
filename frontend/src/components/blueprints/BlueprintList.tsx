import { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getUserBlueprints, deleteBlueprint, BlueprintListItem } from '../../utils/blueprintApi';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Trash2, Edit, Play } from 'lucide-react';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog';

interface BlueprintListProps {
  onLoad?: (blueprintId: string) => void;
  onEdit?: (blueprintId: string) => void;
}

export function BlueprintList({ onLoad, onEdit }: BlueprintListProps) {
  const { token } = useAuth();
  const [blueprints, setBlueprints] = useState<BlueprintListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchBlueprints = async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const data = await getUserBlueprints(token);
      setBlueprints(data);
    } catch (error) {
      console.error('Failed to fetch blueprints:', error);
      toast.error('Failed to load blueprints');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBlueprints();
  }, [token]);

  const handleDelete = async () => {
    if (!deleteId || !token) return;

    setIsDeleting(true);
    try {
      await deleteBlueprint(token, deleteId);
      toast.success('Blueprint deleted');
      setBlueprints(blueprints.filter(b => b.id !== deleteId));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete blueprint';
      toast.error(message);
    } finally {
      setIsDeleting(false);
      setDeleteId(null);
    }
  };

  if (isLoading) {
    return <div className="text-gray-400 text-sm">Loading blueprints...</div>;
  }

  if (blueprints.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        <p className="text-sm">No blueprints yet</p>
        <p className="text-xs mt-2">Create your first agent to get started</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {blueprints.map((blueprint) => (
          <Card key={blueprint.id} className="p-4 bg-gray-800 border-gray-700 hover:border-gray-600 transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-gray-200 truncate">
                  {blueprint.name}
                </h3>
                {blueprint.description && (
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                    {blueprint.description}
                  </p>
                )}
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                  <span>v{blueprint.version}</span>
                  <span>•</span>
                  <span>Updated {new Date(blueprint.updated_at).toLocaleDateString()}</span>
                  {blueprint.is_public && (
                    <>
                      <span>•</span>
                      <span className="text-green-500">Public</span>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1 ml-2">
                {onLoad && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onLoad(blueprint.id)}
                    className="text-green-400 hover:text-green-300 hover:bg-green-950"
                    title="Load blueprint"
                  >
                    <Play className="w-4 h-4" />
                  </Button>
                )}
                {onEdit && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(blueprint.id)}
                    className="text-blue-400 hover:text-blue-300 hover:bg-blue-950"
                    title="Edit blueprint"
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDeleteId(blueprint.id)}
                  className="text-red-400 hover:text-red-300 hover:bg-red-950"
                  title="Delete blueprint"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent className="bg-gray-900 border-gray-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-gray-100">Delete Blueprint</AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              Are you sure you want to delete this blueprint? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-gray-800 text-gray-300 hover:bg-gray-700">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
