/**
 * Preview Panel - Shows live blueprint preview and export options
 */

import { useState } from 'react';
import { useBlueprintStore } from '../stores/blueprintStore';
import { exportAsYAML, exportAsJSON } from '../utils/blueprintConverter';
import { Download, FileJson, FileCode, AlertCircle, CheckCircle } from 'lucide-react';

const PreviewPanel = () => {
  const {
    generateBlueprintPreview,
    validateCurrentBlueprint,
    exportBlueprint,
    blueprintName,
    blueprintDescription,
    setBlueprintName,
    setBlueprintDescription,
  } = useBlueprintStore();

  const [previewFormat, setPreviewFormat] = useState<'yaml' | 'json'>('yaml');
  const [isEditing, setIsEditing] = useState(false);

  const blueprint = generateBlueprintPreview();
  const validation = validateCurrentBlueprint();

  const previewContent = blueprint
    ? previewFormat === 'yaml'
      ? exportAsYAML(blueprint)
      : exportAsJSON(blueprint)
    : '';

  const handleExport = () => {
    try {
      exportBlueprint(previewFormat);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-bg-tertiary">
        <h2 className="text-lg font-bold text-neon-green mb-1">Blueprint Preview</h2>
        <p className="text-xs text-text-dim">Live preview of your agent configuration</p>
      </div>

      {/* Metadata Editor */}
      <div className="p-4 border-b border-bg-tertiary space-y-3">
        <div>
          <label className="text-xs text-text-secondary mb-1 block">Agent Name</label>
          {isEditing ? (
            <input
              type="text"
              value={blueprintName}
              onChange={(e) => setBlueprintName(e.target.value)}
              onBlur={() => setIsEditing(false)}
              className="w-full px-3 py-2 bg-bg-tertiary border border-bg-tertiary rounded text-sm text-text-primary focus:outline-none focus:border-neon-green"
              autoFocus
            />
          ) : (
            <div
              onClick={() => setIsEditing(true)}
              className="w-full px-3 py-2 bg-bg-tertiary rounded text-sm text-text-primary cursor-pointer hover:border hover:border-neon-green"
            >
              {blueprintName}
            </div>
          )}
        </div>

        <div>
          <label className="text-xs text-text-secondary mb-1 block">Description</label>
          <textarea
            value={blueprintDescription}
            onChange={(e) => setBlueprintDescription(e.target.value)}
            className="w-full px-3 py-2 bg-bg-tertiary border border-bg-tertiary rounded text-sm text-text-primary focus:outline-none focus:border-neon-green resize-none"
            rows={2}
          />
        </div>
      </div>

      {/* Validation Status */}
      <div className="p-4 border-b border-bg-tertiary">
        {validation.valid ? (
          <div className="flex items-center gap-2 text-neon-green text-sm">
            <CheckCircle className="w-4 h-4" />
            <span>Blueprint is valid</span>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>Blueprint has errors</span>
            </div>
            <ul className="text-xs text-red-300 space-y-1 ml-6">
              {validation.errors.map((error, idx) => (
                <li key={idx}>• {error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Format Toggle */}
      <div className="p-4 border-b border-bg-tertiary">
        <div className="flex gap-2">
          <button
            onClick={() => setPreviewFormat('yaml')}
            className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
              previewFormat === 'yaml'
                ? 'bg-neon-green text-bg-primary'
                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-tertiary/80'
            }`}
          >
            <FileCode className="w-4 h-4 inline mr-1" />
            YAML
          </button>
          <button
            onClick={() => setPreviewFormat('json')}
            className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
              previewFormat === 'json'
                ? 'bg-neon-green text-bg-primary'
                : 'bg-bg-tertiary text-text-secondary hover:bg-bg-tertiary/80'
            }`}
          >
            <FileJson className="w-4 h-4 inline mr-1" />
            JSON
          </button>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1 overflow-auto lab-scrollbar">
        {blueprint ? (
          <pre className="p-4 text-xs text-text-primary font-mono whitespace-pre-wrap break-words">
            {previewContent}
          </pre>
        ) : (
          <div className="p-4 text-sm text-text-dim text-center">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Add required parts to see preview</p>
            <p className="text-xs mt-1">Head and Execution Mode are required</p>
          </div>
        )}
      </div>

      {/* Export Button */}
      <div className="p-4 border-t border-bg-tertiary">
        <button
          onClick={handleExport}
          disabled={!validation.valid}
          className={`w-full px-4 py-3 rounded font-medium transition-all flex items-center justify-center gap-2 ${
            validation.valid
              ? 'bg-neon-green text-bg-primary hover:shadow-[0_0_20px_rgba(57,255,20,0.5)] hover:scale-105'
              : 'bg-bg-tertiary text-text-dim cursor-not-allowed'
          }`}
        >
          <Download className="w-4 h-4" />
          Export Blueprint ({previewFormat.toUpperCase()})
        </button>
        {validation.valid && (
          <p className="text-xs text-text-dim text-center mt-2">
            Downloads to: {blueprintName.toLowerCase().replace(/\s+/g, '_')}.{previewFormat}
          </p>
        )}
      </div>
    </div>
  );
};

export default PreviewPanel;
