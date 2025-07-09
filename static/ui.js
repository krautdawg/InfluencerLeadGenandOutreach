// UI.js - Client-side interactions for Instagram LeadGen

let sortDirection = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkSessionId();
});

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred', 'error');
    event.preventDefault();
});

function initializeEventListeners() {
    // Session modal
    document.getElementById('saveSession')?.addEventListener('click', saveSessionId);
    
    // Main run button
    document.getElementById('runButton')?.addEventListener('click', processKeyword);
    
    // Enter key on keyword input
    document.getElementById('keywordInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            processKeyword();
        }
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
    
    if (!keyword) {
        showToast('Please enter a keyword', 'error');
        return;
    }
    
    // Show processing status
    const statusDiv = document.getElementById('processingStatus');
    const statusText = document.getElementById('statusText');
    const runButton = document.getElementById('runButton');
    
    statusDiv.style.display = 'block';
    statusText.textContent = 'Processing keyword and gathering leads...';
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            displayResults(result.leads);
            showToast(`Successfully processed ${result.leads.length} leads`, 'success');
        } else {
            showToast(result.error || 'Processing failed', 'error');
        }
    } catch (error) {
        console.error('Error processing keyword:', error);
        showToast('Failed to process keyword', 'error');
    } finally {
        // Hide processing status
        statusDiv.style.display = 'none';
        runButton.disabled = false;
        runButton.innerHTML = '<i class="fas fa-play me-2"></i>Run';
    }
}

function displayResults(leads) {
    if (!leads || leads.length === 0) {
        return;
    }
    
    const resultsSection = document.getElementById('resultsSection');
    const exportSection = document.getElementById('exportSection');
    const tbody = document.getElementById('resultsBody');
    
    // Clear existing results
    tbody.innerHTML = '';
    
    // Add new results
    leads.forEach((lead, index) => {
        const row = createLeadRow(lead, index);
        tbody.appendChild(row);
    });
    
    // Show results section and export options
    resultsSection.style.display = 'block';
    exportSection.style.display = 'block';
}

function createLeadRow(lead, index) {
    const row = document.createElement('tr');
    
    // Add duplicate highlighting
    if (lead.is_duplicate) {
        row.classList.add('duplicate-row');
    }
    
    row.innerHTML = `
        <td>
            <strong>@${lead.username}</strong>
            ${lead.is_duplicate ? '<br><small class="text-warning">Duplicate</small>' : ''}
        </td>
        <td>${lead.fullName || '-'}</td>
        <td>${lead.email || '-'}</td>
        <td>${formatNumber(lead.followersCount)}</td>
        <td>
            <textarea class="table-input table-textarea" id="subject_${index}" placeholder="Email subject...">${lead.subject || ''}</textarea>
        </td>
        <td>
            <textarea class="table-input table-textarea" id="body_${index}" placeholder="Email body..." rows="4">${lead.emailBody || ''}</textarea>
        </td>
        <td>
            <div class="btn-group-vertical btn-group-sm">
                ${lead.sent ? 
                    `<span class="status-sent">Sent<br><small>${formatDate(lead.sentAt)}</small></span>` :
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
    
    if (!confirm(`Send email to @${username}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/send/${username}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subject: subject,
                body: body
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Update the row to show sent status
            const row = document.getElementById(`subject_${index}`).closest('tr');
            const actionsCell = row.lastElementChild;
            actionsCell.innerHTML = `<span class="status-sent">Sent<br><small>${formatDate(new Date().toISOString())}</small></span>`;
            
            showToast('Email sent successfully', 'success');
        } else {
            showToast(result.error || 'Failed to send email', 'error');
        }
    } catch (error) {
        console.error('Error sending email:', error);
        showToast('Failed to send email', 'error');
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
        if (columnIndex === 3) { // Followers count
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
