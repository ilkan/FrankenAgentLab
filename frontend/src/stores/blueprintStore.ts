/**
 * Blueprint Store - Manages blueprint state and operations
 * 
 * Handles blueprint creation, validation, export, and API communication
 */

import { create } from 'zustand';
import { AgentConfiguration } from '../types/agent-parts';
import {
  convertToBlueprint,
  downloadBlueprint,
  validateBlueprint,
  BlueprintFormat,
} from '../utils/blueprintConverter';

interface BlueprintState {
  // Current agent configuration
  agentConfig: AgentConfiguration;
  
  // Blueprint metadata
  blueprintName: string;
  blueprintDescription: string;
  
  // State flags
  hasUnsavedChanges: boolean;
  isExporting: boolean;
  
  // Actions
  setAgentConfig: (config: AgentConfiguration) => void;
  setBlueprintName: (name: string) => void;
  setBlueprintDescription: (description: string) => void;
  setHasUnsavedChanges: (hasChanges: boolean) => void;
  
  // Blueprint operations
  exportBlueprint: (format: 'yaml' | 'json') => void;
  validateCurrentBlueprint: () => { valid: boolean; errors: string[] };
  generateBlueprintPreview: () => BlueprintFormat | null;
  
  // API operations (for future backend integration)
  saveToBackend: () => Promise<void>;
  loadFromBackend: (blueprintId: string) => Promise<void>;
}

export const useBlueprintStore = create<BlueprintState>((set, get) => ({
  // Initial state
  agentConfig: { arms: [] },
  blueprintName: 'Untitled Agent',
  blueprintDescription: 'Agent created with Frankenstein Builder',
  hasUnsavedChanges: false,
  isExporting: false,
  
  // State setters
  setAgentConfig: (config) => {
    set({ agentConfig: config, hasUnsavedChanges: true });
  },
  
  setBlueprintName: (name) => {
    set({ blueprintName: name, hasUnsavedChanges: true });
  },
  
  setBlueprintDescription: (description) => {
    set({ blueprintDescription: description, hasUnsavedChanges: true });
  },
  
  setHasUnsavedChanges: (hasChanges) => {
    set({ hasUnsavedChanges: hasChanges });
  },
  
  // Blueprint operations
  exportBlueprint: (format) => {
    const { agentConfig, blueprintName, blueprintDescription } = get();
    
    try {
      set({ isExporting: true });
      
      const blueprint = convertToBlueprint(
        agentConfig,
        blueprintName,
        blueprintDescription
      );
      
      downloadBlueprint(blueprint, format);
      set({ hasUnsavedChanges: false });
      
      console.log('Blueprint exported successfully:', blueprint);
    } catch (error) {
      console.error('Failed to export blueprint:', error);
      throw error;
    } finally {
      set({ isExporting: false });
    }
  },
  
  validateCurrentBlueprint: () => {
    const { agentConfig } = get();
    return validateBlueprint(agentConfig);
  },
  
  generateBlueprintPreview: () => {
    const { agentConfig, blueprintName, blueprintDescription } = get();
    
    try {
      return convertToBlueprint(agentConfig, blueprintName, blueprintDescription);
    } catch (error) {
      console.error('Failed to generate blueprint preview:', error);
      return null;
    }
  },
  
  // API operations (placeholder for backend integration)
  saveToBackend: async () => {
    const { agentConfig, blueprintName, blueprintDescription } = get();
    
    try {
      const blueprint = convertToBlueprint(
        agentConfig,
        blueprintName,
        blueprintDescription
      );
      
      // TODO: Implement API call to backend
      const response = await fetch('/api/blueprints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(blueprint),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save blueprint to backend');
      }
      
      set({ hasUnsavedChanges: false });
      console.log('Blueprint saved to backend');
    } catch (error) {
      console.error('Failed to save to backend:', error);
      throw error;
    }
  },
  
  loadFromBackend: async (blueprintId: string) => {
    try {
      // TODO: Implement API call to backend
      const response = await fetch(`/api/blueprints/${blueprintId}`);
      
      if (!response.ok) {
        throw new Error('Failed to load blueprint from backend');
      }
      
      const blueprint: BlueprintFormat = await response.json();
      
      // TODO: Convert blueprint back to AgentConfiguration
      // This requires reverse mapping from backend format to frontend format
      
      console.log('Blueprint loaded from backend:', blueprint);
    } catch (error) {
      console.error('Failed to load from backend:', error);
      throw error;
    }
  },
}));
