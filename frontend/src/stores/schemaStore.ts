/**
 * Schema Store - Manages component configuration schemas
 * 
 * Fetches and caches schemas from the backend for form generation and validation
 */

import { create } from 'zustand';
import { ComponentSchemas, getComponentSchemas } from '../utils/api';

interface SchemaState {
  // Schema data
  schemas: ComponentSchemas | null;
  
  // Loading state
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchSchemas: () => Promise<void>;
  clearError: () => void;
}

export const useSchemaStore = create<SchemaState>((set) => ({
  // Initial state
  schemas: null,
  isLoading: false,
  error: null,
  
  // Fetch schemas from backend
  fetchSchemas: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const schemas = await getComponentSchemas();
      set({ schemas, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch schemas';
      set({ error: errorMessage, isLoading: false });
      console.error('Failed to fetch component schemas:', error);
    }
  },
  
  // Clear error state
  clearError: () => {
    set({ error: null });
  },
}));
