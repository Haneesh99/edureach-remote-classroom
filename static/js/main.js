// EduReach - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initLanguageSelector();
    initFileUploads();
    initAttendanceForms();
    initFlashMessages();
    initMobileMenu();
});

// Language Selector
function initLanguageSelector() {
    const selector = document.getElementById('language-selector');
    if (selector) {
        selector.addEventListener('change', function() {
            const lang = this.value;
            document.cookie = 'lang=' + lang + ';path=/;max-age=' + (60 * 60 * 24 * 365);
            window.location.reload();
        });
    }
}

// File Upload Enhancements
function initFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        const label = input.closest('.file-upload');
        if (label) {
            input.addEventListener('change', function() {
                const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
                const textElement = label.querySelector('.file-upload-text');
                if (textElement) {
                    textElement.textContent = fileName;
                }
            });
        }
    });
}

// Attendance Form Handling
function initAttendanceForms() {
    const attendanceForms = document.querySelectorAll('.attendance-form');
    attendanceForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
            if (checkboxes.length === 0) {
                e.preventDefault();
                alert('Please select at least one student to mark attendance.');
            }
        });
    });
}

// Flash Messages Auto-dismiss
function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
}

// Mobile Menu Toggle
function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
}

// Quiz Form Validation
function validateQuizForm() {
    const questions = document.querySelectorAll('.quiz-question');
    let allAnswered = true;
    
    questions.forEach((question, index) => {
        const options = question.querySelectorAll('input[type="radio"]:checked');
        if (options.length === 0) {
            allAnswered = false;
            question.style.borderColor = '#C4622D';
        } else {
            question.style.borderColor = '#DDD';
        }
    });
    
    if (!allAnswered) {
        alert('Please answer all questions before submitting.');
        return false;
    }
    
    return true;
}

// Delete Confirmation
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Toggle Section
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.toggle('hidden');
        const icon = document.querySelector('[data-toggle="' + sectionId + '"]');
        if (icon) {
            icon.classList.toggle('expanded');
        }
    }
}

// Smooth Scroll
function smoothScroll(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// Print Page
function printPage() {
    window.print();
}

// Export Table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = 'data:text/csv;charset=utf-8,' + csv.join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Search Filter for Tables
function filterTable(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

// Form Validation Helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateRequired(value) {
    return value.trim().length > 0;
}

function validateDate(dateString) {
    const date = new Date(dateString);
    return !isNaN(date.getTime());
}

// Character Counter for Textareas
function initCharacterCounter() {
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.textContent = '0 / ' + maxLength;
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            const current = this.value.length;
            counter.textContent = current + ' / ' + maxLength;
            counter.classList.toggle('warning', current > maxLength * 0.9);
        });
    });
}

// Tooltip Initialization
function initTooltips() {
    const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = text;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        });
        
        trigger.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) tooltip.remove();
        });
    });
}

// Ajax Form Submission
function submitFormAjax(form, callback) {
    const formData = new FormData(form);
    const xhr = new XMLHttpRequest();
    
    xhr.open(form.method, form.action, true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (callback) callback(xhr);
        }
    };
    
    xhr.send(formData);
}

// Lazy Loading Images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Accordion
function initAccordion() {
    const accordions = document.querySelectorAll('.accordion-header');
    accordions.forEach(header => {
        header.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const isActive = content.classList.contains('active');
            
            document.querySelectorAll('.accordion-content').forEach(c => {
                c.classList.remove('active');
                c.style.maxHeight = null;
            });
            
            if (!isActive) {
                content.classList.add('active');
                content.style.maxHeight = content.scrollHeight + 'px';
            }
        });
    });
}

// Tab Navigation
function initTabs() {
    const tabGroups = document.querySelectorAll('.tabs');
    tabGroups.forEach(group => {
        const tabs = group.querySelectorAll('.tab');
        const panels = group.querySelectorAll('.tab-panel');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetId = this.getAttribute('data-tab');
                
                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                
                this.classList.add('active');
                document.getElementById(targetId).classList.add('active');
            });
        });
    });
}

// Date Picker Enhancement
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.showPicker();
        });
    });
}

// Initialize all components when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initCharacterCounter();
        initTooltips();
        initLazyLoading();
        initAccordion();
        initTabs();
        initDatePickers();
    });
} else {
    initCharacterCounter();
    initTooltips();
    initLazyLoading();
    initAccordion();
    initTabs();
    initDatePickers();
}
