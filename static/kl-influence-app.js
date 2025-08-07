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

// Pagination variables
let currentPage = 1;
let pageSize = 25;
let totalRows = 0;
let filteredRows = [];
let allRows = [];

// Template prompts for different scenarios
const TEMPLATE_PROMPTS = {
    withProduct: {
        subject: 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Falls ein Produkt ausgewählt ist, erwähne es subtil in der Betreffzeile. Antworte nur mit der Betreffzeile, ohne zusätzliche Formatierung.',
        body: 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. WICHTIG: Falls ein Produkt ausgewählt ist, integriere unbedingt folgende Elemente in die E-Mail: 1) Erwähne das Produkt namentlich, 2) Füge den direkten Link zum Produkt ein (Produkt-URL), 3) Erkläre kurz die Produkteigenschaften basierend auf der Beschreibung, 4) Beziehe das Produkt auf die Bio/Interessen des Influencers. Die E-Mail sollte den Produktlink natürlich in den Text einbetten. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte nur mit dem Email-Inhalt, ohne zusätzliche Formatierung.'
    },
    withoutProduct: {
        subject: 'Schreibe in DU-Form eine persönliche Betreffzeile mit freundlichen Hook für eine Influencer Kooperation mit Kasimir + Liselotte. Nutze persönliche Infos (z.B. Username, BIO, Interessen), sprich sie direkt in DU-Form. Fokussiere dich auf die Interessen und den Content des Influencers. Antworte nur mit der Betreffzeile, ohne zusätzliche Formatierung.',
        body: 'Erstelle eine personalisierte, professionelle deutsche E-Mail, ohne die Betreffzeile, für potenzielle Instagram Influencer Kooperationen. Die E-Mail kommt von Kasimir vom Store KasimirLieselotte. Verwende einen höflichen, professionellen Ton auf Deutsch aber in DU-Form um es casual im Instagram feel zu bleiben. Fokussiere dich auf eine allgemeine Kooperationsanfrage, die auf die Interessen und den Content des Influencers eingeht. Erwähne deine Begeisterung für ihren Content und schlage eine mögliche Zusammenarbeit vor, ohne spezifische Produkte zu erwähnen. Füge am Ende die Signatur mit der Website https://www.kasimirlieselotte.de/ hinzu. Antworte nur mit dem Email-Inhalt, ohne zusätzliche Formatierung.'
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    checkSessionId();
    initializeTableFilters();
    initializeColumnResizing();
    
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
    } else {
        // If no leads data in window, fetch from API
        fetchAndDisplayAllLeadsOnStartup();
    }
    
    // Initialize UI state for resource protection
    updateUIState();
    
    // Initialize Prompt Settings
    initializePromptSettings();
    
    // Initialize pagination
    initializePagination();
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
    

    
    // Email template auto-save
    initializeEmailTemplateAutoSave();
    
    // Default product selector change
    document.getElementById('defaultProductSelect')?.addEventListener('change', updateTemplatePromptsBasedOnProduct);
    
    // Modal close on background click (except for prompt settings modal, edit modal, product edit modal, and email campaign modal)
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal && modal.id !== 'promptSettingsModal' && modal.id !== 'editModal' && modal.id !== 'productEditModal' && modal.id !== 'emailCampaignModal') {
                closeModal(modal.id);
            }
        });
    });
    
    // Keyboard navigation for table
    document.addEventListener('keydown', handleTableKeyNavigation);
    
    // Mobile input field optimization
    optimizeMobileInputs();
    
    // Emergency restart button
    document.getElementById('emergencyRestartBtn')?.addEventListener('click', emergencyRestart);
}

// Initialize table filters
function initializeTableFilters() {
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('input', debounce(applyFilters, 300));
    });
    
    // Set up follower range filter
    const followerRangeSelect = document.getElementById('filterFollowersRange');
    const followerCustomInput = document.getElementById('filterFollowers');
    
    if (followerRangeSelect) {
        followerRangeSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            console.log('Follower range selected:', selectedValue);
            
            if (selectedValue === 'custom') {
                // Show custom input for advanced users
                followerCustomInput.style.display = 'block';
                followerCustomInput.focus();
            } else {
                // Hide custom input
                followerCustomInput.style.display = 'none';
                followerCustomInput.value = '';
            }
            applyFilters();
        });
    }
    
    // Set up personal only filter checkbox
    const personalOnlyCheckbox = document.getElementById('filterPersonalOnly');
    if (personalOnlyCheckbox) {
        personalOnlyCheckbox.addEventListener('change', function() {
            console.log('Personal only filter:', this.checked);
            applyFilters();
        });
    }
    
    // Set up post date filter
    const postDateSelect = document.getElementById('filterPostDate');
    const postDateCustom = document.getElementById('filterPostDateCustom');
    const customDateRange = document.getElementById('customDateRange');
    const postDateStart = document.getElementById('filterPostDateStart');
    const postDateEnd = document.getElementById('filterPostDateEnd');
    
    if (postDateSelect) {
        postDateSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            console.log('Post date filter selected:', selectedValue);
            
            // Hide all custom inputs first
            if (postDateCustom) postDateCustom.style.display = 'none';
            if (customDateRange) customDateRange.style.display = 'none';
            
            // Show appropriate custom input based on selection
            if (selectedValue === 'alter-als' && postDateCustom) {
                postDateCustom.style.display = 'block';
            } else if (selectedValue === 'benutzerdefiniert' && customDateRange) {
                customDateRange.style.display = 'block';
            }
            
            applyFilters();
        });
    }
    
    // Set up custom date inputs
    if (postDateCustom) {
        postDateCustom.addEventListener('change', applyFilters);
    }
    if (postDateStart) {
        postDateStart.addEventListener('change', applyFilters);
    }
    if (postDateEnd) {
        postDateEnd.addEventListener('change', applyFilters);
    }
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
    const followerRangeSelect = document.getElementById('filterFollowersRange');
    const followerCustomInput = document.getElementById('filterFollowers');
    
    // Get follower filter value from range select or custom input
    let followerFilter = '';
    if (followerRangeSelect && followerRangeSelect.value !== 'custom' && followerRangeSelect.value !== '') {
        followerFilter = followerRangeSelect.value;
    } else if (followerCustomInput && followerCustomInput.value !== '') {
        followerFilter = followerCustomInput.value;
    }
    
    const filters = {
        nameUsername: document.getElementById('filterNameUsername')?.value.toLowerCase() || '',
        hashtag: document.getElementById('filterHashtag')?.value.toLowerCase() || '',
        followers: followerFilter,
        personalOnly: document.getElementById('filterPersonalOnly')?.checked || false,
        email: document.getElementById('filterEmail')?.value.toLowerCase() || '',
        website: document.getElementById('filterWebsite')?.value.toLowerCase() || '',
        postDate: document.getElementById('filterPostDate')?.value || '',
        emailStatus: document.getElementById('filterEmailStatus')?.value.toLowerCase() || ''
    };
    
    const tbody = document.getElementById('resultsBody');
    const rows = tbody.querySelectorAll('tr');
    
    // Clear the filtered rows array and reset to page 1
    currentPage = 1;
    filteredRows = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length === 0) return;
        
        const username = cells[1]?.textContent.toLowerCase() || '';
        const hashtag = cells[2]?.textContent.toLowerCase() || '';
        const followersText = cells[3]?.textContent || '0';
        const followers = parseFollowerCount(followersText);
        const email = cells[4]?.textContent.toLowerCase() || '';
        const website = cells[5]?.textContent.toLowerCase() || '';
        const postDate = cells[6]?.textContent.toLowerCase() || '';
        const emailStatus = cells[7]?.textContent.toLowerCase() || '';
        
        let show = true;
        
        // Text filters - combined name/username filter
        if (filters.nameUsername) {
            const nameUsernameText = cells[1]?.textContent.toLowerCase() || '';
            if (!nameUsernameText.includes(filters.nameUsername)) show = false;
        }
        if (filters.hashtag && !hashtag.includes(filters.hashtag)) show = false;
        if (filters.email && !email.includes(filters.email)) show = false;
        if (filters.website && !website.includes(filters.website)) show = false;
        if (filters.emailStatus && !emailStatus.includes(filters.emailStatus)) show = false;
        
        // Personal only filter - need to check the lead data directly since we removed the column
        if (filters.personalOnly) {
            // Find the lead data for this row to check isBusiness property
            const leadIndex = parseInt(cells[0]?.textContent) - 1;
            if (leadIndex >= 0 && leads && leads[leadIndex] && leads[leadIndex].isBusiness) {
                show = false; // Hide business accounts when "Nur Personal" is checked
            }
        }
        
        // Date filter
        if (filters.postDate) {
            const leadIndex = parseInt(cells[0]?.textContent) - 1;
            if (leadIndex >= 0 && leads && leads[leadIndex]) {
                const lead = leads[leadIndex];
                if (lead.sourceTimestamp) {
                    const postDate = new Date(lead.sourceTimestamp);
                    const now = new Date();
                    
                    switch (filters.postDate) {
                        case 'letzte-woche':
                            // Previous Monday to Sunday
                            const lastMonday = new Date(now);
                            const daysSinceMonday = (now.getDay() + 6) % 7; // 0=Sunday, 1=Monday, etc.
                            lastMonday.setDate(now.getDate() - daysSinceMonday - 7);
                            lastMonday.setHours(0, 0, 0, 0);
                            
                            const lastSunday = new Date(lastMonday);
                            lastSunday.setDate(lastMonday.getDate() + 6);
                            lastSunday.setHours(23, 59, 59, 999);
                            
                            if (postDate < lastMonday || postDate > lastSunday) show = false;
                            break;
                            
                        case 'letzten-monat':
                            // Previous calendar month
                            const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                            const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999);
                            if (postDate < lastMonth || postDate > lastMonthEnd) show = false;
                            break;
                            
                        case 'dieses-jahr':
                            // January 1 of current year to today
                            const yearStart = new Date(now.getFullYear(), 0, 1);
                            if (postDate < yearStart || postDate > now) show = false;
                            break;
                            
                        case 'alter-als':
                            // Older than custom date
                            const customDate = document.getElementById('filterPostDateCustom')?.value;
                            if (customDate) {
                                const targetDate = new Date(customDate);
                                if (postDate >= targetDate) show = false;
                            }
                            break;
                            
                        case 'benutzerdefiniert':
                            // Custom date range
                            const startDate = document.getElementById('filterPostDateStart')?.value;
                            const endDate = document.getElementById('filterPostDateEnd')?.value;
                            if (startDate && endDate) {
                                const start = new Date(startDate);
                                const end = new Date(endDate);
                                end.setHours(23, 59, 59, 999); // Include full end date
                                if (postDate < start || postDate > end) show = false;
                            }
                            break;
                    }
                } else {
                    // No post date - hide when any date filter is active
                    show = false;
                }
            }
        }
        
        // Numeric filter for followers
        if (filters.followers) {
            console.log('Filtering followers:', followersText, 'parsed to:', followers, 'filter:', filters.followers);
            
            // Check if it's a range filter (e.g., "1000-10000")
            if (filters.followers.includes('-') && !filters.followers.startsWith('-')) {
                const [minStr, maxStr] = filters.followers.split('-');
                const minValue = parseInt(minStr);
                const maxValue = parseInt(maxStr);
                
                console.log('Range filter:', minValue, '<=', followers, '<=', maxValue);
                
                if (followers < minValue || followers > maxValue) {
                    show = false;
                }
            } else {
                // Original comparison operators for custom input
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
        }
        
        // Add to filtered rows if it should be shown
        if (show) {
            filteredRows.push(row);
        }
    });
    
    // Update pagination after filtering
    currentPage = 1; // Reset to first page
    updatePagination();
}

// Clear all filters
function clearFilters() {
    document.querySelectorAll('.filter-input').forEach(input => {
        input.value = '';
    });
    
    // Reset follower range filter
    const followerRangeSelect = document.getElementById('filterFollowersRange');
    const followerCustomInput = document.getElementById('filterFollowers');
    if (followerRangeSelect) {
        followerRangeSelect.value = '';
    }
    if (followerCustomInput) {
        followerCustomInput.style.display = 'none';
        followerCustomInput.value = '';
    }
    
    // Reset personal only filter to checked (default state)
    const personalOnlyCheckbox = document.getElementById('filterPersonalOnly');
    if (personalOnlyCheckbox) {
        personalOnlyCheckbox.checked = true;
    }
    
    // Reset post date filter
    const postDateSelect = document.getElementById('filterPostDate');
    const postDateCustom = document.getElementById('filterPostDateCustom');
    const customDateRange = document.getElementById('customDateRange');
    const postDateStart = document.getElementById('filterPostDateStart');
    const postDateEnd = document.getElementById('filterPostDateEnd');
    
    if (postDateSelect) {
        postDateSelect.value = '';
    }
    if (postDateCustom) {
        postDateCustom.style.display = 'none';
        postDateCustom.value = '';
    }
    if (customDateRange) {
        customDateRange.style.display = 'none';
    }
    if (postDateStart) {
        postDateStart.value = '';
    }
    if (postDateEnd) {
        postDateEnd.value = '';
    }
    
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
// Legacy function - updated for Bootstrap 5 compatibility
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        if (modal.classList.contains('modal')) {
            // Bootstrap 5 modal
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            } else {
                modal.classList.remove('show');
            }
        } else {
            // Legacy modal
            modal.classList.remove('show');
            modal.style.display = 'none';
        }
    }
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
    
    // Check if email generation is in progress
    if (isEmailDraftGenerationInProgress) {
        showToast('Email-Generierung läuft bereits. Bitte warten bis diese abgeschlossen ist.', 'warning');
        return;
    }
    
    const runButton = document.getElementById('runButton');
    
    // Set lead generation state
    setLeadGenerationState(true);
    
    // Update UI for processing state
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    // Show processing status with detailed initial step
    document.getElementById('processingStatus').style.display = 'block';
    document.getElementById('statusText').textContent = '1. Suche Instagram-Profile für Hashtag wird vorbereitet...';
    document.getElementById('progressText').textContent = 'Phase: Initialisierung der Hashtag-Suche';
    
    // Reset previous lead count for new processing run
    previousLeadCount = 0;
    
    // Start progress polling
    const progressInterval = setInterval(updateProgress, 2000);
    
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
        
        clearInterval(progressInterval);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Process response:', result); // Debug log
            if (result.success && result.phase === 'hashtag_selection') {
                // Handle hashtag selection phase
                clearInterval(progressInterval);
                showHashtagSelection(result.hashtag_variants);
                showToast(`Found ${result.hashtag_variants.length} hashtag variants`, 'success');
            } else if (result.success && result.leads) {
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
        clearInterval(progressInterval);
        console.error('Processing error:', error);
        if (error.name === 'AbortError') {
            showToast('Anfrage ist abgelaufen. Bitte versuche es mit einem kleineren Suchlimit erneut.', 'error');
        } else if (error.message && error.message.includes('fetch')) {
            showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung und versuche es erneut.', 'error');
        } else {
            showToast(`Verarbeitungsfehler: ${error.message || 'Unbekannter Fehler'}`, 'error');
        }
    } finally {
        // Reset lead generation state and button states
        setLeadGenerationState(false);
        resetProcessingUI();
    }
}

// Track previous lead count to detect new leads
let previousLeadCount = 0;

// Global state management for resource protection
let isLeadGenerationInProgress = false;
let isEmailDraftGenerationInProgress = false;

// Function to fetch and display all leads on startup
async function fetchAndDisplayAllLeadsOnStartup() {
    try {
        const response = await fetch('/api/leads');
        if (response.ok) {
            const result = await response.json();
            
            // Handle new response format with success flag
            if (result.success !== false && result.leads && Array.isArray(result.leads)) {
                if (result.leads.length > 0) {
                    console.log(`Loading ${result.leads.length} leads on startup`);
                    displayResults(result.leads);
                } else {
                    // Show empty state if no leads found
                    const emptyState = document.getElementById('emptyState');
                    if (emptyState) {
                        emptyState.style.display = 'block';
                    }
                }
            } else {
                console.error('API returned error or invalid format on startup:', result);
                // Show empty state on error
                const emptyState = document.getElementById('emptyState');
                if (emptyState) {
                    emptyState.style.display = 'block';
                }
            }
        } else {
            console.error('Failed to fetch leads on startup:', response.status);
        }
    } catch (error) {
        console.error('Error fetching leads on startup:', error);
        // Show empty state on error
        const emptyState = document.getElementById('emptyState');
        if (emptyState) {
            emptyState.style.display = 'block';
        }
    }
}

// Function to update UI based on current processing states
function updateUIState() {
    // Lead Generation UI elements
    const runButton = document.getElementById('runButton');
    const keywordInput = document.getElementById('keywordInput');
    const searchLimitInput = document.getElementById('searchLimitInput');
    
    // Email Generation buttons in table (will be updated when table is rendered)
    const emailButtons = document.querySelectorAll('button[onclick*="generateEmailContent"]');
    
    // Update Lead Generation UI
    if (isEmailDraftGenerationInProgress) {
        runButton.disabled = true;
        runButton.style.opacity = '0.5';
        runButton.title = 'Email-Generierung läuft - bitte warten';
        keywordInput.disabled = true;
        searchLimitInput.disabled = true;
    } else {
        if (!isLeadGenerationInProgress) {
            runButton.disabled = false;
            runButton.style.opacity = '1';
            runButton.title = '';
            keywordInput.disabled = false;
            searchLimitInput.disabled = false;
        }
    }
    
    // Update Email Generation buttons
    emailButtons.forEach(button => {
        if (isLeadGenerationInProgress) {
            button.disabled = true;
            button.style.opacity = '0.5';
            button.title = 'Lead-Generierung läuft - bitte warten';
        } else if (isEmailDraftGenerationInProgress) {
            button.disabled = true;
            button.style.opacity = '0.5';
            button.title = 'Email-Generierung bereits in Bearbeitung';
        } else {
            button.disabled = false;
            button.style.opacity = '1';
            button.title = 'Email generieren';
        }
    });
}

// Function to set lead generation state
function setLeadGenerationState(inProgress) {
    isLeadGenerationInProgress = inProgress;
    updateUIState();
}

// Function to set email draft generation state
function setEmailDraftGenerationState(inProgress) {
    isEmailDraftGenerationInProgress = inProgress;
    updateUIState();
}

// Show hashtag selection UI
function showHashtagSelection(hashtag_variants) {
    // Hide processing status
    document.getElementById('processingStatus').style.display = 'none';
    
    // Create hashtag selection UI
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    
    const selectionContainer = document.createElement('div');
    selectionContainer.className = 'hashtag-selection-container p-4';
    selectionContainer.innerHTML = `
        <h3 class="mb-4">Hashtag-Varianten gefunden</h3>
        <p class="text-muted mb-4">Wählen Sie die Hashtags aus, für die Sie Profile anreichern möchten:</p>
        <div id="hashtagList" class="mb-4"></div>
        <div class="d-flex gap-2">
            <button id="selectAllHashtags" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-check-square"></i> Alle auswählen
            </button>
            <button id="deselectAllHashtags" class="btn btn-sm btn-outline-secondary">
                <i class="far fa-square"></i> Alle abwählen
            </button>
        </div>
        <div class="mt-4">
            <button id="continueEnrichment" class="btn btn-primary">
                <i class="fas fa-arrow-right"></i> Mit Anreicherung fortfahren
            </button>
            <button id="cancelSelection" class="btn btn-secondary">
                <i class="fas fa-times"></i> Abbrechen
            </button>
        </div>
    `;
    
    resultsContainer.appendChild(selectionContainer);
    
    // Populate hashtag list
    const hashtagList = document.getElementById('hashtagList');
    hashtag_variants.forEach((variant, index) => {
        const hashtagItem = document.createElement('div');
        hashtagItem.className = 'form-check mb-2';
        hashtagItem.innerHTML = `
            <input class="form-check-input hashtag-checkbox" type="checkbox" 
                   value="${variant.hashtag}" id="hashtag${index}" checked>
            <label class="form-check-label" for="hashtag${index}">
                <strong>#${variant.hashtag}</strong> - ${variant.user_count} Profile
            </label>
        `;
        hashtagList.appendChild(hashtagItem);
    });
    
    // Function to revert to leads table
    function revertToLeadsTable() {
        resultsContainer.innerHTML = '';
        setLeadGenerationState(false);
        resetProcessingUI();
        
        // Refresh and show current leads table (fetch all leads)
        fetchAndDisplayAllLeads();
        
        // Show a message about reverting
        showToast('Zurück zur Leads-Tabelle', 'info');
    }
    
    // Helper function to fetch and display all current leads
    async function fetchAndDisplayAllLeads() {
        try {
            const response = await fetch('/api/leads');
            if (response.ok) {
                const result = await response.json();
                
                // Handle new response format with success flag
                if (result.success !== false && result.leads && Array.isArray(result.leads)) {
                    if (result.leads.length > 0) {
                        displayResults(result.leads);
                    } else {
                        // Show empty state if no leads - with null check
                        const emptyState = document.getElementById('emptyState');
                        if (emptyState) {
                            emptyState.style.display = 'block';
                        }
                    }
                } else {
                    // Handle error response or missing leads array
                    console.error('API returned error or invalid format:', result);
                    const emptyState = document.getElementById('emptyState');
                    if (emptyState) {
                        emptyState.style.display = 'block';
                    }
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error fetching leads:', error);
            // Show empty state on error - with null check
            const emptyState = document.getElementById('emptyState');
            if (emptyState) {
                emptyState.style.display = 'block';
            }
        }
    }
    
    // Removed global click listener to prevent premature UI closure
    
    // Add event listeners
    document.getElementById('selectAllHashtags').addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.hashtag-checkbox').forEach(cb => cb.checked = true);
    });
    
    document.getElementById('deselectAllHashtags').addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.hashtag-checkbox').forEach(cb => cb.checked = false);
    });
    
    document.getElementById('continueEnrichment').addEventListener('click', (e) => {
        e.stopPropagation();
        continueWithEnrichment();
    });
    
    document.getElementById('cancelSelection').addEventListener('click', (e) => {
        e.stopPropagation();
        revertToLeadsTable();
        showToast('Verarbeitung abgebrochen', 'info');
    });
    
    // Checkboxes no longer trigger auto-revert to allow proper selection
}

// Continue with enrichment for selected hashtags
async function continueWithEnrichment() {
    const selectedHashtags = [];
    document.querySelectorAll('.hashtag-checkbox:checked').forEach(cb => {
        selectedHashtags.push(cb.value);
    });
    
    if (selectedHashtags.length === 0) {
        showToast('Bitte wählen Sie mindestens einen Hashtag aus', 'warning');
        return;
    }
    
    // Hide selection UI and show processing status
    document.getElementById('resultsContainer').innerHTML = '';
    document.getElementById('processingStatus').style.display = 'block';
    document.getElementById('statusText').textContent = '2. Starte Profil-Anreicherung...';
    
    // Start progress polling
    const progressInterval = setInterval(updateProgress, 2000);
    
    try {
        const response = await fetch('/continue-enrichment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                selected_hashtags: selectedHashtags
            }),
            timeout: 7320000 // 2h 2min timeout
        });
        
        clearInterval(progressInterval);
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.leads) {
                displayResults(result.leads);
                showToast(`Successfully generated ${result.leads.length} leads`, 'success');
            } else {
                // Even if no new leads, show existing data table
                if (leads && leads.length > 0) {
                    displayResults(leads);
                } else {
                    document.getElementById('emptyState').style.display = 'block';
                }
                showToast(result.message || 'No leads found', 'warning');
            }
        } else {
            const error = await response.json();
            // Show existing data table on error too
            if (leads && leads.length > 0) {
                displayResults(leads);
            } else {
                document.getElementById('emptyState').style.display = 'block';
            }
            showToast(error.error || 'Failed to enrich profiles', 'error');
        }
    } catch (error) {
        clearInterval(progressInterval);
        console.error('Enrichment error:', error);
        showToast(`Enrichment error: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        setLeadGenerationState(false);
        resetProcessingUI();
    }
}

// Update progress
async function updateProgress() {
    try {
        const response = await fetch('/progress');
        if (response.ok) {
            const progress = await response.json();
            
            // Update status display with more detailed information
            if (progress.current_step && progress.current_step.trim() !== '') {
                document.getElementById('statusText').textContent = progress.current_step;
                
                // Ensure processing status is visible during processing
                if (progress.phase && progress.phase !== 'completed') {
                    document.getElementById('processingStatus').style.display = 'block';
                }
            }
            

            // Keep progress display simple - just show basic step information
            let progressHTML = '';
            
            if (progress.total_steps > 0) {
                const percentage = Math.round((progress.completed_steps / progress.total_steps) * 100);
                progressHTML += `Fortschritt: ${progress.completed_steps}/${progress.total_steps} (${percentage}%)`;
            }
            
            if (progressHTML) {
                document.getElementById('progressText').innerHTML = progressHTML;
            }
            
            // Handle incremental lead updates - detect when lead count changes
            if (progress.incremental_leads !== undefined && progress.keyword) {
                // Check if we have new leads (count increased) OR if we haven't refreshed yet
                if (progress.incremental_leads > previousLeadCount || (progress.incremental_leads > 0 && previousLeadCount === 0)) {
                    console.log(`New leads detected: ${progress.incremental_leads} (was ${previousLeadCount}) for keyword: ${progress.keyword}`);
                    const newLeadsCount = progress.incremental_leads - previousLeadCount;
                    previousLeadCount = progress.incremental_leads;
                    
                    // Show notification only for significant new leads (batches of 3 or more) and throttle notifications
                    if (newLeadsCount >= 3) {
                        const now = Date.now();
                        // Only show notification if at least 3 seconds have passed since last notification
                        if (now - lastNotificationTime > 3000) {
                            const notificationText = `+${newLeadsCount} neue Leads generiert (${progress.incremental_leads} gesamt)`;
                            showToast(notificationText, 'success');
                            lastNotificationTime = now;
                        }
                    }
                    
                    // Always refresh the table when lead count changes
                    await refreshLeadsTable(progress.keyword);
                }
            }
            
            // Handle completion status
            if (progress.final_status === 'success' && progress.total_leads_generated !== undefined) {
                showToast(`Erfolgreich ${progress.total_leads_generated} Leads generiert!`, 'success');
                // Reset previous lead count for next run
                previousLeadCount = 0;
                resetProcessingUI();
            } else if (progress.final_status === 'stopped') {
                showToast('Verarbeitung gestoppt', 'warning');
                resetProcessingUI();
            }
        }
    } catch (error) {
        console.error('Progress update error:', error);
    }
}

// Reset processing UI to initial state
function resetProcessingUI() {
    const runButton = document.getElementById('runButton');
    
    // Reset run button
    runButton.disabled = false;
    runButton.innerHTML = '<i class="fas fa-play"></i><span>Leads generieren</span>';
    
    // Hide processing status
    document.getElementById('processingStatus').style.display = 'none';
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
            
            // Handle new response format with success flag
            if (result.success !== false && result.leads && Array.isArray(result.leads)) {
                if (result.leads.length > 0) {
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
                } else {
                    console.log(`No leads found for keyword: ${keyword}`);
                }
            } else {
                console.error('API returned error or invalid format:', result);
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
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
    
    // Store all rows for pagination
    allRows = [];
    filteredRows = [];
    
    leads.forEach((lead, index) => {
        const row = createLeadRow(lead, index);
        tbody.appendChild(row);
        allRows.push(row);
    });
    
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('emptyState').style.display = 'none';
    
    // Apply any existing filters (this will populate filteredRows)
    applyFilters();
    
    // Initialize column resizing for the table (if not already done)
    initializeColumnResizing();
    
    // Add reset button to action bar
    addColumnWidthResetButton();
    
    // Update UI state to ensure buttons have correct disabled/enabled states
    updateUIState();
}

// Create lead row
function createLeadRow(lead, index) {
    const row = document.createElement('tr');
    if (lead.is_duplicate) {
        row.style.backgroundColor = 'rgba(255, 165, 0, 0.1)';
    }
    
    // Get email status
    const emailStatus = getEmailStatus(lead);
    
    // Mobile data attributes
    row.innerHTML = `
        <td data-label="#">${index + 1}</td>
        <td data-label="Name/Benutzername">
            ${lead.full_name ? `${lead.full_name} (` : ''}
            <a href="https://www.instagram.com/${lead.username}" target="_blank" rel="noopener noreferrer" style="color: var(--color-natural-green);">
                @${lead.username}
            </a>
            ${lead.full_name ? ')' : ''}
            ${lead.is_duplicate ? '<br><small class="text-warning">Duplikat</small>' : ''}
        </td>
        <td data-label="Hashtag">${lead.hashtag || '-'}</td>
        <td data-label="Follower">${formatNumber(lead.followers_count || lead.followersCount || 0)}</td>
        <td data-label="Email" class="editable-cell" onclick="startInlineEdit(this, '${lead.username}', 'email')">
            ${lead.email || '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>'}
        </td>
        <td data-label="Website" class="editable-cell" onclick="startInlineEdit(this, '${lead.username}', 'website')">
            ${(lead.website || lead.external_url) ? 
                `<a href="${lead.website || lead.external_url}" target="_blank" rel="noopener noreferrer" style="color: var(--color-natural-green);">${(lead.website || lead.external_url).substring(0, 30)}${(lead.website || lead.external_url).length > 30 ? '...' : ''}</a>` : 
                '<span style="color: var(--color-light-gray);">Klicken zum Hinzufügen</span>'
            }
        </td>
        <td data-label="Post Datum">
            ${lead.sourceTimestamp ? 
                `<a href="${lead.sourcePostUrl || '#'}" target="_blank" rel="noopener noreferrer" style="color: var(--color-natural-green);">${formatGermanDateOnly(lead.sourceTimestamp)}</a>` : 
                '-'
            }
        </td>
        <td data-label="Email Status">
            <span class="email-status ${emailStatus.class}">
                <i class="fas ${emailStatus.class === 'gesendet' ? 'fa-check-circle' : emailStatus.class === 'entwurf' ? 'fa-edit' : 'fa-circle'}"></i>
                ${emailStatus.text}
                ${lead.sent && lead.sent_at ? `<br><small>${formatDate(lead.sent_at)}</small>` : ''}
            </span>
        </td>
        <td data-label="Aktionen">
            <button class="btn btn-email-setup" onclick="openEmailWorkspace('${lead.id}', '${lead.username}')" title="Email Workspace">
                <i class="fas fa-envelope-open-text"></i> Email Setup
            </button>
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
    
    // Check if lead generation is in progress
    if (isLeadGenerationInProgress) {
        showToast('Lead-Generierung läuft bereits. Bitte warten bis diese abgeschlossen ist.', 'warning');
        return;
    }
    
    // Check if another email is being generated
    if (isEmailDraftGenerationInProgress) {
        showToast('Email-Generierung bereits in Bearbeitung. Bitte warten bis diese abgeschlossen ist.', 'warning');
        return;
    }
    
    // Set email draft generation state
    setEmailDraftGenerationState(true);
    
    // Show loading state
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generiert...';
    button.disabled = true;
    
    try {
        // Only apply default product if lead doesn't already have a manually assigned product
        const defaultProductSelect = document.getElementById('defaultProductSelect');
        const defaultProductId = defaultProductSelect ? defaultProductSelect.value : null;
        
        // Check if lead already has a product assigned (respect manual selections)
        const hasExistingProduct = lead.selectedProductId || lead.selected_product_id;
        
        if (defaultProductSelect && !hasExistingProduct && defaultProductId) {
            // Only apply default product if no product is currently assigned
            await fetch(`/api/leads/${username}/product`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: defaultProductId })
            });
            
            // Update local lead data with default product
            lead.selected_product_id = parseInt(defaultProductId);
            lead.selectedProductId = parseInt(defaultProductId);
            const selectedProduct = products.find(p => p.id == defaultProductId);
            if (selectedProduct) {
                lead.selected_product = selectedProduct;
            }
        }
        
        const response = await fetch(`/draft-email/${username}`);
        if (response.ok) {
            const result = await response.json();
            
            // Update the lead data
            lead.subject = result.subject;
            lead.email_body = result.body;
            
            // Preserve existing product assignment - don't overwrite with default
            // Only update if we actually applied a default product (for leads that had no product)
            if (!hasExistingProduct && defaultProductId) {
                lead.selectedProductId = parseInt(defaultProductId);
            }
            // If lead already had a product, keep it unchanged
            
            // Update the table display to show the current product state
            displayResults(leads);
            
            // Update the specific product cell to reflect the current product assignment
            const productCell = document.getElementById(`product-cell-${username}`);
            if (productCell) {
                const currentProductId = lead.selectedProductId || lead.selected_product_id;
                const productName = currentProductId ? getProductNameById(currentProductId) : null;
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
        // Reset email draft generation state
        setEmailDraftGenerationState(false);
        
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
    
    const modal = document.getElementById('editModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
    
    // Focus on textarea
    setTimeout(() => {
        document.getElementById('editModalContent').focus();
    }, 100);
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
    closeModal('editModal');
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
    // Determine sort direction
    if (currentSortColumn === columnIndex) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortDirection = 'asc';
        currentSortColumn = columnIndex;
    }
    
    // Sort all rows
    allRows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent;
        const bValue = b.cells[columnIndex].textContent;
        
        // Handle numeric columns
        if (columnIndex === 0 || columnIndex === 3) {
            const aNum = parseNumber(aValue);
            const bNum = parseNumber(bValue);
            return currentSortDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Text columns
        return currentSortDirection === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Re-append sorted rows to tbody
    const tbody = document.getElementById('resultsBody');
    tbody.innerHTML = '';
    allRows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    updateSortIndicators(columnIndex, currentSortDirection);
    
    // Re-apply filters and pagination
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
    console.log('Export function called with format:', format);
    try {
        console.log('Making fetch request to:', `/export/${format}`);
        const response = await fetch(`/export/${format}`);
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (response.ok) {
            if (format === 'csv') {
                // For CSV, handle as direct file download
                const blob = await response.blob();
                console.log('CSV Blob size:', blob.size);
                
                // Extract filename from Content-Disposition header
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = `instagram_leads_${new Date().toISOString().slice(0,19).replace(/:/g, '')}.csv`;
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                console.log('Download filename:', filename);
                
                const url = window.URL.createObjectURL(blob);
                console.log('Created URL:', url);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                console.log('Download link clicked');
                
                // Clean up
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);
                
                showToast(`Google Sheets kompatible CSV Datei exportiert`, 'success');
            } else {
                // For JSON, handle as before
                const result = await response.json();
                console.log('Response result keys:', Object.keys(result));
                
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
            console.error('Export failed with status:', response.status);
            const errorText = await response.text();
            console.error('Error response:', errorText);
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

// Helper function to format German date for Post Zeit column
function formatGermanDate(isoString) {
    if (!isoString) return '';
    
    try {
        const date = new Date(isoString);
        return date.toLocaleString('de-DE', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit', 
            minute: '2-digit'
        });
    } catch (error) {
        console.error('Error formatting German date:', error);
        return '';
    }
}

// Format German date only (no time)
function formatGermanDateOnly(isoString) {
    if (!isoString) return '';
    
    try {
        const date = new Date(isoString);
        return date.toLocaleDateString('de-DE', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric'
        });
    } catch (error) {
        console.error('Error formatting German date only:', error);
        return '';
    }
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function getEmailStatus(lead) {
    if (lead.sent) {
        return { class: 'gesendet', text: 'Gesendet' };
    } else if (lead.subject && lead.email_body) {
        return { class: 'entwurf', text: 'Entwurf bereit' };
    } else {
        return { class: 'nicht-gestartet', text: 'Nicht gestartet' };
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

function parseFollowerCount(str) {
    if (!str) return 0;
    return parseNumber(str);
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
async function initializeEmailTemplateAutoSave() {
    const subjectPrompt = document.getElementById('subjectPrompt');
    const bodyPrompt = document.getElementById('bodyPrompt');
    
    if (!subjectPrompt || !bodyPrompt) return;
    
    // Load existing templates from backend first
    await loadEmailTemplates();
    
    // Create save status indicators
    addSaveStatusIndicators();
    
    // Add manual save button
    addManualSaveButton();
    
    // Debounced save function (wait 2 seconds after user stops typing)
    const debouncedSave = debounce(saveEmailTemplates, 2000);
    
    // Add event listeners for textarea changes
    subjectPrompt.addEventListener('input', () => {
        showSaveStatus('typing');
        debouncedSave();
    });
    
    bodyPrompt.addEventListener('input', () => {
        showSaveStatus('typing');
        debouncedSave();
    });
    
    // Also save on blur (when user clicks away)
    subjectPrompt.addEventListener('blur', () => {
        showSaveStatus('saving');
        setTimeout(saveEmailTemplates, 100); // Small delay to ensure value is updated
    });
    bodyPrompt.addEventListener('blur', () => {
        showSaveStatus('saving');
        setTimeout(saveEmailTemplates, 100);
    });
    
    // Add keyboard shortcuts for manual save (Ctrl+S)
    subjectPrompt.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            showSaveStatus('saving');
            saveEmailTemplates();
        }
    });
    
    bodyPrompt.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            showSaveStatus('saving');
            saveEmailTemplates();
        }
    });
}

// Add save status indicators to the UI
function addSaveStatusIndicators() {
    const subjectLabel = document.querySelector('label[for="subjectPrompt"]');
    const bodyLabel = document.querySelector('label[for="bodyPrompt"]');
    
    if (subjectLabel && !subjectLabel.querySelector('.save-status')) {
        const statusSpan = document.createElement('span');
        statusSpan.className = 'save-status';
        statusSpan.id = 'subjectSaveStatus';
        statusSpan.style.cssText = 'margin-left: 10px; font-size: 0.85em; color: #666;';
        subjectLabel.appendChild(statusSpan);
    }
    
    if (bodyLabel && !bodyLabel.querySelector('.save-status')) {
        const statusSpan = document.createElement('span');
        statusSpan.className = 'save-status';
        statusSpan.id = 'bodySaveStatus';
        statusSpan.style.cssText = 'margin-left: 10px; font-size: 0.85em; color: #666;';
        bodyLabel.appendChild(statusSpan);
    }
}

// Show save status indicator
function showSaveStatus(status) {
    const subjectStatus = document.getElementById('subjectSaveStatus');
    const bodyStatus = document.getElementById('bodySaveStatus');
    
    let statusText = '';
    let statusColor = '#666';
    
    switch(status) {
        case 'typing':
            statusText = '• Änderungen erkannt...';
            statusColor = '#f39c12';
            break;
        case 'saving':
            statusText = '• Speichert...';
            statusColor = '#3498db';
            break;
        case 'saved':
            statusText = '• Gespeichert ✓';
            statusColor = '#27ae60';
            // Clear status after 2 seconds
            setTimeout(() => {
                if (subjectStatus) subjectStatus.textContent = '';
                if (bodyStatus) bodyStatus.textContent = '';
            }, 2000);
            break;
        case 'error':
            statusText = '• Fehler beim Speichern ✗';
            statusColor = '#e74c3c';
            break;
    }
    
    if (subjectStatus) {
        subjectStatus.textContent = statusText;
        subjectStatus.style.color = statusColor;
    }
    if (bodyStatus) {
        bodyStatus.textContent = statusText;
        bodyStatus.style.color = statusColor;
    }
}

// Function to load email templates from backend
async function loadEmailTemplates() {
    try {
        const response = await fetch('/api/email-templates');
        if (response.ok) {
            const templates = await response.json();
            const subjectPrompt = document.getElementById('subjectPrompt');
            const bodyPrompt = document.getElementById('bodyPrompt');
            
            if (subjectPrompt && templates.subject) {
                subjectPrompt.value = templates.subject;
            }
            if (bodyPrompt && templates.body) {
                bodyPrompt.value = templates.body;
            }
            
            console.log('Email templates loaded successfully from backend');
        } else {
            console.warn('Failed to load email templates from backend, using defaults');
        }
    } catch (error) {
        console.warn('Error loading email templates, using defaults:', error);
    }
}

// Add manual save button to the settings panel
function addManualSaveButton() {
    const settingsPanel = document.getElementById('settingsPanel');
    if (!settingsPanel || settingsPanel.querySelector('.manual-save-btn')) return;
    
    const saveButton = document.createElement('button');
    saveButton.className = 'btn btn-secondary btn-sm manual-save-btn';
    saveButton.innerHTML = '<i class="fas fa-save"></i> Manuell speichern';
    saveButton.style.cssText = 'margin-top: 10px; width: 100%;';
    saveButton.type = 'button';
    
    saveButton.addEventListener('click', () => {
        showSaveStatus('saving');
        saveEmailTemplates();
    });
    
    settingsPanel.appendChild(saveButton);
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
        showSaveStatus('saving');
        
        const response = await fetch('/api/email-templates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(templates)
        });
        
        if (response.ok) {
            const result = await response.json();
            showSaveStatus('saved');
            // Show subtle success feedback with reduced frequency
            console.log('Email templates saved successfully');
        } else {
            const error = await response.json();
            console.error('Failed to save email templates:', error);
            showSaveStatus('error');
            showToast('Speichern der Email-Vorlagen fehlgeschlagen', 'error');
        }
    } catch (error) {
        console.error('Error saving email templates:', error);
        showSaveStatus('error');
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

// Prompt Settings functionality
let currentSystemPrompts = null;

// Emergency restart function
async function emergencyRestart() {
    const confirmed = confirm(
        "⚠️ WARNUNG: Server Neustart\n\n" +
        "Dies wird den Server sofort neu starten und alle laufenden Prozesse beenden.\n\n" +
        "Sind Sie sicher, dass Sie fortfahren möchten?"
    );
    
    if (!confirmed) {
        return;
    }
    
    try {
        showToast('Server wird neu gestartet...', 'warning');
        
        // Send restart request
        const response = await fetch('/emergency-restart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // The server will restart before we get a response, but handle it gracefully
        if (response.ok) {
            showToast('Neustart eingeleitet...', 'info');
        }
        
    } catch (error) {
        // Expected - connection will be lost when server restarts
        showToast('Server wird neu gestartet...', 'info');
        
        // Attempt to reload page after a short delay
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    }
}

// Legacy prompt settings initialization - replaced by Email Workspace
function initializePromptSettings() {
    console.log('Legacy prompt settings - now handled by Email Workspace');
    // Initialize product management (still needed for backwards compatibility)
    initializeProductManagement();
}

// Load system prompts from backend
async function loadSystemPrompts() {
    console.log('Loading system prompts...');
    try {
        const response = await fetch('/api/system-prompts');
        console.log('Response status:', response.status);
        
        if (response.ok) {
            currentSystemPrompts = await response.json();
            console.log('Loaded system prompts:', currentSystemPrompts);
        } else {
            const errorText = await response.text();
            console.error('Failed to load system prompts:', errorText);
            showToast('Fehler beim Laden der Prompt-Einstellungen', 'error');
        }
    } catch (error) {
        console.error('Error loading system prompts:', error);
        showToast('Fehler beim Laden der Prompt-Einstellungen', 'error');
    }
}

// Product selector removed - now using binary radio button choice

// Update prompt fields based on selection
function updatePromptFields() {
    if (!currentSystemPrompts) return;
    
    const selectedMode = document.querySelector('input[name="promptMode"]:checked');
    const hasProduct = selectedMode ? selectedMode.value === 'with_product' : false;
    const promptType = document.getElementById('promptTypeSelect').value;
    
    const key = hasProduct ? 'with_product' : 'without_product';
    
    // Update system message
    const systemMessage = document.getElementById('systemMessage');
    if (systemMessage) {
        systemMessage.value = currentSystemPrompts[key][promptType] || '';
    }
    
    // Update user template - now uses the same key structure as system prompts
    const userTemplate = document.getElementById('userTemplate');
    if (userTemplate && currentSystemPrompts.user_templates) {
        userTemplate.value = currentSystemPrompts.user_templates[key][promptType] || '';
    }
}

// Update variables list based on product selection
function updateVariablesList() {
    const variablesList = document.getElementById('variablesList');
    if (!variablesList) return;
    
    const selectedMode = document.querySelector('input[name="promptMode"]:checked');
    const hasProduct = selectedMode ? selectedMode.value === 'with_product' : false;
    const promptType = document.getElementById('promptTypeSelect').value;
    
    // Clear existing variables
    variablesList.innerHTML = '';
    
    // Define variables based on product selection with their internal names
    const variableDefinitions = hasProduct ? [
        { name: 'Benutzername', value: '@{username}', key: 'username' },
        { name: 'Vollständiger Name', value: '{full_name}', key: 'full_name' },
        { name: 'Bio', value: '{bio}', key: 'bio' },
        { name: 'Hashtag', value: '{hashtag}', key: 'hashtag' },
        { name: 'Beitragstext', value: '{caption}', key: 'caption' },
        { name: 'Beitragsdatum', value: '{beitragsdatum}', key: 'beitragsdatum' },
        { name: 'Ausgewähltes Produkt', value: '{product_name}', key: 'product_name' },
        { name: 'Produkt-URL', value: '{product_url}', key: 'product_url' },
        { name: 'Beschreibung', value: '{product_description}', key: 'product_description' }
    ] : [
        { name: 'Benutzername', value: '@{username}', key: 'username' },
        { name: 'Vollständiger Name', value: '{full_name}', key: 'full_name' },
        { name: 'Bio', value: '{bio}', key: 'bio' },
        { name: 'Hashtag', value: '{hashtag}', key: 'hashtag' },
        { name: 'Beitragstext', value: '{caption}', key: 'caption' },
        { name: 'Beitragsdatum', value: '{beitragsdatum}', key: 'beitragsdatum' }
    ];
    
    // Get current variable settings from loaded prompts
    const modeKey = hasProduct ? 'with_product' : 'without_product';
    const currentVariableSettings = currentSystemPrompts?.variable_settings?.[modeKey]?.[promptType] || {};
    
    // Create checkboxes for each variable
    variableDefinitions.forEach(variable => {
        const isEnabled = currentVariableSettings[variable.key] !== undefined ? currentVariableSettings[variable.key] : true;
        
        const div = document.createElement('div');
        div.className = 'form-check mb-2';
        div.innerHTML = `
            <input class="form-check-input variable-checkbox" type="checkbox" id="var_${variable.key}" data-variable="${variable.key}" ${isEnabled ? 'checked' : ''}>
            <label class="form-check-label" for="var_${variable.key}" style="margin-left: 8px; font-weight: 500;">
                ${variable.name} <small class="text-muted">${variable.value}</small>
            </label>
        `;
        variablesList.appendChild(div);
    });
}

// Save system prompts
async function saveSystemPrompts() {
    const selectedMode = document.querySelector('input[name="promptMode"]:checked');
    const hasProduct = selectedMode ? selectedMode.value === 'with_product' : false;
    const promptType = document.getElementById('promptTypeSelect').value;
    const systemMessage = document.getElementById('systemMessage').value;
    const userTemplate = document.getElementById('userTemplate').value;
    
    // Collect variable settings from checkboxes
    const variableSettings = {};
    const checkboxes = document.querySelectorAll('.variable-checkbox');
    checkboxes.forEach(checkbox => {
        const variableName = checkbox.dataset.variable;
        variableSettings[variableName] = checkbox.checked;
    });
    
    const data = {
        prompt_type: promptType,
        has_product: hasProduct,
        system_message: systemMessage,
        user_template: userTemplate,
        variable_settings: variableSettings
    };
    
    try {
        const response = await fetch('/api/system-prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast('Prompt-Einstellungen erfolgreich gespeichert', 'success');
            
            // Add visual feedback to the save button
            const saveBtn = document.getElementById('savePromptSettings');
            const originalText = saveBtn.textContent;
            const originalBgColor = saveBtn.style.backgroundColor;
            saveBtn.textContent = 'Gespeichert!';
            saveBtn.style.backgroundColor = 'var(--color-success)';
            
            // Reset button after 2 seconds
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.style.backgroundColor = originalBgColor;
            }, 2000);
            
            await loadSystemPrompts(); // Reload prompts
            // Keep modal open - don't close it automatically
        } else {
            const error = await response.json();
            console.error('Failed to save system prompts:', error);
            showToast('Fehler beim Speichern der Prompt-Einstellungen', 'error');
        }
    } catch (error) {
        console.error('Error saving system prompts:', error);
        showToast('Fehler beim Speichern der Prompt-Einstellungen', 'error');
    }
}

// Product management functionality removed

// Modal utility functions
function closeModal(modalId) {
    console.log('Closing modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        
        // Special cleanup for editModal
        if (modalId === 'editModal') {
            editingUsername = null;
            editingField = null;
        }
        
        // Allow transition to complete before hiding
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

// Add initialization to DOMContentLoaded (this was already called above)
// Just ensure the prompt settings initialization is included

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

// ===============================
// COLUMN RESIZING FUNCTIONALITY
// ===============================

let isResizing = false;
let currentResizeColumn = null;
let startX = 0;
let startWidth = 0;
let previewLine = null;

// Initialize column resizing functionality
function initializeColumnResizing() {
    const table = document.querySelector('.data-table');
    if (!table) return;

    // Create preview line only if it doesn't exist
    if (!previewLine) {
        previewLine = document.createElement('div');
        previewLine.className = 'resize-preview-line';
        document.body.appendChild(previewLine);
    }

    // Add event listeners to resize handles (only new ones)
    const resizeHandles = table.querySelectorAll('.resize-handle:not(.initialized)');
    resizeHandles.forEach(handle => {
        handle.addEventListener('mousedown', startResize);
        handle.classList.add('initialized'); // Mark as initialized
    });

    // Global mouse events (only add once)
    if (!window.columnResizeInitialized) {
        document.addEventListener('mousemove', doResize);
        document.addEventListener('mouseup', endResize);
        window.columnResizeInitialized = true;
    }

    // Load saved column widths
    loadColumnWidths();
}

// Start resizing a column
function startResize(e) {
    e.preventDefault();
    e.stopPropagation();

    isResizing = true;
    currentResizeColumn = parseInt(e.target.dataset.column);
    startX = e.clientX;
    
    // Get current width of the column
    const columnWidth = getComputedStyle(document.documentElement).getPropertyValue(`--col-width-${currentResizeColumn}`);
    startWidth = parseInt(columnWidth);

    // Add resizing class to handle
    e.target.classList.add('resizing');
    
    // Disable text selection during resize
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';

    // Show preview line
    updatePreviewLine(e.clientX);
    previewLine.style.display = 'block';
}

// Handle resizing
function doResize(e) {
    if (!isResizing || !currentResizeColumn) return;

    e.preventDefault();
    
    // Update preview line position
    updatePreviewLine(e.clientX);
}

// Update preview line position
function updatePreviewLine(clientX) {
    if (!previewLine) return;
    
    const tableWrapper = document.querySelector('.table-wrapper');
    if (!tableWrapper) return;
    
    const rect = tableWrapper.getBoundingClientRect();
    const relativeX = clientX - rect.left + tableWrapper.scrollLeft;
    
    previewLine.style.left = `${rect.left + relativeX}px`;
    previewLine.style.top = `${rect.top}px`;
    previewLine.style.height = `${rect.height}px`;
}

// End resizing
function endResize(e) {
    if (!isResizing || !currentResizeColumn) return;

    const deltaX = e.clientX - startX;
    const newWidth = Math.max(50, startWidth + deltaX); // Minimum width of 50px

    // Update CSS variable
    document.documentElement.style.setProperty(`--col-width-${currentResizeColumn}`, `${newWidth}px`);

    // Save to localStorage
    saveColumnWidths();

    // Clean up
    const resizeHandle = document.querySelector(`.resize-handle[data-column="${currentResizeColumn}"]`);
    if (resizeHandle) {
        resizeHandle.classList.remove('resizing');
    }

    isResizing = false;
    currentResizeColumn = null;
    document.body.style.userSelect = '';
    document.body.style.cursor = '';
    
    // Hide preview line
    if (previewLine) {
        previewLine.style.display = 'none';
    }
}

// Save column widths to localStorage
function saveColumnWidths() {
    const columnWidths = {};
    
    for (let i = 1; i <= 12; i++) {
        const width = getComputedStyle(document.documentElement).getPropertyValue(`--col-width-${i}`);
        if (width) {
            columnWidths[i] = width.trim();
        }
    }
    
    localStorage.setItem('klinfluence-column-widths', JSON.stringify(columnWidths));
}

// Load column widths from localStorage
function loadColumnWidths() {
    try {
        const saved = localStorage.getItem('klinfluence-column-widths');
        if (saved) {
            const columnWidths = JSON.parse(saved);
            
            Object.entries(columnWidths).forEach(([column, width]) => {
                document.documentElement.style.setProperty(`--col-width-${column}`, width);
            });
        }
    } catch (error) {
        console.warn('Error loading column widths:', error);
    }
}

// Reset column widths to defaults
function resetColumnWidths() {
    // Reset CSS variables to default values
    const defaultWidths = {
        1: '60px',
        2: '150px',
        3: '120px',
        4: '180px',
        5: '100px',
        6: '200px',
        7: '180px',
        8: '150px',
        9: '250px',
        10: '300px',
        11: '120px',
        12: '120px'
    };
    
    Object.entries(defaultWidths).forEach(([column, width]) => {
        document.documentElement.style.setProperty(`--col-width-${column}`, width);
    });
    
    // Save to localStorage
    saveColumnWidths();
    
    showToast('Spaltenbreiten zurückgesetzt', 'success');
}

// Add reset button to the action bar (call this when the table is displayed)
function addColumnWidthResetButton() {
    const actionBar = document.querySelector('.d-flex.justify-content-between.align-items-center.mb-4');
    if (!actionBar) return;
    
    const rightButtonGroup = actionBar.querySelector('.d-flex.gap-2');
    if (!rightButtonGroup) return;
    
    // Check if button already exists
    if (rightButtonGroup.querySelector('#resetColumnsBtn')) return;
    
    const resetButton = document.createElement('button');
    resetButton.type = 'button';
    resetButton.className = 'btn btn-tertiary btn-sm';
    resetButton.id = 'resetColumnsBtn';
    resetButton.onclick = resetColumnWidths;
    resetButton.innerHTML = '<i class="fas fa-columns"></i> Spalten zurücksetzen';
    resetButton.title = 'Spaltenbreiten auf Standardwerte zurücksetzen';
    
    rightButtonGroup.appendChild(resetButton);
}

// ========== PRODUCT MANAGEMENT FUNCTIONS ==========

// Legacy product management initialization - replaced by Email Workspace
function initializeProductManagement() {
    console.log('Legacy product management - now handled by Email Workspace');
    const productSelector = document.getElementById('productSelector');
    const saveProductBtn = document.getElementById('saveProduct');
    
    if (productSelector) {
        productSelector.addEventListener('change', async (e) => {
            const productId = e.target.value;
            if (productId) {
                await loadProductData(productId);
            } else {
                clearProductForm();
            }
        });
    }
    
    if (saveProductBtn) {
        saveProductBtn.addEventListener('click', saveProduct);
    }
}

// Open product modal
function openProductModal() {
    populateProductSelector();
    clearProductForm();
    
    const modal = document.getElementById('productEditModal');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('show');
    }
}

// Populate product selector dropdown
function populateProductSelector() {
    const selector = document.getElementById('productSelector');
    if (!selector) return;
    
    // Clear existing options
    selector.innerHTML = '<option value="">-- Neues Produkt erstellen --</option>';
    
    // Add existing products
    if (window.productsData) {
        window.productsData.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.name;
            selector.appendChild(option);
        });
    }
}

// Load product data for editing
async function loadProductData(productId) {
    const product = window.productsData.find(p => p.id == productId);
    if (!product) return;
    
    document.getElementById('productEditId').value = product.id;
    document.getElementById('productName').value = product.name || '';
    document.getElementById('productUrl').value = product.url || '';
    document.getElementById('productImageUrl').value = product.image_url || '';
    document.getElementById('productDescription').value = product.description || '';
    document.getElementById('productPrice').value = product.price || '';
    
    // Show/hide delete button
    showDeleteButton(product.id);
}

// Clear product form
function clearProductForm() {
    document.getElementById('productEditId').value = '';
    document.getElementById('productName').value = '';
    document.getElementById('productUrl').value = '';
    document.getElementById('productImageUrl').value = '';
    document.getElementById('productDescription').value = '';
    document.getElementById('productPrice').value = '';
    
    // Hide delete button for new products
    hideDeleteButton();
}

// Save product (create or update)
async function saveProduct() {
    const productId = document.getElementById('productEditId').value;
    const productName = document.getElementById('productName').value.trim();
    const productUrl = document.getElementById('productUrl').value.trim();
    const productImageUrl = document.getElementById('productImageUrl').value.trim();
    const productDescription = document.getElementById('productDescription').value.trim();
    const productPrice = document.getElementById('productPrice').value.trim();
    
    // Validation
    if (!productName || !productUrl) {
        showToast('Bitte geben Sie mindestens einen Produktnamen und eine URL ein', 'error');
        return;
    }
    
    const productData = {
        name: productName,
        url: productUrl,
        image_url: productImageUrl,
        description: productDescription,
        price: productPrice
    };
    
    if (productId) {
        productData.id = productId;
    }
    
    try {
        const response = await fetch('/api/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(productData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Produkt erfolgreich gespeichert', 'success');
            
            // Reload products data
            await loadProducts();
            
            // Update all product selectors
            populateProductSelectors();
            populateProductSelector();
            
            // Clear form and close modal
            clearProductForm();
            closeModal('productEditModal');
        } else {
            const error = await response.json();
            if (error.error && error.error.includes('UNIQUE constraint failed')) {
                showToast('Ein Produkt mit diesem Namen existiert bereits', 'error');
            } else {
                showToast('Fehler beim Speichern des Produkts', 'error');
            }
        }
    } catch (error) {
        console.error('Error saving product:', error);
        showToast('Fehler beim Speichern des Produkts', 'error');
    }
}

// Delete product
async function deleteProduct() {
    const productId = document.getElementById('productEditId').value;
    if (!productId) return;
    
    const product = window.productsData.find(p => p.id == productId);
    if (!product) return;
    
    if (!confirm(`Möchten Sie das Produkt "${product.name}" wirklich löschen?`)) {
        return;
    }
    
    try {
        // First check if any leads use this product
        const response = await fetch(`/api/products/${productId}/check-usage`);
        if (response.ok) {
            const result = await response.json();
            if (result.in_use) {
                showToast(`Dieses Produkt kann nicht gelöscht werden, da es von ${result.lead_count} Lead(s) verwendet wird`, 'error');
                return;
            }
        }
        
        // If not in use, proceed with deletion
        const deleteResponse = await fetch(`/api/products/${productId}`, {
            method: 'DELETE'
        });
        
        if (deleteResponse.ok) {
            showToast('Produkt erfolgreich gelöscht', 'success');
            
            // Reload products data
            await loadProducts();
            
            // Update all product selectors
            populateProductSelectors();
            populateProductSelector();
            
            // Clear form and close modal
            clearProductForm();
            closeModal('productEditModal');
        } else {
            showToast('Fehler beim Löschen des Produkts', 'error');
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        showToast('Fehler beim Löschen des Produkts', 'error');
    }
}

// Show delete button
function showDeleteButton(productId) {
    const modalFooter = document.querySelector('#productEditModal .modal-footer');
    let deleteBtn = document.getElementById('deleteProductBtn');
    
    if (!deleteBtn) {
        deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-danger';
        deleteBtn.id = 'deleteProductBtn';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Löschen';
        deleteBtn.onclick = deleteProduct;
        
        // Insert before the cancel button
        const cancelBtn = modalFooter.querySelector('.btn-secondary');
        modalFooter.insertBefore(deleteBtn, cancelBtn);
    }
    
    deleteBtn.style.display = 'inline-block';
}

// Hide delete button
function hideDeleteButton() {
    const deleteBtn = document.getElementById('deleteProductBtn');
    if (deleteBtn) {
        deleteBtn.style.display = 'none';
    }
}

// Pagination Functions
function initializePagination() {
    // Load saved page size from localStorage
    const savedPageSize = localStorage.getItem('pageSize');
    if (savedPageSize && savedPageSize !== 'null') {
        pageSize = savedPageSize === 'all' ? 'all' : parseInt(savedPageSize);
        const pageSizeSelect = document.getElementById('pageSizeSelect');
        const pageSizeSelectBottom = document.getElementById('pageSizeSelectBottom');
        if (pageSizeSelect) {
            pageSizeSelect.value = savedPageSize;
        }
        if (pageSizeSelectBottom) {
            pageSizeSelectBottom.value = savedPageSize;
        }
    }
    
    // Set up page size selectors (both top and bottom)
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    const pageSizeSelectBottom = document.getElementById('pageSizeSelectBottom');
    
    const handlePageSizeChange = function() {
        const newPageSize = this.value;
        pageSize = newPageSize === 'all' ? 'all' : parseInt(newPageSize);
        localStorage.setItem('pageSize', newPageSize);
        currentPage = 1;
        
        // Sync both selectors
        if (pageSizeSelect) pageSizeSelect.value = newPageSize;
        if (pageSizeSelectBottom) pageSizeSelectBottom.value = newPageSize;
        
        updatePagination();
    };
    
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', handlePageSizeChange);
    }
    if (pageSizeSelectBottom) {
        pageSizeSelectBottom.addEventListener('change', handlePageSizeChange);
    }
    
    // Set up navigation buttons (top controls)
    document.getElementById('firstPageBtn')?.addEventListener('click', () => goToPage(1));
    document.getElementById('prevPageBtn')?.addEventListener('click', () => goToPage(currentPage - 1));
    document.getElementById('nextPageBtn')?.addEventListener('click', () => goToPage(currentPage + 1));
    document.getElementById('lastPageBtn')?.addEventListener('click', () => {
        const totalPages = getTotalPages();
        goToPage(totalPages);
    });
    
    // Set up navigation buttons (bottom controls)
    document.getElementById('firstPageBtnBottom')?.addEventListener('click', () => goToPage(1));
    document.getElementById('prevPageBtnBottom')?.addEventListener('click', () => goToPage(currentPage - 1));
    document.getElementById('nextPageBtnBottom')?.addEventListener('click', () => goToPage(currentPage + 1));
    document.getElementById('lastPageBtnBottom')?.addEventListener('click', () => {
        const totalPages = getTotalPages();
        goToPage(totalPages);
    });
}

function getTotalPages() {
    if (pageSize === 'all') return 1;
    return Math.ceil(filteredRows.length / pageSize);
}

function updatePagination() {
    const totalPages = getTotalPages();
    const showPagination = filteredRows.length > 0 && pageSize !== 'all' && totalPages > 1;
    
    // Show/hide pagination controls
    const paginationTop = document.getElementById('paginationControlsTop');
    const paginationBottom = document.getElementById('paginationControlsBottom');
    
    if (showPagination) {
        if (paginationTop) paginationTop.style.display = 'flex';
        if (paginationBottom) paginationBottom.style.display = 'flex';
    } else {
        if (paginationTop) paginationTop.style.display = 'none';
        if (paginationBottom) paginationBottom.style.display = 'none';
    }
    
    if (!showPagination) return;
    
    // Update results info (both top and bottom)
    const startResult = ((currentPage - 1) * pageSize) + 1;
    const endResult = Math.min(currentPage * pageSize, filteredRows.length);
    const resultsInfo = document.getElementById('resultsInfo');
    const resultsInfoBottom = document.getElementById('resultsInfoBottom');
    const infoText = `Zeige ${startResult}-${endResult} von ${filteredRows.length} Ergebnissen`;
    
    if (resultsInfo) resultsInfo.textContent = infoText;
    if (resultsInfoBottom) resultsInfoBottom.textContent = infoText;
    
    // Update page info (both top and bottom)
    const pageInfo = document.getElementById('pageInfo');
    const pageInfoBottom = document.getElementById('pageInfoBottom');
    const pageText = `Seite ${currentPage} von ${totalPages}`;
    
    if (pageInfo) pageInfo.textContent = pageText;
    if (pageInfoBottom) pageInfoBottom.textContent = pageText;
    
    // Update navigation buttons (top)
    const firstBtn = document.getElementById('firstPageBtn');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const lastBtn = document.getElementById('lastPageBtn');
    
    if (firstBtn) firstBtn.disabled = currentPage === 1;
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    if (lastBtn) lastBtn.disabled = currentPage >= totalPages;
    
    // Update navigation buttons (bottom)
    const firstBtnBottom = document.getElementById('firstPageBtnBottom');
    const prevBtnBottom = document.getElementById('prevPageBtnBottom');
    const nextBtnBottom = document.getElementById('nextPageBtnBottom');
    const lastBtnBottom = document.getElementById('lastPageBtnBottom');
    
    if (firstBtnBottom) firstBtnBottom.disabled = currentPage === 1;
    if (prevBtnBottom) prevBtnBottom.disabled = currentPage === 1;
    if (nextBtnBottom) nextBtnBottom.disabled = currentPage >= totalPages;
    if (lastBtnBottom) lastBtnBottom.disabled = currentPage >= totalPages;
    
    // Update page numbers (both top and bottom)
    updatePageNumbers();
    
    // Show only current page rows
    showCurrentPageRows();
}

function updatePageNumbers() {
    const pageNumbers = document.getElementById('pageNumbers');
    const pageNumbersBottom = document.getElementById('pageNumbersBottom');
    
    const totalPages = getTotalPages();
    
    // Update top page numbers
    if (pageNumbers) {
        pageNumbers.innerHTML = '';
        createPageNumbersForContainer(pageNumbers, totalPages);
    }
    
    // Update bottom page numbers
    if (pageNumbersBottom) {
        pageNumbersBottom.innerHTML = '';
        createPageNumbersForContainer(pageNumbersBottom, totalPages);
    }
}

function createPageNumbersForContainer(container, totalPages) {
    if (totalPages <= 7) {
        // Show all page numbers if 7 or fewer pages
        for (let i = 1; i <= totalPages; i++) {
            createPageButton(i, container);
        }
    } else {
        // Smart pagination with ellipsis
        createPageButton(1, container);
        
        if (currentPage > 4) {
            createEllipsis(container);
        }
        
        const startPage = Math.max(2, currentPage - 2);
        const endPage = Math.min(totalPages - 1, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            createPageButton(i, container);
        }
        
        if (currentPage < totalPages - 3) {
            createEllipsis(container);
        }
        
        if (totalPages > 1) {
            createPageButton(totalPages, container);
        }
    }
}

function createPageButton(pageNum, container) {
    const button = document.createElement('button');
    button.className = `btn btn-sm${pageNum === currentPage ? ' active' : ''}`;
    button.textContent = pageNum;
    button.addEventListener('click', () => goToPage(pageNum));
    container.appendChild(button);
}

function createEllipsis(container) {
    const ellipsis = document.createElement('span');
    ellipsis.className = 'page-ellipsis';
    ellipsis.textContent = '...';
    container.appendChild(ellipsis);
}

function goToPage(page) {
    const totalPages = getTotalPages();
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    updatePagination();
}

function showCurrentPageRows() {
    const tbody = document.getElementById('resultsBody');
    if (!tbody) return;
    
    // Hide all rows first
    const allTableRows = tbody.querySelectorAll('tr');
    allTableRows.forEach(row => row.style.display = 'none');
    
    if (pageSize === 'all') {
        // Show all filtered rows
        filteredRows.forEach(row => row.style.display = '');
    } else {
        // Show only current page rows
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const currentPageRows = filteredRows.slice(startIndex, endIndex);
        
        currentPageRows.forEach(row => row.style.display = '');
    }
}