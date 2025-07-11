// K+L Influence App JavaScript

// Global variables
let currentSortColumn = -1;
let currentSortDirection = 'asc';
let leads = [];
let selectedCell = null;
let editingUsername = null;
let editingField = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkSessionId();
    initializeTableFilters();
    
    // Update session display if we have a session ID
    if (window.igSessionId) {
        updateSessionIdDisplay(window.igSessionId);
    }
    
    // Check if we have leads data from the server
    const existingLeads = window.leadsData || [];
    console.log('Existing leads found:', existingLeads.length);
    if (existingLeads.length > 0) {
        displayResults(existingLeads);
    }
});

// Initialize all event listeners
function initializeEventListeners() {
    // Mobile menu toggle
    document.getElementById('mobileMenuToggle')?.addEventListener('click', () => {
        document.getElementById('sidebarNav').classList.toggle('open');
    });
    
    // Session management
    document.getElementById('changeSessionBtn')?.addEventListener('click', openSessionModal);
    document.getElementById('sessionStatus')?.addEventListener('click', openSessionModal);
    document.getElementById('saveSession')?.addEventListener('click', saveSessionId);
    
    // Settings toggle
    document.getElementById('toggleSettings')?.addEventListener('click', () => {
        const panel = document.getElementById('settingsPanel');
        const icon = document.querySelector('#toggleSettings i:last-child');
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        } else {
            panel.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    });
    
    // Run button
    document.getElementById('runButton')?.addEventListener('click', processKeyword);
    
    // Modal close on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Keyboard navigation for table
    document.addEventListener('keydown', handleTableKeyNavigation);
}

// Initialize table filters
function initializeTableFilters() {
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('input', debounce(applyFilters, 300));
    });
}

// Apply filters to table
function applyFilters() {
    const filters = {
        username: document.getElementById('filterUsername')?.value.toLowerCase() || '',
        hashtag: document.getElementById('filterHashtag')?.value.toLowerCase() || '',
        fullName: document.getElementById('filterFullName')?.value.toLowerCase() || '',
        followers: document.getElementById('filterFollowers')?.value || '',
        email: document.getElementById('filterEmail')?.value.toLowerCase() || '',
        subject: document.getElementById('filterSubject')?.value.toLowerCase() || '',
        emailBody: document.getElementById('filterEmailBody')?.value.toLowerCase() || ''
    };
    
    const tbody = document.getElementById('resultsBody');
    const rows = tbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length === 0) return;
        
        const username = cells[1]?.textContent.toLowerCase() || '';
        const hashtag = cells[2]?.textContent.toLowerCase() || '';
        const fullName = cells[3]?.textContent.toLowerCase() || '';
        const followers = parseInt(cells[4]?.textContent.replace(/[^\d]/g, '')) || 0;
        const email = cells[5]?.textContent.toLowerCase() || '';
        const subject = cells[6]?.textContent.toLowerCase() || '';
        const emailBody = cells[7]?.textContent.toLowerCase() || '';
        
        let show = true;
        
        // Text filters
        if (filters.username && !username.includes(filters.username)) show = false;
        if (filters.hashtag && !hashtag.includes(filters.hashtag)) show = false;
        if (filters.fullName && !fullName.includes(filters.fullName)) show = false;
        if (filters.email && !email.includes(filters.email)) show = false;
        if (filters.subject && !subject.includes(filters.subject)) show = false;
        if (filters.emailBody && !emailBody.includes(filters.emailBody)) show = false;
        
        // Numeric filter for followers
        if (filters.followers) {
            const match = filters.followers.match(/([<>=]+)?\s*(\d+)/);
            if (match) {
                const operator = match[1] || '=';
                const value = parseInt(match[2]);
                
                switch(operator) {
                    case '>':
                        if (followers <= value) show = false;
                        break;
                    case '<':
                        if (followers >= value) show = false;
                        break;
                    case '>=':
                        if (followers < value) show = false;
                        break;
                    case '<=':
                        if (followers > value) show = false;
                        break;
                    default:
                        if (followers !== value) show = false;
                }
            }
        }
        
        row.style.display = show ? '' : 'none';
    });
}

// Clear all filters
function clearFilters() {
    document.querySelectorAll('.filter-input').forEach(input => {
        input.value = '';
    });
    applyFilters();
}

// Check session ID
function checkSessionId() {
    const sessionDisplay = document.getElementById('sessionStatusText');
    if (sessionDisplay && sessionDisplay.textContent === 'Not Connected' && !window.igSessionId) {
        setTimeout(openSessionModal, 500);
    }
}

// Open session modal
function openSessionModal() {
    const modal = document.getElementById('sessionModal');
    modal.classList.add('show');
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

// Save session ID
async function saveSessionId() {
    const sessionId = document.getElementById('sessionInput').value.trim();
    if (!sessionId) {
        showToast('Please enter a valid Session ID', 'error');
        return;
    }
    
    try {
        const response = await fetch('/set-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ig_sessionid: sessionId })
        });
        
        if (response.ok) {
            const result = await response.json();
            updateSessionIdDisplay(sessionId);
            closeModal('sessionModal');
            showToast('Session ID saved successfully', 'success');
        } else {
            showToast('Failed to save Session ID', 'error');
        }
    } catch (error) {
        console.error('Error saving session:', error);
        showToast('An error occurred while saving Session ID', 'error');
    }
}

// Update session ID display
function updateSessionIdDisplay(sessionId) {
    const displays = [
        document.querySelector('.sidebar-section span[style*="font-mono"]'),
        document.getElementById('sessionStatusText')
    ];
    
    displays.forEach(display => {
        if (display) {
            if (display.id === 'sessionStatusText') {
                display.textContent = 'Connected';
            } else {
                display.textContent = sessionId.substring(0, 8) + '...';
            }
        }
    });
}

// Process keyword
async function processKeyword() {
    const keyword = document.getElementById('keywordInput').value.trim();
    const searchLimit = parseInt(document.getElementById('searchLimitInput').value) || 25;
    const enrichLimit = parseInt(document.getElementById('enrichLimitInput').value) || 5;
    
    if (!keyword) {
        showToast('Please enter a hashtag keyword', 'warning');
        return;
    }
    
    // Show processing status
    document.getElementById('processingStatus').style.display = 'block';
    document.getElementById('statusText').textContent = 'Initializing...';
    document.getElementById('runButton').disabled = true;
    
    // Start progress polling
    const progressInterval = setInterval(updateProgress, 2000);
    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                keyword: keyword,
                search_limit: searchLimit,
                enrich_limit: enrichLimit
            }),
            timeout: 300000 // 5 minute timeout
        });
        
        clearInterval(progressInterval);
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.leads) {
                displayResults(result.leads);
                showToast(`Successfully generated ${result.leads.length} leads`, 'success');
            } else {
                showToast(result.message || 'No leads found', 'warning');
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to process keyword', 'error');
        }
    } catch (error) {
        clearInterval(progressInterval);
        console.error('Processing error:', error);
        showToast('An error occurred during processing', 'error');
    } finally {
        document.getElementById('processingStatus').style.display = 'none';
        document.getElementById('runButton').disabled = false;
    }
}

// Update progress
async function updateProgress() {
    try {
        const response = await fetch('/progress');
        if (response.ok) {
            const progress = await response.json();
            document.getElementById('statusText').textContent = progress.message || 'Processing...';
            if (progress.details) {
                document.getElementById('progressText').textContent = progress.details;
            }
        }
    } catch (error) {
        console.error('Progress update error:', error);
    }
}

// Display results in table
function displayResults(leadsData) {
    leads = leadsData;
    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';
    
    leads.forEach((lead, index) => {
        const row = createLeadRow(lead, index);
        tbody.appendChild(row);
    });
    
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('emptyState').style.display = 'none';
    
    // Apply any existing filters
    applyFilters();
}

// Create lead row
function createLeadRow(lead, index) {
    const row = document.createElement('tr');
    if (lead.is_duplicate) {
        row.style.backgroundColor = 'rgba(255, 165, 0, 0.1)';
    }
    
    // Mobile data attributes
    row.innerHTML = `
        <td data-label="#">${index + 1}</td>
        <td data-label="Username">
            <a href="https://instagram.com/${lead.username}" target="_blank" style="color: var(--color-natural-green);">
                @${lead.username}
            </a>
        </td>
        <td data-label="Hashtag">${lead.hashtag || ''}</td>
        <td data-label="Full Name">${lead.full_name || ''}</td>
        <td data-label="Followers">${formatNumber(lead.followers_count || lead.follower_count || 0)}</td>
        <td data-label="Email" class="editable-cell" onclick="startInlineEdit(this, '${lead.username}', 'email')">
            ${lead.email || '<span style="color: var(--color-light-gray);">Click to add</span>'}
        </td>
        <td data-label="Subject" class="editable-cell" onclick="showEditModal('Edit Subject', 'Subject', '${(lead.subject || '').replace(/'/g, '\\\'').replace(/"/g, '&quot;')}', 'subject'); editingUsername = '${lead.username}';">
            ${lead.subject || '<span style="color: var(--color-light-gray);">Click to add</span>'}
        </td>
        <td data-label="Email Body" class="editable-cell" onclick="showEditModal('Edit Email Body', 'Email Body', '${(lead.email_body || '').replace(/'/g, '\\\'').replace(/"/g, '&quot;')}', 'email_body'); editingUsername = '${lead.username}';">
            ${(lead.email_body || '').substring(0, 50)}${(lead.email_body || '').length > 50 ? '...' : ''}${!lead.email_body ? '<span style="color: var(--color-light-gray);">Click to add</span>' : ''}
        </td>
        <td data-label="Actions">
            <div class="d-flex gap-1">
                <button class="btn btn-secondary btn-sm" onclick="generateEmailContent('${lead.username}')" title="Generate Email">
                    <i class="fas fa-envelope"></i> Email
                </button>
                <button class="btn btn-tertiary btn-sm" onclick="sendEmail('${lead.username}')" title="Send Email" ${lead.sent ? 'disabled' : ''}>
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

// Start inline editing
function startInlineEdit(cell, username, field) {
    if (cell.classList.contains('editing')) return;
    
    const currentValue = cell.textContent.replace('Click to add', '').trim();
    cell.classList.add('editing');
    
    const input = document.createElement('input');
    input.type = field === 'email' ? 'email' : 'text';
    input.className = 'cell-editor';
    input.value = currentValue;
    
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
    input.select();
    
    input.addEventListener('blur', () => finishInlineEdit(cell, username, field, input.value));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            input.value = currentValue;
            input.blur();
        }
    });
}

// Finish inline editing
async function finishInlineEdit(cell, username, field, value) {
    cell.classList.remove('editing');
    
    if (value.trim() === '') {
        cell.innerHTML = '<span style="color: var(--color-light-gray);">Click to add</span>';
        return;
    }
    
    cell.textContent = value;
    
    // Update the lead data
    const lead = leads.find(l => l.username === username);
    if (lead) {
        lead[field] = value;
        
        // Save to backend
        try {
            await fetch(`/update-lead/${username}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: value })
            });
        } catch (error) {
            console.error('Failed to update lead:', error);
        }
    }
}

// Generate email content using OpenAI
async function generateEmailContent(username) {
    const lead = leads.find(l => l.username === username);
    if (!lead) return;
    
    // Show loading state
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    button.disabled = true;
    
    try {
        const response = await fetch(`/draft-email/${username}`);
        if (response.ok) {
            const result = await response.json();
            
            // Update the lead data
            lead.subject = result.subject;
            lead.email_body = result.body;
            
            // Update the table display
            displayResults(leads);
            
            showToast('Email content generated successfully!', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to generate email content', 'error');
        }
    } catch (error) {
        console.error('Email generation error:', error);
        showToast('An error occurred while generating email content', 'error');
    } finally {
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Show edit modal
function showEditModal(title, label, content, field) {
    editingField = field;
    document.getElementById('editModalTitle').textContent = title;
    document.getElementById('editModalLabel').textContent = label;
    document.getElementById('editModalContent').value = content || '';
    document.getElementById('editModal').classList.add('show');
    
    // Focus on textarea
    setTimeout(() => {
        document.getElementById('editModalContent').focus();
    }, 100);
}

// Close edit modal
function closeEditModal() {
    document.getElementById('editModal').classList.remove('show');
    editingUsername = null;
    editingField = null;
}

// Save edit modal
async function saveEditModal() {
    const content = document.getElementById('editModalContent').value;
    const lead = leads.find(l => l.username === editingUsername);
    
    if (!lead) return;
    
    lead[editingField] = content;
    
    // If we just edited subject, show body next
    if (editingField === 'subject') {
        closeEditModal();
        setTimeout(() => {
            showEditModal('Edit Email Draft', 'Email Body', lead.email_body, 'email_body');
        }, 300);
    } else {
        // Save to backend
        try {
            await fetch(`/update-lead/${editingUsername}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    subject: lead.subject,
                    email_body: lead.email_body
                })
            });
            showToast('Email draft saved successfully', 'success');
        } catch (error) {
            console.error('Failed to save draft:', error);
            showToast('Failed to save email draft', 'error');
        }
        closeEditModal();
    }
}

// Send email
async function sendEmail(username) {
    const lead = leads.find(l => l.username === username);
    if (!lead) return;
    
    if (!lead.email) {
        showToast('Please add an email address first', 'warning');
        return;
    }
    
    if (!lead.subject || !lead.email_body) {
        showToast('Please create an email draft first', 'warning');
        return;
    }
    
    if (confirm(`Send email to ${lead.email}?`)) {
        try {
            const response = await fetch(`/send-email/${username}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                showToast('Email sent successfully! 🌱', 'success');
                // Update UI to show sent status
                const row = document.querySelector(`tr:has(a[href*="${username}"])`);
                if (row) {
                    const sendButton = row.querySelector('.fa-paper-plane').parentElement;
                    sendButton.disabled = true;
                }
            } else {
                const error = await response.json();
                showToast(error.error || 'Failed to send email', 'error');
            }
        } catch (error) {
            console.error('Send email error:', error);
            showToast('An error occurred while sending email', 'error');
        }
    }
}

// Table sorting
function sortTable(columnIndex) {
    const tbody = document.getElementById('resultsBody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine sort direction
    if (currentSortColumn === columnIndex) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortDirection = 'asc';
        currentSortColumn = columnIndex;
    }
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent;
        const bValue = b.cells[columnIndex].textContent;
        
        // Handle numeric columns
        if (columnIndex === 0 || columnIndex === 4) {
            const aNum = parseNumber(aValue);
            const bNum = parseNumber(bValue);
            return currentSortDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Text columns
        return currentSortDirection === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    updateSortIndicators(columnIndex, currentSortDirection);
    
    // Re-apply filters
    applyFilters();
}

// Update sort indicators
function updateSortIndicators(activeColumn, direction) {
    document.querySelectorAll('.sort-indicator').forEach((indicator, index) => {
        if (index === activeColumn) {
            indicator.textContent = direction === 'asc' ? '↑' : '↓';
            indicator.style.color = 'var(--color-natural-green)';
        } else {
            indicator.textContent = '↕';
            indicator.style.color = 'var(--color-medium-gray)';
        }
    });
}

// Handle table keyboard navigation
function handleTableKeyNavigation(e) {
    if (!selectedCell || !document.querySelector('.data-table')) return;
    
    const table = document.querySelector('.data-table');
    const rows = table.querySelectorAll('tbody tr');
    const currentRow = selectedCell.parentElement;
    const currentRowIndex = Array.from(rows).indexOf(currentRow);
    const currentCellIndex = Array.from(currentRow.cells).indexOf(selectedCell);
    
    let newRow, newCell;
    
    switch(e.key) {
        case 'ArrowUp':
            if (currentRowIndex > 0) {
                newRow = rows[currentRowIndex - 1];
                newCell = newRow.cells[currentCellIndex];
            }
            break;
        case 'ArrowDown':
            if (currentRowIndex < rows.length - 1) {
                newRow = rows[currentRowIndex + 1];
                newCell = newRow.cells[currentCellIndex];
            }
            break;
        case 'ArrowLeft':
            if (currentCellIndex > 0) {
                newCell = currentRow.cells[currentCellIndex - 1];
            }
            break;
        case 'ArrowRight':
            if (currentCellIndex < currentRow.cells.length - 1) {
                newCell = currentRow.cells[currentCellIndex + 1];
            }
            break;
        case 'Enter':
            if (selectedCell.classList.contains('editable-cell')) {
                e.preventDefault();
                selectedCell.click();
            }
            break;
    }
    
    if (newCell) {
        e.preventDefault();
        selectCell(newCell);
    }
}

// Select table cell
function selectCell(cell) {
    if (selectedCell) {
        selectedCell.style.outline = '';
    }
    selectedCell = cell;
    selectedCell.style.outline = '2px solid var(--color-natural-green)';
    selectedCell.scrollIntoView({ block: 'nearest', inline: 'nearest' });
}

// Export data
async function exportData(format) {
    try {
        const response = await fetch(`/export/${format}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `leads_export.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast(`Data exported as ${format.toUpperCase()}`, 'success');
        } else {
            showToast('Failed to export data', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showToast('An error occurred during export', 'error');
    }
}

// Clear all data
async function clearData() {
    if (!confirm('Are you sure you want to clear all data? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/clear-data', { method: 'POST' });
        if (response.ok) {
            leads = [];
            document.getElementById('resultsBody').innerHTML = '';
            document.getElementById('resultsSection').style.display = 'none';
            document.getElementById('emptyState').style.display = 'block';
            showToast('All data has been cleared', 'success');
        } else {
            showToast('Failed to clear data', 'error');
        }
    } catch (error) {
        console.error('Clear data error:', error);
        showToast('An error occurred while clearing data', 'error');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} show`;
    toast.innerHTML = `
        <div class="d-flex align-items-center justify-content-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; font-size: 20px; cursor: pointer;">×</button>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function parseNumber(str) {
    const num = str.replace(/[^\d.]/g, '');
    if (str.includes('M')) {
        return parseFloat(num) * 1000000;
    } else if (str.includes('K')) {
        return parseFloat(num) * 1000;
    }
    return parseFloat(num) || 0;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}