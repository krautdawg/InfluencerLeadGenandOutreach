// K+L Influence App JavaScript

// Global variables
let currentSortColumn = -1;
let currentSortDirection = 'asc';
let leads = [];
let selectedCell = null;
let editingUsername = null;
let editingField = null;
let products = [];
let defaultProductId = null;
let lastNotificationTime = 0;

// Template prompts for different scenarios
const TEMPLATE_PROMPTS = {
    withProduct: {
        subject: 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Falls ein Produkt ausgewählt ist, erwähne es subtil in der Betreffzeile. Antworte im JSON-Format: {"subject": "betreff text"}',
        body: 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. WICHTIG: Falls ein Produkt ausgewählt ist, integriere unbedingt folgende Elemente in die E-Mail: 1) Erwähne das Produkt namentlich, 2) Füge den direkten Link zum Produkt ein (Produkt-URL), 3) Erkläre kurz die Produkteigenschaften basierend auf der Beschreibung, 4) Beziehe das Produkt auf die Bio/Interessen des Influencers. Die E-Mail sollte den Produktlink natürlich in den Text einbetten. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {"body": "email inhalt"}'
    },
    withoutProduct: {
        subject: 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Fokussiere dich auf die Interessen und den Content des Influencers. Antworte im JSON-Format: {"subject": "betreff text"}',
        body: 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. Fokussiere dich auf eine allgemeine Kooperationsanfrage, die auf die Interessen und den Content des Influencers eingeht. Erwähne deine Begeisterung für ihren Content und schlage eine mögliche Zusammenarbeit vor, ohne spezifische Produkte zu erwähnen. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte im JSON-Format: {"body": "email inhalt"}'
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkSessionId();
    initializeTableFilters();
    
    // Load products data from the server or fetch from API
    if (window.productsData) {
        products = window.productsData;
        populateProductSelectors();
    } else {
        loadProducts();
    }
    
    // Set default product from session
    if (window.defaultProductId) {
        defaultProductId = window.defaultProductId;
        const defaultProductSelect = document.getElementById('defaultProductSelect');
        if (defaultProductSelect) {
            defaultProductSelect.value = defaultProductId;
        }
    }
    
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
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        const sidebar = document.getElementById('sidebarNav');
        const toggleButton = document.getElementById('mobileMenuToggle');
        
        if (sidebar && sidebar.classList.contains('open') && 
            !sidebar.contains(e.target) && 
            !toggleButton.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
    
    // Session management
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
    
    // Stop button
    document.getElementById('stopButton')?.addEventListener('click', stopProcessing);
    
    // Email template auto-save
    initializeEmailTemplateAutoSave();
    
    // Default product selector change
    document.getElementById('defaultProductSelect')?.addEventListener('change', updateTemplatePromptsBasedOnProduct);
    
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
    
    // Mobile input field optimization
    optimizeMobileInputs();
}

// Initialize table filters
function initializeTableFilters() {
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('input', debounce(applyFilters, 300));
    });
}

// Optimize mobile input fields
function optimizeMobileInputs() {
    // Ensure numeric inputs work properly on mobile
    const numericInputs = document.querySelectorAll('input[type="number"]');
    numericInputs.forEach(input => {
        // Add mobile-specific attributes
        input.setAttribute('inputmode', 'numeric');
        input.setAttribute('pattern', '[0-9]*');
        
        // Add input validation to prevent invalid values
        input.addEventListener('input', function(e) {
            let value = parseInt(e.target.value);
            
            // Handle search limit validation
            if (e.target.id === 'searchLimitInput') {
                if (value < 1) {
                    e.target.value = 1;
                } else if (value > 50) {
                    e.target.value = 50;
                }
            }
        });
        
        // Add blur event to ensure valid values
        input.addEventListener('blur', function(e) {
            if (!e.target.value) {
                if (e.target.id === 'searchLimitInput') {
                    e.target.value = 25;
                }
            }
        });
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
        website: document.getElementById('filterWebsite')?.value.toLowerCase() || '',
        product: document.getElementById('filterProduct')?.value.toLowerCase() || '',
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
        const website = cells[6]?.textContent.toLowerCase() || '';
        const product = cells[7]?.textContent.toLowerCase() || '';
        const subject = cells[8]?.textContent.toLowerCase() || '';
        const emailBody = cells[9]?.textContent.toLowerCase() || '';
        
        let show = true;
        
        // Text filters
        if (filters.username && !username.includes(filters.username)) show = false;
        if (filters.hashtag && !hashtag.includes(filters.hashtag)) show = false;
        if (filters.fullName && !fullName.includes(filters.fullName)) show = false;
        if (filters.email && !email.includes(filters.email)) show = false;
        if (filters.website && !website.includes(filters.website)) show = false;
        if (filters.product && !product.includes(filters.product)) show = false;
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
    const statusText = document.getElementById('sessionStatusText');
    if (statusText) {
        if (sessionId && sessionId.length > 0) {
            statusText.textContent = `Verbunden (${sessionId.substring(0, 8)}...)`;
        } else {
            statusText.textContent = 'Nicht verbunden';
        }
    }
}

// Stop processing
async function stopProcessing() {
    try {
        const response = await fetch('/stop-processing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Stopp-Anfrage gesendet...', 'info');
            
            // Update button states
            const stopButton = document.getElementById('stopButton');
            stopButton.disabled = true;
            stopButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
        } else {
            showToast('Stopp fehlgeschlagen', 'error');
        }
    } catch (error) {
        console.error('Error stopping processing:', error);
        showToast('Error stopping processing', 'error');
    }
}

// Process keyword
async function processKeyword() {
    const keyword = document.getElementById('keywordInput').value.trim();
    const searchLimit = parseInt(document.getElementById('searchLimitInput').value) || 25;
    
    if (!keyword) {
        showToast('Bitte gib einen Suchbegriff ein', 'warning');
        return;
    }
    
    // Validate search limit
    if (searchLimit < 1 || searchLimit > 50) {
        showToast('Suchlimit muss zwischen 1 und 50 liegen (Speichersicherheit)', 'error');
        return;
    }
    
    const runButton = document.getElementById('runButton');
    const stopButton = document.getElementById('stopButton');
    
    // Update UI for processing state
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    runButton.style.display = 'none';
    
    stopButton.disabled = false;
    stopButton.style.display = 'inline-block';
    stopButton.innerHTML = '<i class="fas fa-stop"></i> Stop Processing';
    

    
    // Reset previous lead count for new processing run
    previousLeadCount = 0;
    

    
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                keyword: keyword,
                searchLimit: searchLimit
            }),
            timeout: 7320000 // 2h 2min timeout to match gunicorn (2h timeout)
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.leads) {
                displayResults(result.leads);
                showToast(`Successfully generated ${result.leads.length} leads`, 'success');
            } else {
                showToast(result.message || 'No leads found', 'warning');
            }
        } else if (response.status === 206) {
            // Partial success - some leads generated but process failed
            const result = await response.json();
            if (result.leads && result.leads.length > 0) {
                displayResults(result.leads);
                showToast(`Process partially failed but saved ${result.partial_count} leads. Error: ${result.error}`, 'warning');
            } else {
                showToast(`Process failed: ${result.error}`, 'error');
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to process keyword', 'error');
        }
    } catch (error) {
        console.error('Processing error:', error);
        if (error.name === 'AbortError') {
            showToast('Anfrage ist abgelaufen. Bitte versuche es mit einem kleineren Suchlimit erneut.', 'error');
        } else if (error.message && error.message.includes('fetch')) {
            showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung und versuche es erneut.', 'error');
        } else {
            showToast(`Verarbeitungsfehler: ${error.message || 'Unbekannter Fehler'}`, 'error');
        }
    } finally {
        // Reset button states
        resetProcessingUI();
    }
}

// Track previous lead count to detect new leads
let previousLeadCount = 0;



// Reset processing UI to initial state
function resetProcessingUI() {
    const runButton = document.getElementById('runButton');
    const stopButton = document.getElementById('stopButton');
    
    // Reset run button
    runButton.disabled = false;
    runButton.innerHTML = '<i class="fas fa-play"></i><span>Leads generieren</span>';
    runButton.style.display = 'inline-block';
    
    // Hide stop button
    stopButton.disabled = true;
    stopButton.style.display = 'none';
    

}

// Refresh leads table for a specific keyword (used during incremental updates)
async function refreshLeadsTable(keyword) {
    try {
        // Add loading indicator to table
        const tbody = document.getElementById('resultsBody');
        if (tbody) {
            tbody.style.opacity = '0.7';
        }
        
        const response = await fetch(`/api/leads?keyword=${encodeURIComponent(keyword)}`);
        if (response.ok) {
            const result = await response.json();
            if (result.leads && result.leads.length > 0) {
                console.log(`Refreshing table with ${result.leads.length} leads for keyword: ${keyword}`);
                displayResults(result.leads);
                
                // Flash effect to show update
                if (tbody) {
                    tbody.style.opacity = '1';
                    tbody.style.transition = 'opacity 0.3s ease-in-out';
                    
                    // Add a subtle highlight effect
                    setTimeout(() => {
                        tbody.style.backgroundColor = '#e8f5e9';
                        setTimeout(() => {
                            tbody.style.backgroundColor = '';
                            tbody.style.transition = 'background-color 0.5s ease-in-out';
                        }, 500);
                    }, 100);
                }
            }
        }
    } catch (error) {
        console.error('Error refreshing leads table:', error);
        if (tbody) {
            tbody.style.opacity = '1';
        }
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
        <td data-label="Followers">${formatNumber(lead.followersCount || 0)}</td>
        <td data-label="Email" class="editable-cell" onclick="startInlineEdit(this, '${lead.username}', 'email')">
            ${lead.email || '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>'}
        </td>
        <td data-label="Website" class="editable-cell" onclick="startInlineEdit(this, '${lead.username}', 'website')">
            ${lead.website ? `<a href="${lead.website}" target="_blank" style="color: var(--color-natural-green);">${lead.website}</a>` : '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>'}
        </td>
        <td data-label="Product" class="editable-cell" id="product-cell-${lead.username}" onclick="editProductSelection('${lead.username}')">
            ${getProductNameById(lead.selectedProductId) || '<span style="color: var(--color-light-gray);">Kein Produkt</span>'}
        </td>
        <td data-label="Subject" class="editable-cell" data-username="${lead.username}" data-field="subject" onclick="editField(this)">
            ${lead.subject || '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>'}
        </td>
        <td data-label="Email Body" class="editable-cell" data-username="${lead.username}" data-field="email_body" onclick="editField(this)">
            ${(lead.email_body || '').substring(0, 50)}${(lead.email_body || '').length > 50 ? '...' : ''}${!lead.email_body ? '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>' : ''}
        </td>
        <td data-label="Status">
            ${lead.sent ? `<span style="color: var(--color-natural-green); font-weight: 500;"><i class="fas fa-check-circle"></i> Gesendet<br><small style="color: var(--color-medium-gray); font-weight: normal;">${formatDateTime(lead.sentAt)}</small></span>` : '<span style="color: var(--color-medium-gray);">Entwurf</span>'}
        </td>
        <td data-label="Actions">
            <div class="d-flex gap-1">
                <button class="btn btn-secondary btn-sm" onclick="generateEmailContent('${lead.username}')" title="Email generieren">
                    <i class="fas fa-envelope"></i> Email
                </button>
                <button class="btn btn-tertiary btn-sm send-btn" id="send-btn-${lead.username}" onclick="sendEmail('${lead.username}')" title="Email senden">
                    <i class="fas fa-paper-plane"></i> Senden
                </button>
            </div>
        </td>
    `;
    
    return row;
}

// Edit field handler (for both inline and modal editing)
function editField(cell) {
    const username = cell.getAttribute('data-username');
    const field = cell.getAttribute('data-field');
    const lead = leads.find(l => l.username === username);
    
    if (!lead) return;
    
    if (field === 'email') {
        startInlineEdit(cell, username, field);
    } else if (field === 'subject') {
        showEditModal('Edit Subject', 'Subject', lead.subject || '', 'subject');
        editingUsername = username;
    } else if (field === 'email_body') {
        showEditModal('Edit Email Body', 'Email Body', lead.email_body || '', 'email_body');
        editingUsername = username;
    }
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
        cell.innerHTML = '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>';
        return;
    }
    
    // Format website as clickable link
    if (field === 'website' && value.trim()) {
        cell.innerHTML = `<a href="${value}" target="_blank" style="color: var(--color-natural-green);">${value}</a>`;
    } else {
        cell.textContent = value;
    }
    
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
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generiert...';
    button.disabled = true;
    
    try {
        // First, update the lead's product with the current default selection
        const defaultProductSelect = document.getElementById('defaultProductSelect');
        const selectedProductId = defaultProductSelect ? defaultProductSelect.value : null;
        
        if (defaultProductSelect) {
            // Update product in backend
            await fetch(`/api/leads/${username}/product`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: selectedProductId || null })
            });
            
            // Update local lead data
            if (selectedProductId) {
                lead.selected_product_id = parseInt(selectedProductId);
                const selectedProduct = products.find(p => p.id == selectedProductId);
                if (selectedProduct) {
                    lead.selected_product = selectedProduct;
                }
            } else {
                // Clear product if none selected
                lead.selected_product_id = null;
                lead.selected_product = null;
            }
        }
        
        const response = await fetch(`/draft-email/${username}`);
        if (response.ok) {
            const result = await response.json();
            
            // Update the lead data
            lead.subject = result.subject;
            lead.email_body = result.body;
            
            // Update the selectedProductId field for table display consistency
            if (selectedProductId) {
                lead.selectedProductId = parseInt(selectedProductId);
            } else {
                lead.selectedProductId = null;
            }
            
            // Update the table display to show the product that was used for email generation
            displayResults(leads);
            
            // Update the specific product cell to reflect the product used for this email
            const productCell = document.getElementById(`product-cell-${username}`);
            if (productCell) {
                const productName = selectedProductId ? getProductNameById(selectedProductId) : null;
                productCell.innerHTML = productName || '<span style="color: var(--color-light-gray);">Kein Produkt</span>';
            }
            
            showToast('Email content generated successfully! Product column updated.', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to generate email content', 'error');
        }
    } catch (error) {
        console.error('Email generation error:', error);
        showToast('An error occurred while generating email content', 'error');
    } finally {
        // Restore button state
        if (button) {
            button.innerHTML = originalText;
            button.disabled = false;
        }
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
    
    if (!lead) {
        showToast('Error: Lead not found', 'error');
        return;
    }
    
    // Update the lead data
    lead[editingField] = content;
    
    // Save to backend for all fields (both subject and email_body)
    try {
        const response = await fetch(`/update-lead/${editingUsername}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                subject: lead.subject,
                email_body: lead.email_body
            })
        });
        
        if (response.ok) {
            showToast('Changes saved successfully', 'success');
            // Update the table display
            displayResults(leads);
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to save changes', 'error');
        }
    } catch (error) {
        console.error('Failed to save changes:', error);
        showToast('Failed to save changes', 'error');
    }
    
    // Always close the modal after saving (no automatic transition)
    closeEditModal();
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
            // Create Gmail compose URL
            const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(lead.email)}&su=${encodeURIComponent(lead.subject)}&body=${encodeURIComponent(lead.email_body)}`;
            
            // Open Gmail compose in new tab
            window.open(gmailUrl, '_blank');
            
            // Mark as sent in database
            const response = await fetch(`/send-email/${username}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                showToast('Gmail opened successfully - please send the email', 'success');
                // Update local lead data
                lead.sent = true;
                lead.sent_at = new Date().toISOString();
                
                // Refresh the table to show updated status (but keep send button active)
                displayResults(leads);
            } else {
                const error = await response.json();
                showToast('Gmail geöffnet, aber Status-Update fehlgeschlagen', 'warning');
            }
        } catch (error) {
            console.error('Send email error:', error);
            showToast('Fehler beim Öffnen von Gmail', 'error');
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
            showToast(`Daten als ${format.toUpperCase()} exportiert`, 'success');
        } else {
            showToast('Datenexport fehlgeschlagen', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showToast('Fehler beim Export aufgetreten', 'error');
    }
}

// Clear all data
async function clearData() {
    if (!confirm('Bist du sicher, dass du alle Daten löschen möchtest? Dies kann nicht rückgängig gemacht werden.')) {
        return;
    }
    
    try {
        const response = await fetch('/clear-data', { method: 'POST' });
        if (response.ok) {
            leads = [];
            document.getElementById('resultsBody').innerHTML = '';
            document.getElementById('resultsSection').style.display = 'none';
            document.getElementById('emptyState').style.display = 'block';
            showToast('Alle Daten wurden gelöscht', 'success');
        } else {
            showToast('Datenlöschung fehlgeschlagen', 'error');
        }
    } catch (error) {
        console.error('Clear data error:', error);
        showToast('Fehler beim Löschen der Daten aufgetreten', 'error');
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

// Helper function to format DateTime for display
function formatDateTime(isoString) {
    if (!isoString) return '';
    
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        // If within last 24 hours, show relative time
        if (diffDays === 0) {
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffMinutes = Math.floor(diffMs / (1000 * 60));
            
            if (diffHours === 0) {
                if (diffMinutes === 0) {
                    return 'gerade eben';
                } else if (diffMinutes === 1) {
                    return 'vor 1 Minute';
                } else {
                    return `vor ${diffMinutes} Minuten`;
                }
            } else if (diffHours === 1) {
                return 'vor 1 Stunde';
            } else {
                return `vor ${diffHours} Stunden`;
            }
        }
        // If yesterday
        else if (diffDays === 1) {
            return `gestern ${date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
        }
        // If within this week, show day and time
        else if (diffDays < 7) {
            const weekdays = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
            return `${weekdays[date.getDay()]} ${date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
        }
        // Otherwise show date and time
        else {
            return date.toLocaleString('de-DE', { 
                day: '2-digit', 
                month: '2-digit', 
                year: '2-digit',
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    } catch (error) {
        console.error('Error formatting date:', error);
        return '';
    }
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

// Email template auto-save functionality
function initializeEmailTemplateAutoSave() {
    const subjectPrompt = document.getElementById('subjectPrompt');
    const bodyPrompt = document.getElementById('bodyPrompt');
    
    if (!subjectPrompt || !bodyPrompt) return;
    
    // Debounced save function (wait 2 seconds after user stops typing)
    const debouncedSave = debounce(saveEmailTemplates, 2000);
    
    // Add event listeners for textarea changes
    subjectPrompt.addEventListener('input', debouncedSave);
    bodyPrompt.addEventListener('input', debouncedSave);
    
    // Also save on blur (when user clicks away)
    subjectPrompt.addEventListener('blur', () => {
        setTimeout(saveEmailTemplates, 100); // Small delay to ensure value is updated
    });
    bodyPrompt.addEventListener('blur', () => {
        setTimeout(saveEmailTemplates, 100);
    });
}

// Update template prompts based on selected product
async function updateTemplatePromptsBasedOnProduct() {
    const defaultProductSelect = document.getElementById('defaultProductSelect');
    const subjectPrompt = document.getElementById('subjectPrompt');
    const bodyPrompt = document.getElementById('bodyPrompt');
    
    if (!defaultProductSelect || !subjectPrompt || !bodyPrompt) return;
    
    const hasProduct = defaultProductSelect.value !== '';
    const templates = hasProduct ? TEMPLATE_PROMPTS.withProduct : TEMPLATE_PROMPTS.withoutProduct;
    
    // Update the textarea values
    subjectPrompt.value = templates.subject;
    bodyPrompt.value = templates.body;
    
    // Save the updated templates automatically
    saveEmailTemplates();
    
    // Save the default product selection to session
    try {
        const response = await fetch('/api/set-default-product', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                product_id: defaultProductSelect.value || null 
            })
        });
        
        if (!response.ok) {
            console.error('Failed to save default product to session');
        }
    } catch (error) {
        console.error('Error saving default product:', error);
    }
    
    // Show user feedback
    const productName = hasProduct ? 
        products.find(p => p.id == defaultProductSelect.value)?.name || 'Produkt' : 
        'Kein Produkt';
    
    showToast(`Email-Templates aktualisiert für: ${productName}`, 'success');
}

async function saveEmailTemplates() {
    const subjectPrompt = document.getElementById('subjectPrompt');
    const bodyPrompt = document.getElementById('bodyPrompt');
    
    if (!subjectPrompt || !bodyPrompt) return;
    
    const templates = {
        subject: subjectPrompt.value,
        body: bodyPrompt.value
    };
    
    try {
        const response = await fetch('/api/email-templates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templates)
        });
        
        if (response.ok) {
            const result = await response.json();
            // Show subtle success feedback
            showToast('Email-Vorlagen automatisch gespeichert', 'success');
        } else {
            const error = await response.json();
            console.error('Failed to save email templates:', error);
            showToast('Speichern der Email-Vorlagen fehlgeschlagen', 'error');
        }
    } catch (error) {
        console.error('Error saving email templates:', error);
        showToast('Speichern der Email-Vorlagen fehlgeschlagen', 'error');
    }
}

// Product management functions
async function loadProducts() {
    try {
        const response = await fetch('/api/products');
        if (response.ok) {
            const data = await response.json();
            products = data.products || [];
            populateProductSelectors();
        } else {
            console.error('Failed to load products');
        }
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function populateProductSelectors() {
    const defaultProductSelect = document.getElementById('defaultProductSelect');
    if (defaultProductSelect) {
        // Clear existing options (except the first one)
        while (defaultProductSelect.children.length > 1) {
            defaultProductSelect.removeChild(defaultProductSelect.lastChild);
        }
        
        // Add product options
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.name;
            defaultProductSelect.appendChild(option);
        });
        
        // Add event listener for default product selection
        defaultProductSelect.addEventListener('change', function() {
            defaultProductId = this.value ? parseInt(this.value) : null;
        });
    }
}

function createProductSelector(selectedProductId = null) {
    const select = document.createElement('select');
    select.className = 'form-control form-control-sm';
    select.style.minWidth = '120px';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Kein Produkt';
    select.appendChild(defaultOption);
    
    // Add product options
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = product.name;
        if (selectedProductId && selectedProductId == product.id) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    return select;
}

async function updateLeadProduct(username, productId) {
    try {
        const response = await fetch(`/api/leads/${username}/product`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ product_id: productId })
        });
        
        if (response.ok) {
            showToast('Product updated successfully', 'success');
            return true;
        } else {
            const error = await response.json();
            console.error('Failed to update product:', error);
            showToast('Failed to update product', 'error');
            return false;
        }
    } catch (error) {
        console.error('Error updating product:', error);
        showToast('Failed to update product', 'error');
        return false;
    }
}

function getProductNameById(productId) {
    if (!productId) return '';
    const product = products.find(p => p.id == productId);
    return product ? product.name : '';
}

// Edit product selection inline
function editProductSelection(username) {
    const cell = document.getElementById(`product-cell-${username}`);
    if (cell.classList.contains('editing')) return;
    
    const lead = leads.find(l => l.username === username);
    if (!lead) return;
    
    cell.classList.add('editing');
    const select = createProductSelector(lead.selectedProductId);
    
    cell.innerHTML = '';
    cell.appendChild(select);
    select.focus();
    
    select.addEventListener('change', async () => {
        const newProductId = select.value ? parseInt(select.value) : null;
        const success = await updateLeadProduct(username, newProductId);
        
        if (success) {
            // Update the lead data
            lead.selectedProductId = newProductId;
            
            // Update the cell display
            cell.classList.remove('editing');
            cell.innerHTML = getProductNameById(newProductId) || '<span style="color: var(--color-light-gray);">Kein Produkt</span>';
        } else {
            // Revert on failure
            finishProductEdit(cell, lead.selectedProductId);
        }
    });
    
    select.addEventListener('blur', () => {
        // If no change was made, revert
        setTimeout(() => {
            if (cell.classList.contains('editing')) {
                finishProductEdit(cell, lead.selectedProductId);
            }
        }, 100);
    });
}

function finishProductEdit(cell, originalProductId) {
    cell.classList.remove('editing');
    cell.innerHTML = getProductNameById(originalProductId) || '<span style="color: var(--color-light-gray);">Kein Produkt</span>';
}