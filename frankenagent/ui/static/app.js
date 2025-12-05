/**
 * FrankenAgent Lab - Web UI JavaScript
 * Handles API interaction for blueprint listing and agent execution
 */

// API base URL - defaults to current origin
const API_BASE_URL = window.location.origin;

// Global state
let selectedBlueprint = null;
let isExecuting = false;

/**
 * Load and display available blueprints from the API
 */
async function loadBlueprints() {
    const blueprintsContainer = document.getElementById('blueprints-list');
    
    try {
        blueprintsContainer.innerHTML = '<div class="loading">Loading blueprints</div>';
        
        const response = await fetch(`${API_BASE_URL}/blueprints`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.blueprints || data.blueprints.length === 0) {
            blueprintsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>No blueprints found</p>
                    <p style="font-size: 0.9em; color: #666; margin-top: 10px;">
                        Add blueprint files to the blueprints/ directory
                    </p>
                </div>
            `;
            return;
        }
        
        // Clear loading state
        blueprintsContainer.innerHTML = '';
        
        // Create blueprint items
        for (const blueprintId of data.blueprints) {
            // Fetch detailed info for each blueprint
            try {
                const detailResponse = await fetch(`${API_BASE_URL}/blueprints/${blueprintId}`);
                const blueprint = await detailResponse.json();
                
                const blueprintItem = createBlueprintItem(blueprintId, blueprint);
                blueprintsContainer.appendChild(blueprintItem);
            } catch (error) {
                console.error(`Failed to load blueprint ${blueprintId}:`, error);
                // Create a basic item without details
                const blueprintItem = createBlueprintItem(blueprintId, {
                    name: blueprintId,
                    description: 'Details unavailable',
                    version: 'unknown'
                });
                blueprintsContainer.appendChild(blueprintItem);
            }
        }
        
    } catch (error) {
        console.error('Failed to load blueprints:', error);
        blueprintsContainer.innerHTML = `
            <div class="error-message">
                <div class="error-label">Failed to load blueprints</div>
                <div>${error.message}</div>
            </div>
        `;
    }
}

/**
 * Create a blueprint list item element
 */
function createBlueprintItem(blueprintId, blueprint) {
    const item = document.createElement('div');
    item.className = 'blueprint-item';
    item.onclick = () => selectBlueprint(blueprintId, blueprint);
    
    item.innerHTML = `
        <div class="blueprint-name">${blueprint.name || blueprintId}</div>
        <div class="blueprint-description">${blueprint.description || 'No description'}</div>
        <div class="blueprint-version">v${blueprint.version || '1.0'}</div>
    `;
    
    return item;
}

/**
 * Select a blueprint and show the chat interface
 */
function selectBlueprint(blueprintId, blueprint) {
    selectedBlueprint = {
        id: blueprintId,
        ...blueprint
    };
    
    // Update UI to show selected blueprint
    const blueprintItems = document.querySelectorAll('.blueprint-item');
    blueprintItems.forEach(item => item.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    
    // Show chat container
    document.getElementById('chat-container').classList.add('active');
    document.getElementById('empty-state').style.display = 'none';
    
    // Update selected blueprint info
    document.getElementById('selected-blueprint-name').textContent = blueprint.name || blueprintId;
    document.getElementById('selected-blueprint-description').textContent = blueprint.description || '';
    
    // Clear previous responses
    document.getElementById('responses-container').innerHTML = '';
    
    // Focus on message input
    document.getElementById('message-input').focus();
}

/**
 * Send message to the selected agent
 */
async function sendMessage() {
    if (!selectedBlueprint) {
        alert('Please select a blueprint first');
        return;
    }
    
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) {
        alert('Please enter a message');
        return;
    }
    
    if (isExecuting) {
        return; // Prevent multiple simultaneous requests
    }
    
    // Disable input during execution
    isExecuting = true;
    const sendButton = document.getElementById('send-button');
    sendButton.disabled = true;
    sendButton.textContent = 'Sending...';
    messageInput.disabled = true;
    
    // Clear input
    messageInput.value = '';
    
    // Add user message to responses
    const responsesContainer = document.getElementById('responses-container');
    const responseItem = document.createElement('div');
    responseItem.className = 'response-item';
    
    responseItem.innerHTML = `
        <div class="user-message">
            <div class="user-message-label">You:</div>
            <div class="response-text">${escapeHtml(message)}</div>
        </div>
        <div class="agent-response">
            <div class="agent-response-label">Agent:</div>
            <div class="response-text loading">Thinking</div>
        </div>
    `;
    
    responsesContainer.appendChild(responseItem);
    
    // Scroll to bottom
    responseItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
    
    try {
        const response = await fetch(`${API_BASE_URL}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                blueprint_id: selectedBlueprint.id,
                message: message
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display response
        displayResponse(responseItem, data);
        
    } catch (error) {
        console.error('Execution error:', error);
        
        // Display error
        const agentResponse = responseItem.querySelector('.agent-response .response-text');
        agentResponse.className = 'response-text';
        agentResponse.innerHTML = `
            <div class="error-message">
                <div class="error-label">Execution Failed</div>
                <div>${escapeHtml(error.message)}</div>
            </div>
        `;
    } finally {
        // Re-enable input
        isExecuting = false;
        sendButton.disabled = false;
        sendButton.textContent = 'Send';
        messageInput.disabled = false;
        messageInput.focus();
    }
}

/**
 * Display agent response and execution trace
 */
function displayResponse(responseItem, data) {
    const agentResponse = responseItem.querySelector('.agent-response .response-text');
    
    // Display agent response text
    agentResponse.className = 'response-text';
    agentResponse.textContent = data.response || 'No response';
    
    // Display execution trace if available
    if (data.execution_trace && data.execution_trace.length > 0) {
        const traceHtml = formatExecutionTrace(data.execution_trace, data.total_duration_ms);
        responseItem.insertAdjacentHTML('beforeend', traceHtml);
    }
    
    // Scroll to show the complete response
    responseItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/**
 * Format execution trace as HTML
 */
function formatExecutionTrace(trace, totalDuration) {
    let html = `
        <div class="execution-trace">
            <div class="trace-header">
                <span>🔧 Execution Trace (${trace.length} tool call${trace.length !== 1 ? 's' : ''})</span>
                <span class="trace-duration">Total: ${totalDuration.toFixed(2)}ms</span>
            </div>
            <div class="trace-items">
    `;
    
    trace.forEach((item, index) => {
        html += `
            <div class="trace-item">
                <div class="trace-tool-name">${index + 1}. ${escapeHtml(item.tool_name)}</div>
                <div class="trace-timestamp">⏱️ ${item.timestamp} (${item.duration_ms.toFixed(2)}ms)</div>
                <div class="trace-details">
                    <div class="trace-inputs">
                        <span class="trace-label">Inputs:</span>
                        <pre>${escapeHtml(JSON.stringify(item.inputs, null, 2))}</pre>
                    </div>
                    <div class="trace-outputs">
                        <span class="trace-label">Outputs:</span>
                        <pre>${escapeHtml(formatOutput(item.outputs))}</pre>
                    </div>
        `;
        
        if (item.error) {
            html += `
                    <div class="trace-error">
                        <span class="trace-label">Error:</span> ${escapeHtml(item.error)}
                    </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Format output for display (handle large objects)
 */
function formatOutput(output) {
    if (output === null || output === undefined) {
        return 'null';
    }
    
    const str = JSON.stringify(output, null, 2);
    
    // Truncate very long outputs
    if (str.length > 1000) {
        return str.substring(0, 1000) + '\n... (truncated)';
    }
    
    return str;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Handle Enter key press in message input
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Initialize the application
 */
function init() {
    console.log('FrankenAgent Lab UI initialized');
    loadBlueprints();
}

// Load blueprints when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
