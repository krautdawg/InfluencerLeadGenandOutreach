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
        showToast('Bitte gib eine gültige Session ID ein', 'error');
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
            showToast('Session ID erfolgreich gespeichert', 'success');
        } else {
            showToast(result.error || 'Fehler beim Speichern der Session ID', 'error');
        }
    } catch (error) {
        console.error('Error saving session:', error);
        showToast('Fehler beim Speichern der Session ID', 'error');
    }
}

async function processKeyword() {
    const keyword = document.getElementById('keywordInput').value.trim();
    const searchLimit = parseInt(document.getElementById('searchLimitInput').value) || 25;
    
    if (!keyword) {
        showToast('Bitte gib einen Suchbegriff ein', 'error');
        return;
    }
    
    if (searchLimit < 1 || searchLimit > 50) {
        showToast('Suchlimit muss zwischen 1 und 50 liegen (Speichersicherheit)', 'error');
        return;
    }
    
    // Show processing status
    const statusDiv = document.getElementById('processingStatus');
    const statusText = document.getElementById('statusText');
    const runButton = document.getElementById('runButton');
    
    statusDiv.style.display = 'block';
    statusText.textContent = `Verarbeite Suchbegriff, sammle bis zu ${searchLimit} Leads...`;
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Verarbeitung...';
    
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
                        <small>Fortschritt: ${progress.completed_steps}/${progress.total_steps} (${percentage}%)</small><br>
                        <small>Geschätzte Restzeit: ${minutes}m ${seconds}s</small>
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
        const timeoutId = setTimeout(() => controller.abort(), 7320000); // 2h 2min (slightly longer than backend's 2h)
        
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ keyword: keyword, searchLimit: searchLimit }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        clearInterval(progressInterval); // Stop progress polling
        
        const result = await response.json();
        
        if (response.ok) {
            displayResults(result.leads);
            showToast(`${result.leads.length} Leads erfolgreich verarbeitet`, 'success');
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
            showToast('Anfrage ist abgelaufen. Bitte versuche es mit einem kleineren Suchlimit erneut.', 'error');
        } else if (error.message && error.message.includes('fetch')) {
            showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung und versuche es erneut.', 'error');
        } else {
            showToast(`Verarbeitungsfehler: ${error.message || 'Unbekannter Fehler'}`, 'error');
        }
    } finally {
        // Hide processing status
        statusDiv.style.display = 'none';
        runButton.disabled = false;
        runButton.innerHTML = '<i class="fas fa-play me-2"></i>Ausführen';
        
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
            ${lead.is_duplicate ? '<br><small class="text-warning">Duplikat</small>' : ''}
        </td>
        <td>${lead.hashtag || '-'}</td>
        <td>${lead.full_name || lead.fullName || '-'}</td>
        <td>${lead.email || '-'}</td>
        <td>${formatNumber(lead.followers_count || lead.followersCount || 0)}</td>
        <td>
            <textarea class="table-input table-textarea" id="subject_${index}" placeholder="Email-Betreff...">${lead.subject || ''}</textarea>
        </td>
        <td>
            <textarea class="table-input table-textarea" id="body_${index}" placeholder="Email-Inhalt..." rows="4">${lead.email_body || lead.emailBody || ''}</textarea>
        </td>
        <td>
            <div class="btn-group-vertical btn-group-sm">
                ${lead.sent ? 
                    `<span class="status-sent">Gesendet<br><small>${formatDate(lead.sent_at || lead.sentAt)}</small></span>` :
                    `<button class="btn btn-secondary btn-sm mb-1" onclick="draftEmail('${lead.username}', ${index})">
                        <i class="fas fa-edit me-1"></i>Entwurf
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="sendEmail('${lead.username}', ${index})">
                        <i class="fas fa-paper-plane me-1"></i>Senden
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
    
    // Get the draft button and store original content
    const draftButton = document.querySelector(`button[onclick="draftEmail('${username}', ${index})"]`);
    const originalContent = draftButton.innerHTML;
    
    // Show spinner and disable button
    draftButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Entwurf wird erstellt...';
    draftButton.disabled = true;
    
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
            showToast('Email-Entwurf erfolgreich erstellt', 'success');
        } else {
            showToast(result.error || 'Fehler beim Erstellen des Email-Entwurfs', 'error');
        }
    } catch (error) {
        console.error('Error drafting email:', error);
        showToast('Fehler beim Erstellen des Email-Entwurfs', 'error');
    } finally {
        // Restore original button content and enable it
        draftButton.innerHTML = originalContent;
        draftButton.disabled = false;
    }
}

async function sendEmail(username, index) {
    const subject = document.getElementById(`subject_${index}`).value.trim();
    const body = document.getElementById(`body_${index}`).value.trim();
    
    if (!subject || !body) {
        showToast('Bitte fülle sowohl Betreff als auch Inhalt aus bevor du sendest', 'error');
        return;
    }
    
    try {
        // Get the lead's email address from the database
        const response = await fetch(`/get-email/${username}`);
        const result = await response.json();
        
        if (!response.ok || !result.email) {
            showToast(result.error || 'Keine E-Mail-Adresse für diesen Lead gefunden', 'error');
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
            actionsCell.innerHTML = `<span class="status-sent">Gesendet<br><small>${formatDate(new Date().toISOString())}</small></span>`;
            
            showToast('Gmail erfolgreich geöffnet - bitte sende die E-Mail', 'success');
        } else {
            showToast('Gmail geöffnet, aber Sendestatus konnte nicht aktualisiert werden', 'warning');
        }
        
    } catch (error) {
        console.error('Error opening Gmail:', error);
        showToast('Fehler beim Öffnen von Gmail', 'error');
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
        
        if (response.ok) {
            if (format === 'csv') {
                // For CSV, handle as direct file download
                const blob = await response.blob();
                
                // Extract filename from Content-Disposition header
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `instagram_leads_${new Date().toISOString().slice(0,19).replace(/:/g, '')}.csv`;
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                
                // Clean up
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);
                
                showToast(`Google Sheets kompatible CSV Datei exportiert`, 'success');
            } else {
                // For JSON, handle as before
                const result = await response.json();
                const blob = new Blob([result.data], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = result.filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showToast(`${format.toUpperCase()} Datei exportiert`, 'success');
            }
        } else {
            const errorText = await response.text();
            showToast('Export fehlgeschlagen', 'error');
        }
    } catch (error) {
        console.error('Error exporting data:', error);
        showToast('Export fehlgeschlagen', 'error');
    }
}

async function clearData() {
    if (!confirm('Bist du sicher, dass du alle Daten löschen möchtest?')) {
        return;
    }
    
    try {
        const response = await fetch('/clear');
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('resultsSection').style.display = 'none';
            document.getElementById('exportSection').style.display = 'none';
            document.getElementById('resultsBody').innerHTML = '';
            showToast('Daten erfolgreich gelöscht', 'success');
        }
    } catch (error) {
        console.error('Error clearing data:', error);
        showToast('Fehler beim Löschen der Daten', 'error');
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
