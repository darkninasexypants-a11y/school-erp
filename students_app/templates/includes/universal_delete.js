// Universal Delete Function for All Templates
// Add this script to templates that need improved delete functionality

function universalDelete(url, id, itemName, itemType = 'item') {
    if (confirm(`Are you sure you want to delete this ${itemType}: "${itemName}"? This action cannot be undone.`)) {
        // Create a form to submit delete request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        
        // Add CSRF token
        const csrfToken = document.createElement('input');
        csrfToken.type = 'hidden';
        csrfToken.name = 'csrfmiddlewaretoken';
        csrfToken.value = '{{ csrf_token }}';
        form.appendChild(csrfToken);
        
        // Add delete ID (support different parameter names)
        const idParamNames = ['id', 'delete_id', 'item_id', 'notice_id', 'user_id', 'timetable_id', 'expense_id'];
        idParamNames.forEach(paramName => {
            const idInput = document.createElement('input');
            idInput.type = 'hidden';
            idInput.name = paramName;
            idInput.value = id;
            form.appendChild(idInput);
        });
        
        // Add action parameter if needed
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = 'delete';
        form.appendChild(actionInput);
        
        // Submit form
        document.body.appendChild(form);
        form.submit();
    }
}

// Enhanced delete function for bulk operations
function universalBulkDelete(formId, itemType = 'items') {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with id "${formId}" not found`);
        return;
    }
    
    // Get checked items
    const checked = form.querySelectorAll('input[type="checkbox"]:checked');
    if (checked.length === 0) {
        alert(`Please select at least one ${itemType} to delete.`);
        return;
    }
    
    if (confirm(`Are you sure you want to delete ${checked.length} ${itemType}? This action cannot be undone.`)) {
        // Add action parameter if not present
        let actionInput = form.querySelector('input[name="action"]');
        if (!actionInput) {
            actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            actionInput.value = 'delete';
            form.appendChild(actionInput);
        }
        
        form.submit();
    }
}

// Enhanced simple confirm delete for direct links
function enhancedConfirmDelete(message, url) {
    if (confirm(message + ' This action cannot be undone.')) {
        window.location.href = url;
    }
}
