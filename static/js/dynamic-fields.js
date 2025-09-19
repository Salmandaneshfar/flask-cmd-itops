// سیستم مدیریت فیلدهای داینامیک
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
            const response = await fetch(`/api/custom-fields/${this.modelName}?t=${Date.now()}`);
            this.fields = await response.json();
        } catch (error) {
            console.error('خطا در بارگذاری فیلدها:', error);
        }
    }

    renderFields() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // پاک کردن فیلدهای قبلی
        container.innerHTML = '';

        // اضافه کردن فیلدهای داینامیک
        this.fields.forEach(field => {
            const fieldElement = this.createFieldElement(field);
            container.appendChild(fieldElement);
        });

        // اضافه کردن دکمه مدیریت فیلدها (فقط برای ادمین)
        if (this.isAdmin()) {
            this.addFieldManagementButton(container);
        }
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
                fieldHtml += `
                    <select class="form-select" 
                            name="custom_field_${field.id}"
                            ${field.is_required ? 'required' : ''}>
                        <option value="">انتخاب کنید...</option>
                        ${field.options ? field.options.map(option => `<option value="${option}">${option}</option>`).join('') : ''}
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

    addFieldManagementButton(container) {
        const managementDiv = document.createElement('div');
        managementDiv.className = 'mb-3 border-top pt-3';
        managementDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <h6 class="mb-0">مدیریت فیلدهای سفارشی</h6>
                <div>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="dynamicFieldsManager.openFieldManager()">
                        <i class="fas fa-cogs"></i> مدیریت فیلدها
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-success" onclick="dynamicFieldsManager.addNewField()">
                        <i class="fas fa-plus"></i> فیلد جدید
                    </button>
                </div>
            </div>
        `;
        container.appendChild(managementDiv);
    }

    setupEventListeners() {
        // ذخیره خودکار مقادیر فیلدها
        const container = document.getElementById(this.containerId);
        if (container) {
            console.log('Setting up event listeners for dynamic fields');
            container.addEventListener('change', (e) => {
                console.log('Field changed:', e.target.name, e.target.value);
                if (e.target.name && e.target.name.startsWith('custom_field_')) {
                    console.log('Saving field value...');
                    this.saveFieldValue(e.target);
                }
            });
        } else {
            console.error('Dynamic fields container not found:', this.containerId);
        }
    }

    async saveFieldValue(input) {
        const fieldId = input.name.replace('custom_field_', '');
        const value = input.type === 'checkbox' ? (input.checked ? '1' : '0') : input.value;
        const recordId = this.getCurrentRecordId();

        console.log('Saving field value:', { fieldId, value, recordId, modelName: this.modelName });

        // فقط اگر رکورد موجود است، ذخیره کن
        if (recordId > 0) {
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
                
                const result = await response.json();
                console.log('Save response:', result);
                
                if (!result.success) {
                    console.error('Failed to save field value:', result.error);
                }
            } catch (error) {
                console.error('خطا در ذخیره فیلد:', error);
            }
        } else {
            console.warn('Record ID is 0, not saving field value');
        }
    }

    getCurrentRecordId() {
        // اگر ID رکورد قبلاً تنظیم شده، از آن استفاده کن
        if (this.currentRecordId !== null) {
            return this.currentRecordId;
        }
        
        // تلاش برای پیدا کردن ID رکورد فعلی از URL یا فرم
        const urlParts = window.location.pathname.split('/');
        const lastPart = urlParts[urlParts.length - 1];
        const recordId = parseInt(lastPart);
        
        // اگر در صفحه اضافه کردن هستیم، ID صفر است
        if (isNaN(recordId) || urlParts.includes('add')) {
            return 0;
        }
        
        return recordId;
    }
    
    // تابع برای تنظیم ID رکورد فعلی
    setCurrentRecordId(recordId) {
        this.currentRecordId = recordId;
    }

    isAdmin() {
        // بررسی اینکه کاربر ادمین است یا نه
        return document.body.getAttribute('data-user-role') === 'admin';
    }

    openFieldManager() {
        // باز کردن مودال مدیریت فیلدها
        window.open('/custom-fields', '_blank');
    }

    addNewField() {
        // باز کردن صفحه اضافه کردن فیلد جدید
        window.open(`/custom-fields/add?model_name=${this.modelName}`, '_blank');
    }

    async refreshFields() {
        await this.loadFields();
        this.renderFields();
    }
}

// تابع کمکی برای مقداردهی اولیه
function initDynamicFields(modelName, containerId) {
    window.dynamicFieldsManager = new DynamicFieldsManager(modelName, containerId);
}

// تابع برای بارگذاری مقادیر موجود
async function loadExistingValues(modelName, recordId) {
    try {
        const response = await fetch(`/api/custom-field-values/${modelName}/${recordId}`);
        const values = await response.json();
        
        // پیدا کردن فیلدها بر اساس ID
        const fieldInputs = document.querySelectorAll('[name^="custom_field_"]');
        fieldInputs.forEach(input => {
            const fieldId = input.name.replace('custom_field_', '');
            
            // پیدا کردن فیلد بر اساس ID
            const fieldData = Object.values(values).find(data => 
                data.field_id && data.field_id.toString() === fieldId
            );
            
            if (fieldData) {
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

// تابع برای بارگذاری مقادیر بر اساس ID فیلد
async function loadExistingValuesByFieldId(modelName, recordId) {
    try {
        const response = await fetch(`/api/custom-field-values/${modelName}/${recordId}`);
        const values = await response.json();
        
        // پیدا کردن فیلدها بر اساس ID
        const fieldInputs = document.querySelectorAll('[name^="custom_field_"]');
        fieldInputs.forEach(input => {
            const fieldId = input.name.replace('custom_field_', '');
            const fieldName = Object.keys(values).find(name => {
                const fieldData = values[name];
                return fieldData && fieldData.field_id && fieldData.field_id.toString() === fieldId;
            });
            
            if (fieldName && values[fieldName]) {
                if (input.type === 'checkbox') {
                    input.checked = values[fieldName].value === '1';
                } else {
                    input.value = values[fieldName].value;
                }
            }
        });
    } catch (error) {
        console.error('خطا در بارگذاری مقادیر:', error);
    }
}
