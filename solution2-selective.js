// Solution 2: Selective Override - Alternative Implementation
function enableMultipleOffcanvasSolution2() {
    // Check if both panels are open before applying overrides
    function shouldApplyDualOverride() {
        const promptOpen = document.getElementById('promptOffcanvas').classList.contains('show');
        const productOpen = document.getElementById('productOffcanvas').classList.contains('show');
        return promptOpen && productOpen;
    }
    
    // Custom close button handling
    document.querySelectorAll('[data-bs-dismiss="offcanvas"]').forEach(button => {
        button.addEventListener('click', function(e) {
            if (shouldApplyDualOverride()) {
                // Only override when both panels are open
                e.preventDefault();
                const targetOffcanvas = this.closest('.offcanvas');
                if (targetOffcanvas) {
                    const offcanvasInstance = bootstrap.Offcanvas.getInstance(targetOffcanvas);
                    if (offcanvasInstance) {
                        offcanvasInstance.hide();
                    }
                }
            }
            // If only one panel open, let Bootstrap handle it normally
        });
    });
}