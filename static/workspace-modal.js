// Workspace Modal - Email Workspace functionality
// Handles the integrated Email Workspace with Offcanvas panels

let currentWorkspaceLeadId = null;
let currentWorkspaceUsername = null;

// Initialize workspace modal functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeWorkspaceModal();
});

// Track panel states
let panelStates = {
    left: false,
    right: false
};

// Custom modal functions
window.showEmailWorkspace = function() {
    const modal = document.getElementById('emailWorkspaceModal');
    if (modal) {
        modal.classList.add('custom-show');
    }
};

window.hideEmailWorkspace = function() {
    const modal = document.getElementById('emailWorkspaceModal');
    if (modal) {
        modal.classList.remove('custom-show');
        modal.classList.remove('left-panel-open', 'right-panel-open', 'both-panels-open');
        // Reset panel states when modal closes
        panelStates.left = false;
        panelStates.right = false;
    }
};

// Update modal width based on panel states
function updateModalWidth() {
    const modal = document.getElementById('emailWorkspaceModal');
    if (!modal) return;
    
    // Remove all width classes first
    modal.classList.remove('left-panel-open', 'right-panel-open', 'both-panels-open');
    
    // Apply appropriate class based on panel states
    if (panelStates.left && panelStates.right) {
        modal.classList.add('both-panels-open');
    } else if (panelStates.left) {
        modal.classList.add('left-panel-open');
    } else if (panelStates.right) {
        modal.classList.add('right-panel-open');
    }
}

function initializeWorkspaceModal() {
    const workspaceModal = document.getElementById('emailWorkspaceModal');
    if (!workspaceModal) {
        console.error('Email Workspace Modal not found');
        return;
    }
    
    // Initialize character counters
    initializeCharacterCounters();
    
    // Initialize event listeners for workspace elements
    initializeWorkspaceEventListeners();
    
    // Initialize offcanvas event listeners
    initializeOffcanvasEventListeners();
}

// Open Email Workspace with lead data
window.openEmailWorkspace = async function(leadId, username) {
    if (!leadId || !username) {
        console.error('Lead ID or username not provided');
        showToast('Fehler: Lead-Daten nicht gefunden', 'error');
        return;
    }
    
    currentWorkspaceLeadId = leadId;
    currentWorkspaceUsername = username;
    
    // Show the modal using custom function
    showEmailWorkspace();
    
    // Show loading state
    document.getElementById('workspaceLeadName').textContent = 'Lade...';
    document.getElementById('workspaceLeadFullName').textContent = 'Lade...';
    document.getElementById('workspaceLeadInfo').textContent = 'Lade...';
    document.getElementById('workspaceLeadHashtag').textContent = 'Lade...';
    
    try {
        await loadWorkspaceData(leadId);
    } catch (error) {
        console.error('Error loading workspace data:', error);
        showToast('Fehler beim Laden der Workspace-Daten', 'error');
    }
};

// Load all workspace data with single API call
async function loadWorkspaceData(leadId) {
    try {
        const response = await fetch(`/api/workspace-data/${leadId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Populate main modal
        populateMainModal(data.lead);
        
        // Populate product selection
        populateProductSelection(data.products, data.lead.selectedProductId);
        
        // Populate offcanvas panels
        populatePromptOffcanvas(data.promptSettings);
        populateProductOffcanvas(data.products, data.lead.selectedProductId);
        
    } catch (error) {
        console.error('Failed to load workspace data:', error);
        showToast('Fehler beim Laden der Daten', 'error');
    }
}

// Populate main modal with lead data
function populateMainModal(lead) {
    // Hidden fields
    document.getElementById('workspaceLeadId').value = lead.id;
    document.getElementById('workspaceUsername').value = lead.username;
    
    // Header and lead info
    document.getElementById('workspaceLeadName').textContent = lead.full_name || lead.username;
    document.getElementById('workspaceLeadFullName').textContent = lead.full_name || lead.username;
    document.getElementById('workspaceLeadInfo').textContent = `@${lead.username} • ${lead.followers_count} Follower`;
    document.getElementById('workspaceLeadHashtag').textContent = `#${lead.hashtag}`;
    
    // Email fields
    document.getElementById('workspaceEmailSubject').value = lead.subject || '';
    document.getElementById('workspaceEmailContent').value = lead.email_body || '';
    
    // Update character counters
    updateCharacterCount('workspaceEmailSubject', 'workspaceSubjectCharCount', 100);
    updateCharacterCount('workspaceEmailContent', 'workspaceContentCharCount');
}

// Populate product selection dropdown
function populateProductSelection(products, selectedProductId) {
    const select = document.getElementById('workspaceProductSelect');
    select.innerHTML = '<option value="">Kein Produkt</option>';
    
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = product.name;
        if (product.id == selectedProductId) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

// Populate prompt offcanvas with current settings
function populatePromptOffcanvas(promptSettings) {
    if (!promptSettings) return;
    
    // Set default mode to without_product
    const withoutProductRadio = document.getElementById('offcanvasPromptModeWithoutProduct');
    const withProductRadio = document.getElementById('offcanvasPromptModeWithProduct');
    
    withoutProductRadio.checked = true;
    withProductRadio.checked = false;
    
    // Set default type to subject
    document.getElementById('offcanvasPromptTypeSelect').value = 'subject';
    
    // Load current settings for without_product + subject
    loadPromptSettingsForType('without_product', 'subject', promptSettings);
}

// Load specific prompt settings based on mode and type
function loadPromptSettingsForType(mode, type, promptSettings) {
    const systemMessage = promptSettings[mode]?.[type] || '';
    const userTemplate = promptSettings.user_templates?.[mode]?.[type] || '';
    const variableSettings = promptSettings.variable_settings?.[mode]?.[type] || {};
    
    document.getElementById('offcanvasSystemMessage').value = systemMessage;
    document.getElementById('offcanvasUserTemplate').value = userTemplate;
    
    // Populate variables
    populateVariablesList(variableSettings);
    
    // Set initial product variable visibility based on current mode
    setTimeout(() => handlePromptModeVariableVisibility(), 100);
}

// Populate variables list with checkboxes
function populateVariablesList(variableSettings) {
    const container = document.getElementById('offcanvasVariablesList');
    container.innerHTML = '';
    
    // Define available variables
    const availableVariables = [
        'Vorname', 'Nachname', 'Benutzername', 'Vollständiger_Name', 'Bio',
        'Anzahl_Follower', 'E-Mail', 'Website', 'Telefonnummer', 'Produktname',
        'Produkt_URL', 'Produkt_Beschreibung', 'Produkt_Preis'
    ];
    
    availableVariables.forEach(variable => {
        const div = document.createElement('div');
        div.className = 'form-check';
        
        // Add product-specific class for conditional hiding
        const productVariables = ['Produktname', 'Produkt_URL', 'Produkt_Beschreibung', 'Produkt_Preis'];
        if (productVariables.includes(variable)) {
            div.classList.add('product-variable');
        }
        
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'form-check-input';
        input.id = `var_${variable}`;
        input.value = variable;
        input.checked = variableSettings[variable] !== undefined ? variableSettings[variable] : true; // Default all to checked
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = input.id;
        label.textContent = variable.replace(/_/g, ' ');
        
        div.appendChild(input);
        div.appendChild(label);
        container.appendChild(div);
    });
}

// Populate product offcanvas
function populateProductOffcanvas(products, selectedProductId) {
    const select = document.getElementById('offcanvasProductSelector');
    select.innerHTML = '<option value="">-- Neues Produkt erstellen --</option>';
    
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product.id;
        option.textContent = product.name;
        select.appendChild(option);
    });
    
    // Clear form fields
    clearProductForm();
}

// Clear product form fields
function clearProductForm() {
    document.getElementById('offcanvasProductEditId').value = '';
    document.getElementById('offcanvasProductName').value = '';
    document.getElementById('offcanvasProductUrl').value = '';
    document.getElementById('offcanvasProductImageUrl').value = '';
    document.getElementById('offcanvasProductDescription').value = '';
    document.getElementById('offcanvasProductPrice').value = '';
    document.getElementById('deleteProductOffcanvas').style.display = 'none';
}

// Initialize character counters
function initializeCharacterCounters() {
    const subjectInput = document.getElementById('workspaceEmailSubject');
    const contentInput = document.getElementById('workspaceEmailContent');
    
    if (subjectInput) {
        subjectInput.addEventListener('input', () => {
            updateCharacterCount('workspaceEmailSubject', 'workspaceSubjectCharCount', 100);
        });
    }
    
    if (contentInput) {
        contentInput.addEventListener('input', () => {
            updateCharacterCount('workspaceEmailContent', 'workspaceContentCharCount');
        });
    }
}

// Update character count display
function updateCharacterCount(inputId, counterId, maxLength = null) {
    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);
    
    if (!input || !counter) return;
    
    const count = input.value.length;
    
    if (maxLength) {
        counter.textContent = count;
        counter.parentElement.style.color = count > maxLength ? 'red' : '';
    } else {
        counter.textContent = count;
    }
}

// Handle product variable visibility based on product selection
function handleProductVariableVisibility() {
    const productSelect = document.getElementById('workspaceProductSelect');
    const productVariables = document.querySelectorAll('.product-variable');
    
    if (!productSelect || !productVariables.length) return;
    
    const hasProduct = productSelect.value && productSelect.value !== '';
    
    productVariables.forEach(element => {
        if (hasProduct) {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    });
}

// Handle product variable visibility based on prompt mode selection
function handlePromptModeVariableVisibility() {
    const withProductRadio = document.getElementById('offcanvasPromptModeWithProduct');
    const productVariables = document.querySelectorAll('.product-variable');
    
    if (!withProductRadio || !productVariables.length) return;
    
    const showProductVariables = withProductRadio.checked;
    
    console.log('Product variable visibility - with product checked:', showProductVariables);
    
    productVariables.forEach(element => {
        if (showProductVariables) {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    });
}

// Initialize workspace event listeners
function initializeWorkspaceEventListeners() {
    // AI Generation button
    const generateBtn = document.getElementById('workspaceGenerateEmailBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', handleWorkspaceAIGeneration);
    }
    
    // Save Draft button
    const saveDraftBtn = document.getElementById('workspaceSaveDraftBtn');
    if (saveDraftBtn) {
        saveDraftBtn.addEventListener('click', handleWorkspaceSaveDraft);
    }
    
    // Send Email button
    const sendEmailBtn = document.getElementById('workspaceSendEmailBtn');
    if (sendEmailBtn) {
        sendEmailBtn.addEventListener('click', handleWorkspaceSendEmail);
    }
    
    // Product selection change
    const productSelect = document.getElementById('workspaceProductSelect');
    if (productSelect) {
        productSelect.addEventListener('change', handleWorkspaceProductChange);
        // Also listen for changes to show/hide product variables in prompt offcanvas
        productSelect.addEventListener('change', handleProductVariableVisibility);
    }
}

// Initialize offcanvas event listeners
function initializeOffcanvasEventListeners() {
    // Prompt settings events
    const promptModeInputs = document.querySelectorAll('input[name="offcanvasPromptMode"]');
    const promptTypeSelect = document.getElementById('offcanvasPromptTypeSelect');
    const savePromptBtn = document.getElementById('savePromptOffcanvas');
    
    promptModeInputs.forEach(input => {
        input.addEventListener('change', handlePromptModeChange);
        input.addEventListener('change', handlePromptModeVariableVisibility);
    });
    
    if (promptTypeSelect) {
        promptTypeSelect.addEventListener('change', handlePromptTypeChange);
    }
    
    if (savePromptBtn) {
        savePromptBtn.addEventListener('click', handleSavePrompt);
    }
    
    // Product offcanvas events
    const productSelector = document.getElementById('offcanvasProductSelector');
    const saveProductBtn = document.getElementById('saveProductOffcanvas');
    const deleteProductBtn = document.getElementById('deleteProductOffcanvas');
    
    if (productSelector) {
        productSelector.addEventListener('change', handleProductSelectorChange);
    }
    
    if (saveProductBtn) {
        saveProductBtn.addEventListener('click', handleSaveProduct);
    }
    
    if (deleteProductBtn) {
        deleteProductBtn.addEventListener('click', handleDeleteProduct);
    }
    
    // Enable multiple offcanvas panels to be open simultaneously
    enableMultipleOffcanvas();
}

// Custom offcanvas implementation for dual panels
function enableMultipleOffcanvas() {
    // No longer needed - we use custom implementation
    console.log('Custom offcanvas system initialized');
}

// Global functions for custom offcanvas control
window.toggleCustomOffcanvas = function(offcanvasId) {
    const offcanvas = document.getElementById(offcanvasId);
    if (!offcanvas) return;
    
    if (offcanvas.classList.contains('custom-show')) {
        hideCustomOffcanvas(offcanvasId);
    } else {
        showCustomOffcanvas(offcanvasId);
    }
};

window.showCustomOffcanvas = function(offcanvasId) {
    const offcanvas = document.getElementById(offcanvasId);
    if (!offcanvas) return;
    
    // Show the panel without backdrop (Solution 1: No backdrop)
    offcanvas.classList.add('custom-show');
    
    // Update panel states for dynamic width adjustment
    if (offcanvasId === 'promptOffcanvas') {
        panelStates.left = true;
        handlePromptOffcanvasShow();
    } else if (offcanvasId === 'productOffcanvas') {
        panelStates.right = true;
        handleProductOffcanvasShow();
    }
    
    // Update modal width based on panel states
    updateModalWidth();
};

window.hideCustomOffcanvas = function(offcanvasId) {
    const offcanvas = document.getElementById(offcanvasId);
    if (!offcanvas) return;
    
    // Hide the panel (Solution 1: No backdrop management needed)
    offcanvas.classList.remove('custom-show');
    
    // Update panel states for dynamic width adjustment
    if (offcanvasId === 'promptOffcanvas') {
        panelStates.left = false;
    } else if (offcanvasId === 'productOffcanvas') {
        panelStates.right = false;
    }
    
    // Update modal width based on panel states
    updateModalWidth();
};

// Solution 1: No backdrop functions needed - removed to prevent modal interference

// Custom implementation - no longer needed
function preventOffcanvasAutoHide() {
    // Custom implementation handles this automatically
}

// Handle AI generation
async function handleWorkspaceAIGeneration() {
    if (!currentWorkspaceUsername) {
        showToast('Fehler: Kein Lead ausgewählt', 'error');
        return;
    }
    
    const button = document.getElementById('workspaceGenerateEmailBtn');
    const originalText = button.innerHTML;
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generiere...';
        button.disabled = true;
        
        const response = await fetch(`/draft-email/${currentWorkspaceUsername}`);
        if (response.ok) {
            const result = await response.json();
            
            document.getElementById('workspaceEmailSubject').value = result.subject || '';
            document.getElementById('workspaceEmailContent').value = result.body || '';
            
            updateCharacterCount('workspaceEmailSubject', 'workspaceSubjectCharCount', 100);
            updateCharacterCount('workspaceEmailContent', 'workspaceContentCharCount');
            
            showToast('Email-Inhalt erfolgreich generiert!', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Fehler bei der Email-Generierung', 'error');
        }
    } catch (error) {
        console.error('AI generation error:', error);
        showToast('Ein Fehler ist bei der Email-Generierung aufgetreten', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Handle save draft
async function handleWorkspaceSaveDraft() {
    if (!currentWorkspaceUsername) {
        showToast('Fehler: Kein Lead ausgewählt', 'error');
        return;
    }
    
    const subject = document.getElementById('workspaceEmailSubject').value.trim();
    const emailBody = document.getElementById('workspaceEmailContent').value.trim();
    
    if (!subject || !emailBody) {
        showToast('Bitte fülle Betreff und Inhalt aus', 'error');
        return;
    }
    
    const button = document.getElementById('workspaceSaveDraftBtn');
    const originalText = button.innerHTML;
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Speichere...';
        button.disabled = true;
        
        const response = await fetch(`/update-lead/${currentWorkspaceUsername}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, email_body: emailBody })
        });
        
        if (response.ok) {
            showToast('Entwurf erfolgreich gespeichert!', 'success');
            // Update the leads table if it's visible
            if (typeof displayResults === 'function' && window.leads) {
                const lead = window.leads.find(l => l.username === currentWorkspaceUsername);
                if (lead) {
                    lead.subject = subject;
                    lead.email_body = emailBody;
                    displayResults(window.leads);
                }
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Fehler beim Speichern des Entwurfs', 'error');
        }
    } catch (error) {
        console.error('Save draft error:', error);
        showToast('Ein Fehler ist beim Speichern aufgetreten', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Handle send email
async function handleWorkspaceSendEmail() {
    if (!currentWorkspaceUsername) {
        showToast('Fehler: Kein Lead ausgewählt', 'error');
        return;
    }
    
    const subject = document.getElementById('workspaceEmailSubject').value.trim();
    const emailBody = document.getElementById('workspaceEmailContent').value.trim();
    
    if (!subject || !emailBody) {
        showToast('Bitte fülle Betreff und Inhalt aus', 'error');
        return;
    }
    
    if (!confirm('E-Mail wirklich senden?')) {
        return;
    }
    
    const button = document.getElementById('workspaceSendEmailBtn');
    const originalText = button.innerHTML;
    
    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sende...';
        button.disabled = true;
        
        // First save the draft
        await fetch(`/update-lead/${currentWorkspaceUsername}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, email_body: emailBody })
        });
        
        // Then send the email
        const response = await fetch(`/send-email/${currentWorkspaceUsername}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('E-Mail erfolgreich gesendet!', 'success');
            
            // Update the leads table
            if (typeof displayResults === 'function' && window.leads) {
                const lead = window.leads.find(l => l.username === currentWorkspaceUsername);
                if (lead) {
                    lead.subject = subject;
                    lead.email_body = emailBody;
                    lead.sent = true;
                    displayResults(window.leads);
                }
            }
            
            // Close the modal using custom function
            hideEmailWorkspace();
            // Also close any open offcanvas panels
            hideCustomOffcanvas('promptOffcanvas');
            hideCustomOffcanvas('productOffcanvas');
        } else {
            const error = await response.json();
            showToast(error.error || 'Fehler beim Senden der E-Mail', 'error');
        }
    } catch (error) {
        console.error('Send email error:', error);
        showToast('Ein Fehler ist beim Senden aufgetreten', 'error');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Handle workspace product selection change
async function handleWorkspaceProductChange() {
    const productId = document.getElementById('workspaceProductSelect').value;
    
    if (!currentWorkspaceUsername) return;
    
    try {
        const response = await fetch(`/api/leads/${currentWorkspaceUsername}/product`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId || null })
        });
        
        if (response.ok) {
            showToast('Produkt-Zuordnung aktualisiert', 'success');
            
            // Update the leads table if visible
            if (typeof displayResults === 'function' && window.leads) {
                const lead = window.leads.find(l => l.username === currentWorkspaceUsername);
                if (lead) {
                    lead.selectedProductId = productId ? parseInt(productId) : null;
                    displayResults(window.leads);
                }
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Fehler beim Aktualisieren der Produkt-Zuordnung', 'error');
        }
    } catch (error) {
        console.error('Product change error:', error);
        showToast('Ein Fehler ist aufgetreten', 'error');
    }
}

// Handle prompt mode/type changes
function handlePromptModeChange() {
    // Reload settings when mode changes
    reloadPromptSettings();
}

function handlePromptTypeChange() {
    // Reload settings when type changes  
    reloadPromptSettings();
    // Also update variable visibility
    handlePromptModeVariableVisibility();
}

async function reloadPromptSettings() {
    if (!currentWorkspaceLeadId) return;
    
    try {
        const response = await fetch(`/api/workspace-data/${currentWorkspaceLeadId}`);
        if (response.ok) {
            const data = await response.json();
            
            const mode = document.querySelector('input[name="offcanvasPromptMode"]:checked')?.value || 'without_product';
            const type = document.getElementById('offcanvasPromptTypeSelect')?.value || 'subject';
            
            loadPromptSettingsForType(mode, type, data.promptSettings);
        }
    } catch (error) {
        console.error('Error reloading prompt settings:', error);
    }
}

// Handle save prompt
async function handleSavePrompt() {
    const mode = document.querySelector('input[name="offcanvasPromptMode"]:checked')?.value;
    const type = document.getElementById('offcanvasPromptTypeSelect')?.value;
    const systemMessage = document.getElementById('offcanvasSystemMessage').value;
    const userTemplate = document.getElementById('offcanvasUserTemplate').value;
    
    // Collect variable settings
    const variableSettings = {};
    document.querySelectorAll('#offcanvasVariablesList input[type="checkbox"]').forEach(checkbox => {
        variableSettings[checkbox.value] = checkbox.checked;
    });
    
    const button = document.getElementById('savePromptOffcanvas');
    const buttonText = button.querySelector('.button-text');
    const originalText = buttonText.textContent;
    
    try {
        buttonText.textContent = 'Speichere...';
        button.disabled = true;
        
        const response = await fetch('/api/save-prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt_type: type,
                has_product: mode === 'with_product',
                system_message: systemMessage,
                user_template: userTemplate,
                variable_settings: variableSettings
            })
        });
        
        if (response.ok) {
            // Show success feedback
            buttonText.textContent = 'Gespeichert!';
            button.style.backgroundColor = 'var(--bs-success)';
            
            setTimeout(() => {
                buttonText.textContent = originalText;
                button.style.backgroundColor = '';
                
                // Hide the custom offcanvas
                hideCustomOffcanvas('promptOffcanvas');
            }, 2000);
            
        } else {
            const error = await response.json();
            showErrorInOffcanvas('promptErrorMessage', error.error || 'Fehler beim Speichern der Prompt-Einstellungen');
        }
    } catch (error) {
        console.error('Save prompt error:', error);
        showErrorInOffcanvas('promptErrorMessage', 'Ein Fehler ist beim Speichern aufgetreten');
    } finally {
        if (buttonText.textContent === 'Speichere...') {
            buttonText.textContent = originalText;
            button.disabled = false;
        }
    }
}

// Handle product selector change
function handleProductSelectorChange() {
    const productId = document.getElementById('offcanvasProductSelector').value;
    
    if (!productId) {
        clearProductForm();
        return;
    }
    
    // Load product data
    loadProductForEditing(productId);
}

// Load product data for editing
async function loadProductForEditing(productId) {
    try {
        const response = await fetch('/api/products');
        if (response.ok) {
            const data = await response.json();
            const product = data.products.find(p => p.id == productId);
            
            if (product) {
                document.getElementById('offcanvasProductEditId').value = product.id;
                document.getElementById('offcanvasProductName').value = product.name;
                document.getElementById('offcanvasProductUrl').value = product.url;
                document.getElementById('offcanvasProductImageUrl').value = product.image_url;
                document.getElementById('offcanvasProductDescription').value = product.description;
                document.getElementById('offcanvasProductPrice').value = product.price;
                document.getElementById('deleteProductOffcanvas').style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Error loading product:', error);
        showErrorInOffcanvas('productErrorMessage', 'Fehler beim Laden der Produktdaten');
    }
}

// Handle save product
async function handleSaveProduct() {
    const productId = document.getElementById('offcanvasProductEditId').value;
    const name = document.getElementById('offcanvasProductName').value.trim();
    const url = document.getElementById('offcanvasProductUrl').value.trim();
    const imageUrl = document.getElementById('offcanvasProductImageUrl').value.trim();
    const description = document.getElementById('offcanvasProductDescription').value.trim();
    const price = document.getElementById('offcanvasProductPrice').value.trim();
    
    if (!name || !url || !imageUrl) {
        showErrorInOffcanvas('productErrorMessage', 'Bitte fülle Name, URL und Bild-URL aus');
        return;
    }
    
    const button = document.getElementById('saveProductOffcanvas');
    const buttonText = button.querySelector('.button-text');
    const originalText = buttonText.textContent;
    
    try {
        buttonText.textContent = 'Speichere...';
        button.disabled = true;
        
        const productData = {
            name, url, image_url: imageUrl, description, price
        };
        
        if (productId) {
            productData.id = parseInt(productId);
        }
        
        const response = await fetch('/api/save-product', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Show success feedback
            buttonText.textContent = 'Gespeichert!';
            button.style.backgroundColor = 'var(--bs-success)';
            
            setTimeout(() => {
                buttonText.textContent = originalText;
                button.style.backgroundColor = '';
                
                // Reload workspace data to update product lists
                if (currentWorkspaceLeadId) {
                    loadWorkspaceData(currentWorkspaceLeadId);
                }
                
                // Hide the custom offcanvas
                hideCustomOffcanvas('productOffcanvas');
            }, 2000);
            
        } else {
            const error = await response.json();
            showErrorInOffcanvas('productErrorMessage', error.error || 'Fehler beim Speichern des Produkts');
        }
    } catch (error) {
        console.error('Save product error:', error);
        showErrorInOffcanvas('productErrorMessage', 'Ein Fehler ist beim Speichern aufgetreten');
    } finally {
        if (buttonText.textContent === 'Speichere...') {
            buttonText.textContent = originalText;
            button.disabled = false;
        }
    }
}

// Handle delete product
async function handleDeleteProduct() {
    const productId = document.getElementById('offcanvasProductEditId').value;
    const productName = document.getElementById('offcanvasProductName').value;
    
    if (!productId) return;
    
    if (!confirm(`Produkt "${productName}" wirklich löschen?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Produkt erfolgreich gelöscht', 'success');
            
            // Clear form and reload data
            clearProductForm();
            if (currentWorkspaceLeadId) {
                loadWorkspaceData(currentWorkspaceLeadId);
            }
            
            // Hide the custom offcanvas
            hideCustomOffcanvas('productOffcanvas');
        } else {
            const error = await response.json();
            showErrorInOffcanvas('productErrorMessage', error.error || 'Fehler beim Löschen des Produkts');
        }
    } catch (error) {
        console.error('Delete product error:', error);
        showErrorInOffcanvas('productErrorMessage', 'Ein Fehler ist beim Löschen aufgetreten');
    }
}

// Show error message in offcanvas
function showErrorInOffcanvas(errorElementId, message) {
    const errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
}