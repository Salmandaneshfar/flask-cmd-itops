// سیستم مدیریت فیلدهای داینامیک - نسخه 2 (بازنویسی کامل)
class DynamicFieldsManagerV2 {
    constructor(modelName, containerId) {
        this.modelName = modelName;
        this.containerId = containerId;
        this.fields = [];
        this.currentRecordId = null;
        this.fieldValues = {};
        this.init();
    }

    async init() {
        console.log(`🚀 Initializing DynamicFieldsManagerV2 for model: ${this.modelName}`);
        await this.loadFields();
        this.renderFields();
        this.setupEventListeners();
        this.loadExistingValues();
    }

    async loadFields() {
        try {
            console.log(`📡 Loading fields for model: ${this.modelName}`);
            const response = await fetch(`/api/custom-fields/${this.modelName}?t=${Date.now()}`, {
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            
            console.log('📊 API Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.fields = await response.json();
            console.log('✅ Fields loaded successfully:', this.fields);
            
            // Debug select fields specifically
            const selectFields = this.fields.filter(f => f.field_type === 'select');
            console.log('🔽 Select fields found:', selectFields.length);
            selectFields.forEach(field => {
                console.log(`  📋 Field "${field.name}":`, {
                    options: field.options,
                    optionsCount: field.options ? field.options.length : 0
                });
            });
            
        } catch (error) {
            console.error('❌ خطا در بارگذاری فیلدها:', error);
            this.showError('خطا در بارگذاری فیلدها: ' + error.message);
        }
    }

    renderFields() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('❌ Container not found:', this.containerId);
            return;
        }

        console.log('🎨 Rendering fields...');
        
        // Clear existing fields
        container.innerHTML = '';

        if (this.fields.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    هیچ فیلد سفارشی تعریف نشده است.
                </div>
            `;
            return;
        }

        // Create fields container
        const fieldsContainer = document.createElement('div');
        fieldsContainer.className = 'dynamic-fields-container';
        fieldsContainer.setAttribute('data-model', this.modelName);

        // Render each field
        this.fields.forEach((field, index) => {
            const fieldElement = this.createFieldElement(field, index);
            fieldsContainer.appendChild(fieldElement);
        });

        container.appendChild(fieldsContainer);
        console.log('✅ Fields rendered successfully');
    }

    createFieldElement(field, index) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = `mb-3 dynamic-field field-${field.field_type}`;
        fieldDiv.setAttribute('data-field-id', field.id);
        fieldDiv.setAttribute('data-field-type', field.field_type);
        fieldDiv.setAttribute('data-field-name', field.name);

        // Field label
        const label = document.createElement('label');
        label.className = 'form-label fw-bold';
        label.setAttribute('for', `custom_field_${field.id}`);
        label.innerHTML = field.label + (field.is_required ? ' <span class="text-danger">*</span>' : '');
        fieldDiv.appendChild(label);

        // Field input
        const inputElement = this.createInputElement(field);
        fieldDiv.appendChild(inputElement);

        // Help text
        if (field.help_text) {
            const helpDiv = document.createElement('div');
            helpDiv.className = 'form-text text-muted';
            helpDiv.innerHTML = field.help_text;
            fieldDiv.appendChild(helpDiv);
        }

        // Validation message container
        const validationDiv = document.createElement('div');
        validationDiv.className = 'invalid-feedback';
        validationDiv.setAttribute('data-field-id', field.id);
        fieldDiv.appendChild(validationDiv);

        console.log(`✅ Created field element for: ${field.name} (${field.field_type})`);
        return fieldDiv;
    }

    createInputElement(field) {
        const inputContainer = document.createElement('div');
        inputContainer.className = 'input-container';

        switch (field.field_type) {
            case 'text':
            case 'email':
            case 'url':
            case 'phone':
                return this.createTextInput(field);
            
            case 'number':
                return this.createNumberInput(field);
            
            case 'date':
                return this.createDateInput(field);
            
            
            case 'textarea':
                return this.createTextareaInput(field);
            
            case 'checkbox':
                return this.createCheckboxInput(field);
            
            default:
                console.warn(`⚠️ Unknown field type: ${field.field_type}`);
                return this.createTextInput(field);
        }
    }

    createTextInput(field) {
        const input = document.createElement('input');
        input.type = field.field_type === 'email' ? 'email' : 
                    field.field_type === 'url' ? 'url' : 
                    field.field_type === 'phone' ? 'tel' : 'text';
        input.className = 'form-control';
        input.id = `custom_field_${field.id}`;
        input.name = `custom_field_${field.id}`;
        input.placeholder = field.placeholder || '';
        input.required = field.is_required;
        
        // Add RTL support for Persian text
        if (field.field_type === 'text') {
            input.style.direction = 'rtl';
            input.style.textAlign = 'right';
        }
        
        return input;
    }

    createNumberInput(field) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control';
        input.id = `custom_field_${field.id}`;
        input.name = `custom_field_${field.id}`;
        input.placeholder = field.placeholder || '';
        input.required = field.is_required;
        input.style.direction = 'ltr';
        input.style.textAlign = 'left';
        
        return input;
    }

    createDateInput(field) {
        const input = document.createElement('input');
        input.type = 'date';
        input.className = 'form-control';
        input.id = `custom_field_${field.id}`;
        input.name = `custom_field_${field.id}`;
        input.required = field.is_required;
        input.style.direction = 'ltr';
        
        return input;
    }


    createTextareaInput(field) {
        const textarea = document.createElement('textarea');
        textarea.className = 'form-control';
        textarea.id = `custom_field_${field.id}`;
        textarea.name = `custom_field_${field.id}`;
        textarea.rows = 3;
        textarea.placeholder = field.placeholder || '';
        textarea.required = field.is_required;
        textarea.style.direction = 'rtl';
        textarea.style.textAlign = 'right';
        
        return textarea;
    }

    createCheckboxInput(field) {
        const container = document.createElement('div');
        container.className = 'form-check';

        const input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'form-check-input';
        input.id = `custom_field_${field.id}`;
        input.name = `custom_field_${field.id}`;
        input.value = '1';
        input.required = field.is_required;

        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.setAttribute('for', `custom_field_${field.id}`);
        label.textContent = field.label;

        container.appendChild(input);
        container.appendChild(label);
        
        return container;
    }

    setupEventListeners() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('❌ Container not found for event listeners:', this.containerId);
            return;
        }

        console.log('🎧 Setting up event listeners...');

        // Change events for immediate saving
        container.addEventListener('change', (e) => {
            if (e.target.name && e.target.name.startsWith('custom_field_')) {
                console.log('🔄 Field changed:', e.target.name, e.target.value);
                this.handleFieldChange(e.target);
            }
        });

        // Input events for text fields (with debouncing)
        container.addEventListener('input', (e) => {
            if (e.target.name && e.target.name.startsWith('custom_field_') && 
                (e.target.type === 'text' || e.target.type === 'textarea')) {
                clearTimeout(this.inputTimeout);
                this.inputTimeout = setTimeout(() => {
                    this.handleFieldChange(e.target);
                }, 1000);
            }
        });

        // Focus events for validation
        container.addEventListener('focus', (e) => {
            if (e.target.name && e.target.name.startsWith('custom_field_')) {
                this.clearFieldError(e.target);
            }
        }, true);

        console.log('✅ Event listeners set up successfully');
    }

    handleFieldChange(input) {
        const fieldId = input.name.replace('custom_field_', '');
        const value = input.type === 'checkbox' ? (input.checked ? '1' : '0') : input.value;
        const recordId = this.getCurrentRecordId();

        console.log('💾 Handling field change:', { fieldId, value, recordId, modelName: this.modelName });

        // Store value locally
        this.fieldValues[fieldId] = value;

        // Validate field
        if (!this.validateField(input)) {
            return;
        }

        // Save to server if record exists
        if (recordId > 0) {
            this.saveFieldValue(fieldId, value, recordId);
        } else {
            console.log('📝 Record ID is 0, storing locally only');
        }
    }

    validateField(input) {
        const fieldId = input.name.replace('custom_field_', '');
        const field = this.fields.find(f => f.id == fieldId);
        
        if (!field) {
            console.warn(`⚠️ Field not found for validation: ${fieldId}`);
            return true;
        }

        const value = input.type === 'checkbox' ? (input.checked ? '1' : '0') : input.value;
        const isValid = !field.is_required || (value && value.trim() !== '');

        if (!isValid) {
            this.showFieldError(input, 'این فیلد اجباری است');
            return false;
        } else {
            this.clearFieldError(input);
            return true;
        }
    }

    showFieldError(input, message) {
        const fieldDiv = input.closest('.dynamic-field');
        const validationDiv = fieldDiv.querySelector('.invalid-feedback');
        
        if (validationDiv) {
            validationDiv.textContent = message;
            validationDiv.style.display = 'block';
        }
        
        input.classList.add('is-invalid');
    }

    clearFieldError(input) {
        const fieldDiv = input.closest('.dynamic-field');
        const validationDiv = fieldDiv.querySelector('.invalid-feedback');
        
        if (validationDiv) {
            validationDiv.style.display = 'none';
        }
        
        input.classList.remove('is-invalid');
    }

    async saveFieldValue(fieldId, value, recordId) {
        try {
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
            
            console.log('💾 Saving field value:', { fieldId, value, recordId, modelName: this.modelName });
            
            const response = await fetch('/api/custom-field-value', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    field_id: fieldId,
                    model_name: this.modelName,
                    record_id: recordId,
                    value: value
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ Save response:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Unknown error');
            }
            
            // Show success indicator
            this.showFieldSuccess(fieldId);
            
        } catch (error) {
            console.error('❌ خطا در ذخیره فیلد:', error);
            this.showError('خطا در ذخیره فیلد: ' + error.message);
        }
    }

    showFieldSuccess(fieldId) {
        const fieldDiv = document.querySelector(`[data-field-id="${fieldId}"]`);
        if (fieldDiv) {
            const input = fieldDiv.querySelector('input, select, textarea');
            if (input) {
                input.classList.add('is-valid');
                setTimeout(() => {
                    input.classList.remove('is-valid');
                }, 2000);
            }
        }
    }

    showError(message) {
        const container = document.getElementById(this.containerId);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.insertBefore(errorDiv, container.firstChild);
    }

    getCurrentRecordId() {
        if (this.currentRecordId !== null) {
            return this.currentRecordId;
        }
        
        // Try to extract from URL
        const urlParts = window.location.pathname.split('/');
        const lastPart = urlParts[urlParts.length - 1];
        const recordId = parseInt(lastPart);
        
        if (isNaN(recordId) || urlParts.includes('add')) {
            return 0;
        }
        
        return recordId;
    }
    
    setCurrentRecordId(recordId) {
        this.currentRecordId = recordId;
        console.log(`📝 Set current record ID: ${recordId}`);
    }

    async loadExistingValues(recordId = null) {
        const targetRecordId = recordId || this.getCurrentRecordId();
        
        if (targetRecordId <= 0) {
            console.log('📝 No record ID, skipping value loading');
            return;
        }
        
        try {
            console.log(`📥 Loading existing values for record: ${targetRecordId}`);
            
            const response = await fetch(`/api/custom-field-values/${this.modelName}/${targetRecordId}?t=${Date.now()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const values = await response.json();
            console.log('📊 Loaded existing values:', values);
            
            // Populate fields with existing values
            Object.keys(values).forEach(fieldName => {
                const fieldData = values[fieldName];
                const input = document.querySelector(`[name="custom_field_${fieldData.field_id}"]`);
                
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = fieldData.value === '1';
                    } else {
                        input.value = fieldData.value;
                    }
                    
                    // Store in local values
                    this.fieldValues[fieldData.field_id] = fieldData.value;
                    
                    console.log(`✅ Populated field ${fieldName}: ${fieldData.value}`);
                }
            });
            
        } catch (error) {
            console.error('❌ خطا در بارگذاری مقادیر:', error);
        }
    }

    async refreshFields() {
        console.log('🔄 Refreshing fields...');
        await this.loadFields();
        this.renderFields();
        this.setupEventListeners();
    }

    // Public methods for external use
    getFieldValue(fieldId) {
        return this.fieldValues[fieldId] || '';
    }

    getAllFieldValues() {
        return { ...this.fieldValues };
    }

    validateAllFields() {
        const inputs = document.querySelectorAll(`#${this.containerId} input, #${this.containerId} select, #${this.containerId} textarea`);
        let isValid = true;
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
}

// Global functions for backward compatibility
function initDynamicFields(modelName, containerId) {
    console.log(`🌐 Initializing dynamic fields: ${modelName} -> ${containerId}`);
    window.dynamicFieldsManager = new DynamicFieldsManagerV2(modelName, containerId);
    return window.dynamicFieldsManager;
}

async function loadExistingValues(modelName, recordId) {
    if (window.dynamicFieldsManager) {
        await window.dynamicFieldsManager.loadExistingValues(recordId);
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', function() {
    const containers = document.querySelectorAll('[data-dynamic-fields]');
    containers.forEach(container => {
        const modelName = container.getAttribute('data-model');
        const containerId = container.id;
        if (modelName && containerId) {
            initDynamicFields(modelName, containerId);
        }
    });
});

console.log('✅ DynamicFieldsManagerV2 loaded successfully');
