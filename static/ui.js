// UI.js - Client-side interactions for Instagram LeadGen

let sortDirection = {};
let filterValues = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkSessionId();
    initializeTableFilters();
});

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Only show toast for non-user-rejected errors (avoid showing for browser extension rejections)
    if (event.reason && event.reason.code !== 4001 && !event.reason.message?.includes('User rejected')) {
        showToast('An unexpected error occurred', 'error');
    }
    event.preventDefault();
});

function initializeEventListeners() {
    // Session modal
    document.getElementById('saveSession')?.addEventListener('click', saveSessionId);
    
    // Change session button
    document.getElementById('changeSessionBtn')?.addEventListener('click', openSessionModal);
    
    // Main run button
    document.getElementById('runButton')?.addEventListener('click', processKeyword);
    
    // Enter key on keyword input
    document.getElementById('keywordInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            processKeyword();
        }
    });
}

function initializeTableFilters() {
    // Set up filter event listeners
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('input', function() {
            const column = parseInt(this.getAttribute('data-column'));
            filterValues[column] = this.value.toLowerCase();
            applyFilters();
        });
    });
}

function applyFilters() {
    const tbody = document.querySelector('#resultsTable tbody');
    const rows = tbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        let shouldShow = true;
        
        // Check each filter
        for (const [column, filterValue] of Object.entries(filterValues)) {
            if (filterValue && filterValue.trim() !== '') {
                const cellText = row.cells[column]?.textContent.toLowerCase() || '';
                
                // Special handling for numeric columns (followers)
                if (column == 4) { // Followers column
                    const numericValue = parseNumber(cellText);
                    const filterNum = parseNumber(filterValue);
                    
                    // Support comparison operators: >, <, >=, <=, =
                    if (filterValue.startsWith('>=')) {
                        shouldShow = numericValue >= parseNumber(filterValue.substring(2));
                    } else if (filterValue.startsWith('<=')) {
                        shouldShow = numericValue <= parseNumber(filterValue.substring(2));
                    } else if (filterValue.startsWith('>')) {
                        shouldShow = numericValue > parseNumber(filterValue.substring(1));
                    } else if (filterValue.startsWith('<')) {
                        shouldShow = numericValue < parseNumber(filterValue.substring(1));
                    } else if (filterValue.startsWith('=')) {
                        shouldShow = numericValue === parseNumber(filterValue.substring(1));
                    } else if (!isNaN(filterNum)) {
                        // If just a number, do exact match
                        shouldShow = numericValue === filterNum;
                    } else {
                        // Fallback to text search
                        shouldShow = cellText.includes(filterValue);
                    }
                } else {
                    // Text columns - case insensitive partial match
                    if (!cellText.includes(filterValue)) {
                        shouldShow = false;
                    }
                }
                
                if (!shouldShow) break;
            }
        }
        
        // Show/hide row based on filter match
        row.style.display = shouldShow ? '' : 'none';
    });
}

function clearFilters() {
    // Clear filter values
    filterValues = {};
    
    // Clear all filter inputs
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.value = '';
    });
    
    // Show all rows
    const tbody = document.querySelector('#resultsTable tbody');
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        row.style.display = '';
    });
}

function checkSessionId() {
    // This is handled by the template, but we can add additional client-side checks here
    const modal = document.getElementById('sessionModal');
    if (modal && modal.style.display === 'block') {
        // Focus on the input field
        document.getElementById('sessionInput')?.focus();
    }
}

function openSessionModal() {
    // Clear the input field and show the modal
    document.getElementById('sessionInput').value = '';
    document.getElementById('sessionModal').style.display = 'block';
    // Focus on the input field
    document.getElementById('sessionInput')?.focus();
}

function updateSessionIdDisplay(sessionId) {
    // Update the session ID display in the navigation
    const displayElement = document.getElementById('sessionIdDisplay');
    if (displayElement) {
        if (sessionId && sessionId.length > 0) {
            displayElement.textContent = sessionId.substring(0, 8) + '...';
        } else {
            displayElement.textContent = 'Not Set';
        }
    }
}

async function saveSessionId() {
    const sessionId = document.getElementById('sessionInput').value.trim();
    
    if (!sessionId) {
        showToast('Please enter a valid Session ID', 'error');
        return;
    }
    
    try {
        const response = await fetch('/session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ig_sessionid: sessionId })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('sessionModal').style.display = 'none';
            updateSessionIdDisplay(sessionId);
            showToast('Session ID saved successfully', 'success');
        } else {
            showToast(result.error || 'Failed to save Session ID', 'error');
        }
    } catch (error) {
        console.error('Error saving session:', error);
        showToast('Failed to save Session ID', 'error');
    }
}

async function processKeyword() {
    const keyword = document.getElementById('keywordInput').value.trim();
    const searchLimit = parseInt(document.getElementById('searchLimitInput').value) || 25;
    const enrichLimit = parseInt(document.getElementById('enrichLimitInput').value) || 5;
    
    if (!keyword) {
        showToast('Please enter a keyword', 'error');
        return;
    }
    
    if (searchLimit < 1 || searchLimit > 50) {
        showToast('Search limit must be between 1 and 50 (memory safety)', 'error');
        return;
    }
    
    if (enrichLimit < 1 || enrichLimit > 25) {
        showToast('Enrich limit must be between 1 and 25 (for testing)', 'error');
        return;
    }
    
    // Show processing status
    const statusDiv = document.getElementById('processingStatus');
    const statusText = document.getElementById('statusText');
    const runButton = document.getElementById('runButton');
    
    statusDiv.style.display = 'block';
    statusText.textContent = `Processing keyword, gathering up to ${searchLimit} leads, enriching ${enrichLimit} profiles...`;
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    // Start progress polling
    let progressInterval = null;
    const updateProgress = async () => {
        try {
            const progressResponse = await fetch('/progress');
            if (progressResponse.ok) {
                const progress = await progressResponse.json();
                if (progress.total_steps > 0) {
                    const percentage = Math.round((progress.completed_steps / progress.total_steps) * 100);
                    const minutes = Math.floor(progress.estimated_time_remaining / 60);
                    const seconds = progress.estimated_time_remaining % 60;
                    statusText.innerHTML = `
                        ${progress.current_step}<br>
                        <small>Progress: ${progress.completed_steps}/${progress.total_steps} (${percentage}%)</small><br>
                        <small>Est. time remaining: ${minutes}m ${seconds}s</small>
                    `;
                }
            }
        } catch (error) {
            console.log('Progress update error:', error);
        }
    };
    
    // Poll progress every 2 seconds
    progressInterval = setInterval(updateProgress, 2000);
    updateProgress(); // Initial update
    
    try {
        // Add timeout to match backend timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 190000); // 3.17 minutes (slightly longer than backend's 180s)
        
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword, searchLimit: searchLimit, enrichLimit: enrichLimit }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        clearInterval(progressInterval); // Stop progress polling
        
        const result = await response.json();
        
        if (response.ok) {
            displayResults(result.leads);
            showToast(`Successfully processed ${result.leads.length} leads`, 'success');
        } else {
            const errorMessage = result.error || 'Processing failed';
            console.error('Server error response:', result);
            showToast(errorMessage, 'error');
            
            // If it's a session ID error, show the modal
            if (errorMessage.includes('Instagram Session ID')) {
                document.getElementById('sessionModal').style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Error processing keyword:', error);
        if (error.name === 'AbortError') {
            showToast('Request timed out. Please try again with a smaller search limit.', 'error');
        } else if (error.message && error.message.includes('fetch')) {
            showToast('Network error. Please check your connection and try again.', 'error');
        } else {
            showToast(`Processing error: ${error.message || 'Unknown error'}`, 'error');
        }
    } finally {
        // Hide processing status
        statusDiv.style.display = 'none';
        runButton.disabled = false;
        runButton.innerHTML = '<i class="fas fa-play me-2"></i>Run';
        
        // Clear progress interval if it exists
        if (progressInterval) {
            clearInterval(progressInterval);
        }
    }
}

function displayResults(leads) {
    if (!leads || leads.length === 0) {
        return;
    }
    
    // Debug logging to understand the data structure
    console.log('Displaying results:', leads);
    console.log('First lead data structure:', leads[0]);
    
    const resultsSection = document.getElementById('resultsSection');
    const exportSection = document.getElementById('exportSection');
    const tbody = document.getElementById('resultsBody');
    
    // Clear existing results
    tbody.innerHTML = '';
    
    // Clear filter values when new results are loaded
    filterValues = {};
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.value = '';
    });
    
    // Add new results
    leads.forEach((lead, index) => {
        const row = createLeadRow(lead, index);
        tbody.appendChild(row);
    });
    
    // Show results section and export options
    resultsSection.style.display = 'block';
    exportSection.style.display = 'block';
    
    // Re-initialize table filters after new content is loaded
    setTimeout(() => {
        initializeTableFilters();
    }, 100);
}

function createLeadRow(lead, index) {
    const row = document.createElement('tr');
    
    // Add duplicate highlighting
    if (lead.is_duplicate) {
        row.classList.add('duplicate-row');
    }
    
    row.innerHTML = `
        <td>
            <a href="https://www.instagram.com/${lead.username}" target="_blank" rel="noopener noreferrer">
                <strong>@${lead.username}</strong>
            </a>
            ${lead.is_duplicate ? '<br><small class="text-warning">Duplicate</small>' : ''}
        </td>
        <td>${lead.hashtag || '-'}</td>
        <td>${lead.full_name || lead.fullName || '-'}</td>
        <td>${lead.email || '-'}</td>
        <td>${formatNumber(lead.followers_count || lead.followersCount || 0)}</td>
        <td>
            <textarea class="table-input table-textarea" id="subject_${index}" placeholder="Email subject...">${lead.subject || ''}</textarea>
        </td>
        <td>
            <textarea class="table-input table-textarea" id="body_${index}" placeholder="Email body..." rows="4">${lead.email_body || lead.emailBody || ''}</textarea>
        </td>
        <td>
            <div class="btn-group-vertical btn-group-sm">
                ${lead.sent ? 
                    `<span class="status-sent">Sent<br><small>${formatDate(lead.sent_at || lead.sentAt)}</small></span>` :
                    `<button class="btn btn-secondary btn-sm mb-1" onclick="draftEmail('${lead.username}', ${index})">
                        <i class="fas fa-edit me-1"></i>Draft
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="sendEmail('${lead.username}', ${index})">
                        <i class="fas fa-paper-plane me-1"></i>Send
                    </button>`
                }
            </div>
        </td>
    `;
    
    return row;
}

async function draftEmail(username, index) {
    const subjectPrompt = document.getElementById('subjectPrompt').value;
    const bodyPrompt = document.getElementById('bodyPrompt').value;
    
    try {
        const response = await fetch(`/draft/${username}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subject_prompt: subjectPrompt,
                body_prompt: bodyPrompt
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById(`subject_${index}`).value = result.subject;
            document.getElementById(`body_${index}`).value = result.body;
            showToast('Email draft generated successfully', 'success');
        } else {
            showToast(result.error || 'Failed to generate email draft', 'error');
        }
    } catch (error) {
        console.error('Error drafting email:', error);
        showToast('Failed to generate email draft', 'error');
    }
}

async function sendEmail(username, index) {
    const subject = document.getElementById(`subject_${index}`).value.trim();
    const body = document.getElementById(`body_${index}`).value.trim();
    
    if (!subject || !body) {
        showToast('Please fill in both subject and body before sending', 'error');
        return;
    }
    
    try {
        // Get the lead's email address from the database
        const response = await fetch(`/get-email/${username}`);
        const result = await response.json();
        
        if (!response.ok || !result.email) {
            showToast(result.error || 'No email address found for this lead', 'error');
            return;
        }
        
        // Create Gmail compose URL
        const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(result.email)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        
        // Open Gmail compose in new tab
        window.open(gmailUrl, '_blank');
        
        // Mark as sent in database
        const updateResponse = await fetch(`/mark-sent/${username}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subject: subject,
                body: body
            })
        });
        
        if (updateResponse.ok) {
            // Update the row to show sent status
            const row = document.getElementById(`subject_${index}`).closest('tr');
            const actionsCell = row.lastElementChild;
            actionsCell.innerHTML = `<span class="status-sent">Sent<br><small>${formatDate(new Date().toISOString())}</small></span>`;
            
            showToast('Gmail opened successfully - please send the email', 'success');
        } else {
            showToast('Gmail opened, but failed to update send status', 'warning');
        }
        
    } catch (error) {
        console.error('Error opening Gmail:', error);
        showToast('Failed to open Gmail', 'error');
    }
}

function sortTable(columnIndex) {
    const table = document.getElementById('resultsTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.rows);
    
    // Determine sort direction
    const currentDirection = sortDirection[columnIndex] || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    sortDirection[columnIndex] = newDirection;
    
    // Sort rows
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        // Handle numeric values
        if (columnIndex === 4) { // Followers count (updated index)
            const aNum = parseNumber(aVal);
            const bNum = parseNumber(bVal);
            return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Handle text values
        const comparison = aVal.localeCompare(bVal);
        return newDirection === 'asc' ? comparison : -comparison;
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    updateSortIndicators(columnIndex, newDirection);
    
    // Re-apply filters after sorting
    applyFilters();
}

function updateSortIndicators(activeColumn, direction) {
    const headers = document.querySelectorAll('#resultsTable th');
    headers.forEach((header, index) => {
        const icon = header.querySelector('i');
        if (icon) {
            if (index === activeColumn) {
                icon.className = direction === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
            } else {
                icon.className = 'fas fa-sort';
            }
        }
    });
}

async function exportData(format) {
    try {
        const response = await fetch(`/export/${format}`);
        const result = await response.json();
        
        if (response.ok) {
            // Create and trigger download
            const blob = new Blob([result.data], { 
                type: format === 'csv' ? 'text/csv' : 'application/json' 
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast(`Data exported as ${format.toUpperCase()}`, 'success');
        } else {
            showToast(result.error || 'Export failed', 'error');
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        showToast('Export failed', 'error');
    }
}

async function clearData() {
    if (!confirm('Are you sure you want to clear all data?')) {
        return;
    }
    
    try {
        const response = await fetch('/clear');
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('resultsSection').style.display = 'none';
            document.getElementById('exportSection').style.display = 'none';
            document.getElementById('resultsBody').innerHTML = '';
            showToast('Data cleared successfully', 'success');
        }
    } catch (error) {
        console.error('Error clearing data:', error);
        showToast('Failed to clear data', 'error');
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toastMessage');
    const toastBody = document.getElementById('toastBody');
    
    toastBody.textContent = message;
    
    // Remove existing type classes
    toast.classList.remove('bg-success', 'bg-danger', 'bg-info');
    
    // Add appropriate type class
    switch (type) {
        case 'success':
            toast.classList.add('bg-success', 'text-white');
            break;
        case 'error':
            toast.classList.add('bg-danger', 'text-white');
            break;
        default:
            toast.classList.add('bg-info', 'text-white');
    }
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Utility functions
function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function parseNumber(str) {
    const cleaned = str.replace(/[^\d.]/g, '');
    const num = parseFloat(cleaned);
    if (str.includes('M')) return num * 1000000;
    if (str.includes('K')) return num * 1000;
    return num || 0;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
}
