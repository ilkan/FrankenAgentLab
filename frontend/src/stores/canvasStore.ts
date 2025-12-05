/**
 * Canvas Store - Manages canvas state for node-based editor
 * 
 * Handles nodes, edges, selection, undo/redo, and canvas operations
 */

import { create } from 'zustand';

export interface CanvasNode {
  id: string;
  type: 'head' | 'arm' | 'leg' | 'heart' | 'spine';
  position: { x: number; y: number };
  data: {
    label: string;
    color: string;
    config: Record<string, any>;
  };
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
}

interface CanvasState {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  selectedNodeIds: string[];
  history: Array<{ nodes: CanvasNode[]; edges: CanvasEdge[] }>;
  historyIndex: number;
  
  // Actions
  addNode: (node: CanvasNode) => void;
  removeNode: (nodeId: string) => void;
  updateNode: (nodeId: string, updates: Partial<CanvasNode>) => void;
  setSelectedNodes: (nodeIds: string[]) => void;
  
  // History
  undo: () => void;
  redo: () => void;
  
  // Canvas operations
  loadCanvas: (state: { nodes: CanvasNode[]; edges: CanvasEdge[]; timestamp: number }) => void;
  clearCanvas: () => void;
}

let markUnsavedChangesCallback: (() => void) | null = null;

export const setMarkUnsavedChangesCallback = (callback: () => void) => {
  markUnsavedChangesCallback = callback;
};

export const useCanvasStore = create<CanvasState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeIds: [],
  history: [],
  historyIndex: -1,
  
  addNode: (node) => {
    set((state) => {
      const newNodes = [...state.nodes, node];
      const newHistory = state.history.slice(0, state.historyIndex + 1);
      newHistory.push({ nodes: newNodes, edges: state.edges });
      
      if (markUnsavedChangesCallback) {
        markUnsavedChangesCallback();
      }
      
      return {
        nodes: newNodes,
        history: newHistory,
        historyIndex: newHistory.length - 1,
      };
    });
  },
  
  removeNode: (nodeId) => {
    set((state) => {
      const newNodes = state.nodes.filter((n) => n.id !== nodeId);
      const newHistory = state.history.slice(0, state.historyIndex + 1);
      newHistory.push({ nodes: newNodes, edges: state.edges });
      
      if (markUnsavedChangesCallback) {
        markUnsavedChangesCallback();
      }
      
      return {
        nodes: newNodes,
        selectedNodeIds: state.selectedNodeIds.filter((id) => id !== nodeId),
        history: newHistory,
        historyIndex: newHistory.length - 1,
      };
    });
  },
  
  updateNode: (nodeId, updates) => {
    set((state) => {
      const newNodes = state.nodes.map((n) =>
        n.id === nodeId ? { ...n, ...updates } : n
      );
      const newHistory = state.history.slice(0, state.historyIndex + 1);
      newHistory.push({ nodes: newNodes, edges: state.edges });
      
      if (markUnsavedChangesCallback) {
        markUnsavedChangesCallback();
      }
      
      return {
        nodes: newNodes,
        history: newHistory,
        historyIndex: newHistory.length - 1,
      };
    });
  },
  
  setSelectedNodes: (nodeIds) => {
    set({ selectedNodeIds: nodeIds });
  },
  
  undo: () => {
    set((state) => {
      if (state.historyIndex > 0) {
        const newIndex = state.historyIndex - 1;
        const historyState = state.history[newIndex];
        return {
          nodes: historyState.nodes,
          edges: historyState.edges,
          historyIndex: newIndex,
        };
      }
      return state;
    });
  },
  
  redo: () => {
    set((state) => {
      if (state.historyIndex < state.history.length - 1) {
        const newIndex = state.historyIndex + 1;
        const historyState = state.history[newIndex];
        return {
          nodes: historyState.nodes,
          edges: historyState.edges,
          historyIndex: newIndex,
        };
      }
      return state;
    });
  },
  
  loadCanvas: (state) => {
    set({
      nodes: state.nodes,
      edges: state.edges,
      history: [{ nodes: state.nodes, edges: state.edges }],
      historyIndex: 0,
    });
  },
  
  clearCanvas: () => {
    set({
      nodes: [],
      edges: [],
      selectedNodeIds: [],
      history: [{ nodes: [], edges: [] }],
      historyIndex: 0,
    });
    
    if (markUnsavedChangesCallback) {
      markUnsavedChangesCallback();
    }
  },
}));
