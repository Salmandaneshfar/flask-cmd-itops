// سیستم مدیریت فیلدهای داینامیک - بازنویسی شده
class DynamicFieldsManager {
    constructor(modelName, containerId) {
        this.modelName = modelName;
        this.containerId = containerId;
        this.fields = [];
        this.currentRecordId = null;
        this.init();
    }

    async init() {
        await this.loadFields();
        this.renderFields();
        this.setupEventListeners();
    }

    async loadFields() {
        try {
            console.log(`Loading fields for model: ${this.modelName}`);
            const response = await fetch(`/api/custom-fields/${this.modelName}?t=${Date.now()}`);
            console.log('API Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this.fields = await response.json();
            console.log('Fields loaded:', this.fields);
            
            // Debug select fields specifically
            const selectFields = this.fields.filter(f => f.field_type === 'select');
            console.log('Select fields found:', selectFields);
            selectFields.forEach(field => {
                console.log(`Field ${field.name}:`, field.options);
            });
        } catch (error) {
            console.error('خطا در بارگذاری فیلدها:', error);
        }
    }

    renderFields() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('Container not found:', this.containerId);
            return;
        }

        // پاک کردن فیلدهای قبلی
        container.innerHTML = '';

        if (this.fields.length === 0) {
            container.innerHTML = '<div class="text-muted">هیچ فیلد سفارشی تعریف نشده است.</div>';
            return;
        }

        // اضافه کردن فیلدهای داینامیک
        this.fields.forEach(field => {
            const fieldElement = this.createFieldElement(field);
            container.appendChild(fieldElement);
        });
    }

    createFieldElement(field) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'mb-3 dynamic-field';
        fieldDiv.setAttribute('data-field-id', field.id);

        let fieldHtml = `
            <label class="form-label">
                ${field.label}
                ${field.is_required ? '<span class="text-danger">*</span>' : ''}
            </label>
        `;

        // ایجاد فیلد بر اساس نوع
        switch (field.field_type) {
            case 'text':
            case 'email':
            case 'url':
            case 'phone':
                fieldHtml += `
                    <input type="${field.field_type === 'email' ? 'email' : field.field_type === 'url' ? 'url' : field.field_type === 'phone' ? 'tel' : 'text'}" 
                           class="form-control" 
                           name="custom_field_${field.id}" 
                           placeholder="${field.placeholder || ''}"
                           ${field.is_required ? 'required' : ''}>
                `;
                break;
            case 'number':
                fieldHtml += `
                    <input type="number" 
                           class="form-control" 
                           name="custom_field_${field.id}" 
                           placeholder="${field.placeholder || ''}"
                           ${field.is_required ? 'required' : ''}>
                `;
                break;
            case 'date':
                fieldHtml += `
                    <input type="date" 
                           class="form-control" 
                           name="custom_field_${field.id}"
                           ${field.is_required ? 'required' : ''}>
                `;
                break;
            case 'select':
                console.log(`Rendering select field ${field.name} with options:`, field.options);
                const optionsHtml = field.options ? field.options.map(option => `<option value="${option}">${option}</option>`).join('') : '';
                console.log(`Options HTML:`, optionsHtml);
                fieldHtml += `
                    <select class="form-select" 
                            name="custom_field_${field.id}"
                            ${field.is_required ? 'required' : ''}>
                        <option value="">انتخاب کنید...</option>
                        ${optionsHtml}
                    </select>
                `;
                break;
            case 'textarea':
                fieldHtml += `
                    <textarea class="form-control" 
                              name="custom_field_${field.id}" 
                              rows="3" 
                              placeholder="${field.placeholder || ''}"
                              ${field.is_required ? 'required' : ''}></textarea>
                `;
                break;
            case 'checkbox':
                fieldHtml += `
                    <div class="form-check">
                        <input type="checkbox" 
                               class="form-check-input" 
                               name="custom_field_${field.id}"
                               value="1">
                        <label class="form-check-label">${field.label}</label>
                    </div>
                `;
                break;
        }

        // اضافه کردن راهنمای فیلد
        if (field.help_text) {
            fieldHtml += `<div class="form-text">${field.help_text}</div>`;
        }

        fieldDiv.innerHTML = fieldHtml;
        return fieldDiv;
    }

    setupEventListeners() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('Container not found for event listeners:', this.containerId);
            return;
        }

        console.log('Setting up event listeners for dynamic fields');
        
        container.addEventListener('change', (e) => {
            if (e.target.name && e.target.name.startsWith('custom_field_')) {
                console.log('Field changed:', e.target.name, e.target.value);
                this.saveFieldValue(e.target);
            }
        });

        container.addEventListener('input', (e) => {
            if (e.target.name && e.target.name.startsWith('custom_field_') && e.target.type === 'text') {
                // برای فیلدهای متنی، ذخیره با تاخیر
                clearTimeout(this.inputTimeout);
                this.inputTimeout = setTimeout(() => {
                    this.saveFieldValue(e.target);
                }, 1000);
            }
        });
    }

    async saveFieldValue(input) {
        const fieldId = input.name.replace('custom_field_', '');
        const value = input.type === 'checkbox' ? (input.checked ? '1' : '0') : input.value;
        const recordId = this.getCurrentRecordId();

        console.log('Saving field value:', { fieldId, value, recordId, modelName: this.modelName });

        if (recordId <= 0) {
            console.warn('Record ID is 0 or negative, not saving field value');
            return;
        }

        try {
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
            
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
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('Save response:', result);
            
            if (!result.success) {
                console.error('Failed to save field value:', result.error);
                alert('خطا در ذخیره فیلد: ' + result.error);
            }
        } catch (error) {
            console.error('خطا در ذخیره فیلد:', error);
            alert('خطا در ذخیره فیلد: ' + error.message);
        }
    }

    getCurrentRecordId() {
        if (this.currentRecordId !== null) {
            return this.currentRecordId;
        }
        
        // تلاش برای پیدا کردن ID رکورد فعلی از URL
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
    }

    async loadExistingValues(recordId) {
        if (recordId <= 0) return;
        
        try {
            const response = await fetch(`/api/custom-field-values/${this.modelName}/${recordId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const values = await response.json();
            console.log('Loaded existing values:', values);
            
            // پر کردن فیلدها با مقادیر موجود
            Object.keys(values).forEach(fieldName => {
                const fieldData = values[fieldName];
                const input = document.querySelector(`[name="custom_field_${fieldData.field_id}"]`);
                
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = fieldData.value === '1';
                    } else {
                        input.value = fieldData.value;
                    }
                }
            });
        } catch (error) {
            console.error('خطا در بارگذاری مقادیر:', error);
        }
    }

    async refreshFields() {
        await this.loadFields();
        this.renderFields();
    }
}

// تابع کمکی برای مقداردهی اولیه
function initDynamicFields(modelName, containerId) {
    window.dynamicFieldsManager = new DynamicFieldsManager(modelName, containerId);
    return window.dynamicFieldsManager;
}

// تابع برای بارگذاری مقادیر موجود
async function loadExistingValues(modelName, recordId) {
    if (window.dynamicFieldsManager) {
        await window.dynamicFieldsManager.loadExistingValues(recordId);
    }
}
