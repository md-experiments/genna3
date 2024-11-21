// Dark mode handling
function initDarkMode() {
    const modeSwitch = document.getElementById('modeSwitch');
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        modeSwitch.checked = true;
    }

    modeSwitch.addEventListener('change', () => {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', modeSwitch.checked);
    });
}

// Load existing manual annotations
function loadAnnotations(filename) {
    const project = document.body.getAttribute('data-project');
    fetch(`/load_annotations/${project}/${filename}`)
        .then(response => response.json())
        .then(data => {
            // Handle manual annotations
            if (data.manual_annotations) {
                Object.entries(data.manual_annotations).forEach(([rowId, annotations]) => {
                    Object.entries(annotations).forEach(([column, value]) => {
                        const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
                        if (row) {
                            const cells = Array.from(row.cells);
                            const cell = cells.find(cell => {
                                const content = cell.textContent.trim();
                                return content.startsWith(column);
                            });
                            if (cell) {
                                const btn = cell.querySelector(value ? '.thumbs-up' : '.thumbs-down');
                                if (btn) btn.classList.add('active');
                            }
                        }
                    });
                });
            }

            // Handle AI annotations
            if (data.ai_annotations) {
                Object.entries(data.ai_annotations).forEach(([modelId, modelAnnotations]) => {
                    Object.entries(modelAnnotations).forEach(([rowId, rowAnnotations]) => {
                        Object.entries(rowAnnotations).forEach(([column, value]) => {
                            const element = document.querySelector(
                                `tr.annotations-row[data-row-id="${rowId}"] ` +
                                `.annotation-value[data-model="${modelId}"][data-column="${column}"]`
                            );
                            if (element) {
                                element.textContent = value;
                            }
                        });
                    });
                });
            }
        });
}

// Toggle row annotations visibility
function toggleAnnotations(rowId) {
    const button = document.querySelector(`tr[data-row-id="${rowId}"] .expand-row i`);
    const annotationsRow = document.querySelector(`tr.annotations-row[data-row-id="${rowId}"]`);
    
    if (annotationsRow.style.display === 'none') {
        button.classList.remove('bi-chevron-right');
        button.classList.add('bi-chevron-down');
        annotationsRow.style.display = 'table-row';
    } else {
        button.classList.remove('bi-chevron-down');
        button.classList.add('bi-chevron-right');
        annotationsRow.style.display = 'none';
    }
}

// Set manual label for a cell
function setLabel(rowId, column, value, project) {
    const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
    const cells = Array.from(row.cells);
    const cell = cells.find(cell => {
        const content = cell.textContent.trim();
        return content.startsWith(column);
    });
    
    if (cell) {
        const thumbsUp = cell.querySelector('.thumbs-up');
        const thumbsDown = cell.querySelector('.thumbs-down');
        
        thumbsUp.classList.toggle('active', value);
        thumbsDown.classList.toggle('active', !value);

        const filename = document.getElementById('fileSelect').value;
        if (!filename) return;

        fetch(`/save_annotations/${project}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project: project,
                csv_filename: filename,
                manual_annotations: {
                    [rowId]: {
                        [column]: value
                    }
                }
            })
        });
    }
}

// Load model annotations
function loadModelAnnotations(project) {
    fetch(`/get_model_annotations/${project}`)
        .then(response => response.json())
        .then(data => {
            Object.entries(data).forEach(([modelId, modelAnnotations]) => {
                Object.entries(modelAnnotations).forEach(([rowId, rowAnnotations]) => {
                    Object.entries(rowAnnotations).forEach(([column, value]) => {
                        const element = document.querySelector(
                            `tr.annotations-row[data-row-id="${rowId}"] ` +
                            `.annotation-value[data-model="${modelId}"][data-column="${column}"]`
                        );
                        if (element) {
                            element.textContent = value;
                        }
                    });
                });
            });
        });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
});
