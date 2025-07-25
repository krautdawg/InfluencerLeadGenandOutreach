// Filter Bar JavaScript for K+L Influence App

// Filter state management
let activeFilters = {
    datum: null,
    follower: null,
    typ: 'personal', // Default to personal
    hashtag: [],
    produkt: [],
    status: []
};

// Initialize filter bar
function initializeFilterBar() {
    // Create filter bar HTML
    const filterBarHTML = createFilterBarHTML();
    
    // Insert filter bar before results section
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        const filterBarContainer = document.createElement('div');
        filterBarContainer.innerHTML = filterBarHTML;
        resultsSection.parentNode.insertBefore(filterBarContainer.firstChild, resultsSection);
        
        // Initialize filter event listeners
        initializeFilterEventListeners();
        
        // Set default type filter
        updateTypeToggle('personal');
    }
}

// Create filter bar HTML
function createFilterBarHTML() {
    return `
        <div class="filter-bar-container">
            <!-- Filter Chips Display -->
            <div class="filter-chips-display" id="filterChipsDisplay"></div>
            
            <!-- Filter Controls -->
            <div class="filter-controls">
                <!-- Date Filter -->
                <div class="filter-control">
                    <label>Datum</label>
                    <div class="date-preset-buttons">
                        <button class="date-preset-btn" data-date="week">Letzte Woche</button>
                        <button class="date-preset-btn" data-date="month">Letzten Monat</button>
                        <button class="date-preset-btn" data-date="year">Dieses Jahr</button>
                        <button class="date-preset-btn" data-date="older">Älter als...</button>
                    </div>
                    <input type="date" class="filter-dropdown" id="customDateStart" style="display: none;">
                    <input type="date" class="filter-dropdown" id="customDateEnd" style="display: none;">
                </div>
                
                <!-- Follower Filter -->
                <div class="filter-control">
                    <label>Follower</label>
                    <select class="filter-dropdown" id="followerFilter">
                        <option value="">Alle Follower</option>
                        <option value="1-100">1 - 100</option>
                        <option value="100-1000">100 - 1K</option>
                        <option value="1000-10000">1K - 10K</option>
                        <option value="10000-50000">10K - 50K</option>
                        <option value="50000-100000">50K - 100K</option>
                        <option value="100000-500000">100K - 500K</option>
                        <option value="500000-1000000">500K - 1M</option>
                        <option value="1000000-999999999">1M+</option>
                    </select>
                </div>
                
                <!-- Type Toggle -->
                <div class="filter-control">
                    <label>Typ</label>
                    <div class="type-toggle">
                        <button class="type-toggle-btn" data-type="personal">Personal</button>
                        <button class="type-toggle-btn" data-type="business">Business</button>
                    </div>
                </div>
                
                <!-- Hashtag Multi-Select -->
                <div class="filter-control">
                    <label>Hashtag</label>
                    <select class="filter-dropdown" id="hashtagFilter" multiple>
                        <!-- Options will be populated dynamically -->
                    </select>
                </div>
                
                <!-- Product Multi-Select -->
                <div class="filter-control">
                    <label>Produkt</label>
                    <select class="filter-dropdown" id="produktFilter" multiple>
                        <!-- Options will be populated from products data -->
                    </select>
                </div>
                
                <!-- Status Multi-Select -->
                <div class="filter-control">
                    <label>Status</label>
                    <select class="filter-dropdown" id="statusFilter" multiple>
                        <option value="draft">Entwurf</option>
                        <option value="sent">Gesendet</option>
                    </select>
                </div>
                
                <!-- Clear Filters Button -->
                <button class="clear-filters-btn" onclick="clearAllFilters()">
                    <i class="fas fa-times"></i> Filter löschen
                </button>
            </div>
        </div>
    `;
}

// Initialize filter event listeners
function initializeFilterEventListeners() {
    // Date preset buttons
    document.querySelectorAll('.date-preset-btn').forEach(btn => {
        btn.addEventListener('click', handleDatePreset);
    });
    
    // Follower filter
    document.getElementById('followerFilter').addEventListener('change', handleFollowerFilter);
    
    // Type toggle buttons
    document.querySelectorAll('.type-toggle-btn').forEach(btn => {
        btn.addEventListener('click', handleTypeToggle);
    });
    
    // Multi-select filters
    ['hashtagFilter', 'produktFilter', 'statusFilter'].forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', handleMultiSelectFilter);
        }
    });
    
    // Populate dynamic options
    populateFilterOptions();
}

// Handle date preset clicks
function handleDatePreset(e) {
    const preset = e.target.dataset.date;
    const now = new Date();
    let startDate = new Date();
    
    // Remove active class from all date buttons
    document.querySelectorAll('.date-preset-btn').forEach(btn => btn.classList.remove('active'));
    
    switch(preset) {
        case 'week':
            startDate.setDate(now.getDate() - 7);
            break;
        case 'month':
            startDate.setMonth(now.getMonth() - 1);
            break;
        case 'year':
            startDate.setFullYear(now.getFullYear() - 1);
            break;
        case 'older':
            // Show custom date inputs
            document.getElementById('customDateStart').style.display = 'inline-block';
            document.getElementById('customDateEnd').style.display = 'inline-block';
            return;
    }
    
    // Hide custom date inputs
    document.getElementById('customDateStart').style.display = 'none';
    document.getElementById('customDateEnd').style.display = 'none';
    
    e.target.classList.add('active');
    activeFilters.datum = { preset, startDate, endDate: now };
    updateFilterChips();
    applyTableFilters();
}

// Handle follower filter
function handleFollowerFilter(e) {
    const value = e.target.value;
    if (value) {
        e.target.classList.add('active');
        activeFilters.follower = value;
    } else {
        e.target.classList.remove('active');
        activeFilters.follower = null;
    }
    updateFilterChips();
    applyTableFilters();
}

// Handle type toggle
function handleTypeToggle(e) {
    const type = e.target.dataset.type;
    updateTypeToggle(type);
    activeFilters.typ = type;
    updateFilterChips();
    applyTableFilters();
}

// Update type toggle UI
function updateTypeToggle(type) {
    document.querySelectorAll('.type-toggle-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        }
    });
}

// Handle multi-select filters
function handleMultiSelectFilter(e) {
    const filterId = e.target.id;
    const filterKey = filterId.replace('Filter', '');
    const selectedOptions = Array.from(e.target.selectedOptions).map(opt => opt.value);
    
    if (selectedOptions.length > 0) {
        e.target.classList.add('active');
        activeFilters[filterKey] = selectedOptions;
    } else {
        e.target.classList.remove('active');
        activeFilters[filterKey] = [];
    }
    
    updateFilterChips();
    applyTableFilters();
}

// Update filter chips display
function updateFilterChips() {
    const chipsContainer = document.getElementById('filterChipsDisplay');
    chipsContainer.innerHTML = '';
    
    // Date chip
    if (activeFilters.datum) {
        const dateText = getDateFilterText(activeFilters.datum);
        addFilterChip('Datum', dateText, () => {
            activeFilters.datum = null;
            document.querySelectorAll('.date-preset-btn').forEach(btn => btn.classList.remove('active'));
            updateFilterChips();
            applyTableFilters();
        });
    }
    
    // Follower chip
    if (activeFilters.follower) {
        addFilterChip('Follower', activeFilters.follower, () => {
            activeFilters.follower = null;
            document.getElementById('followerFilter').value = '';
            document.getElementById('followerFilter').classList.remove('active');
            updateFilterChips();
            applyTableFilters();
        });
    }
    
    // Type chip (always show since it has a default)
    addFilterChip('Typ', activeFilters.typ === 'business' ? 'Business' : 'Personal', () => {
        // Don't remove type filter, just toggle it
        activeFilters.typ = activeFilters.typ === 'business' ? 'personal' : 'business';
        updateTypeToggle(activeFilters.typ);
        updateFilterChips();
        applyTableFilters();
    });
    
    // Multi-select chips
    ['hashtag', 'produkt', 'status'].forEach(filterKey => {
        if (activeFilters[filterKey] && activeFilters[filterKey].length > 0) {
            activeFilters[filterKey].forEach(value => {
                const displayValue = filterKey === 'status' ? 
                    (value === 'sent' ? 'Gesendet' : 'Entwurf') : value;
                addFilterChip(filterKey.charAt(0).toUpperCase() + filterKey.slice(1), displayValue, () => {
                    activeFilters[filterKey] = activeFilters[filterKey].filter(v => v !== value);
                    updateMultiSelectUI(filterKey + 'Filter', activeFilters[filterKey]);
                    updateFilterChips();
                    applyTableFilters();
                });
            });
        }
    });
}

// Add individual filter chip
function addFilterChip(label, value, removeCallback) {
    const chipsContainer = document.getElementById('filterChipsDisplay');
    const chip = document.createElement('div');
    chip.className = 'filter-chip';
    chip.innerHTML = `
        <span>${label}: ${value}</span>
        <span class="remove-chip" onclick="">×</span>
    `;
    chip.querySelector('.remove-chip').onclick = removeCallback;
    chipsContainer.appendChild(chip);
}

// Get date filter text
function getDateFilterText(dateFilter) {
    const presetTexts = {
        week: 'Letzte Woche',
        month: 'Letzten Monat',
        year: 'Dieses Jahr',
        older: 'Älter als...'
    };
    return presetTexts[dateFilter.preset] || 'Benutzerdefiniert';
}

// Update multi-select UI
function updateMultiSelectUI(selectId, selectedValues) {
    const select = document.getElementById(selectId);
    if (select) {
        Array.from(select.options).forEach(option => {
            option.selected = selectedValues.includes(option.value);
        });
        select.classList.toggle('active', selectedValues.length > 0);
    }
}

// Clear all filters
function clearAllFilters() {
    activeFilters = {
        datum: null,
        follower: null,
        typ: 'personal',
        hashtag: [],
        produkt: [],
        status: []
    };
    
    // Reset UI
    document.querySelectorAll('.date-preset-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById('followerFilter').value = '';
    document.getElementById('followerFilter').classList.remove('active');
    updateTypeToggle('personal');
    ['hashtagFilter', 'produktFilter', 'statusFilter'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.selectedIndex = -1;
            element.classList.remove('active');
        }
    });
    
    updateFilterChips();
    applyTableFilters();
}

// Populate filter options from data
function populateFilterOptions() {
    // Get leads data from window
    const leadsData = window.leadsData || [];
    
    // Populate hashtags
    const hashtags = [...new Set(leadsData.map(lead => lead.hashtag).filter(h => h))];
    const hashtagSelect = document.getElementById('hashtagFilter');
    if (hashtagSelect) {
        hashtagSelect.innerHTML = hashtags.map(h => `<option value="${h}">#${h}</option>`).join('');
    }
    
    // Populate products
    if (window.productsData) {
        const produktSelect = document.getElementById('produktFilter');
        if (produktSelect) {
            produktSelect.innerHTML = window.productsData.map(p => 
                `<option value="${p.id}">${p.name}</option>`
            ).join('');
        }
    }
}

// Apply filters to table
function applyTableFilters() {
    const rows = document.querySelectorAll('#resultsBody tr');
    
    rows.forEach(row => {
        let show = true;
        
        // Date filter (Post Zeit column)
        if (activeFilters.datum) {
            const postDateCell = row.querySelector('[data-post-date]');
            if (postDateCell) {
                const postDate = new Date(postDateCell.dataset.postDate);
                if (postDate < activeFilters.datum.startDate || postDate > activeFilters.datum.endDate) {
                    show = false;
                }
            }
        }
        
        // Follower filter
        if (activeFilters.follower && show) {
            const followersCell = row.querySelector('[data-followers]');
            if (followersCell) {
                const followers = parseInt(followersCell.dataset.followers);
                const [min, max] = activeFilters.follower.split('-').map(n => parseInt(n));
                if (followers < min || followers > max) {
                    show = false;
                }
            }
        }
        
        // Type filter
        if (activeFilters.typ && show) {
            const typeCell = row.querySelector('[data-business]');
            if (typeCell) {
                const isBusiness = typeCell.dataset.business === 'true';
                if ((activeFilters.typ === 'business' && !isBusiness) || 
                    (activeFilters.typ === 'personal' && isBusiness)) {
                    show = false;
                }
            }
        }
        
        // Hashtag filter
        if (activeFilters.hashtag.length > 0 && show) {
            const hashtagCell = row.querySelector('[data-hashtag]');
            if (hashtagCell) {
                const hashtag = hashtagCell.dataset.hashtag;
                if (!activeFilters.hashtag.includes(hashtag)) {
                    show = false;
                }
            }
        }
        
        // Product filter
        if (activeFilters.produkt.length > 0 && show) {
            const productCell = row.querySelector('[data-product]');
            if (productCell) {
                const productId = productCell.dataset.product;
                if (!activeFilters.produkt.includes(productId)) {
                    show = false;
                }
            }
        }
        
        // Status filter
        if (activeFilters.status.length > 0 && show) {
            const statusCell = row.querySelector('[data-status]');
            if (statusCell) {
                const status = statusCell.dataset.status;
                if (!activeFilters.status.includes(status)) {
                    show = false;
                }
            }
        }
        
        row.style.display = show ? '' : 'none';
    });
}