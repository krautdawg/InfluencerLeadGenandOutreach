// Solution 3: Reset on Close - Alternative Implementation
function enableMultipleOffcanvasSolution3() {
    const promptOffcanvas = document.getElementById('promptOffcanvas');
    const productOffcanvas = document.getElementById('productOffcanvas');
    
    // Add close event listeners to reset overrides
    [promptOffcanvas, productOffcanvas].forEach(canvas => {
        if (canvas) {
            canvas.addEventListener('hidden.bs.offcanvas', function() {
                // Reset all CSS overrides when any panel closes
                document.querySelectorAll('.offcanvas').forEach(c => {
                    c.style.visibility = '';
                    c.style.transform = '';
                });
                
                // Clear the preventAutoHide behavior
                clearInterval(preventAutoHideInterval);
            });
        }
    });
    
    // Normal close button behavior - no overrides
    document.querySelectorAll('[data-bs-dismiss="offcanvas"]').forEach(button => {
        // Remove any existing custom listeners
        button.removeEventListener('click', customCloseHandler);
    });
}