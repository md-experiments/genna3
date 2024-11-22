// Load annotations
function loadAnnotations(filename) {
    const project = document.body.getAttribute('data-project');
    fetch(`/load_annotations/${project}/${filename}`)
        .then(response => response.json())
        .then(data => {
            // Handle AI annotations first to determine which models to show
            if (data.ai_annotations) {
                const modelRows = document.querySelectorAll('.model-row');
                modelRows.forEach(row => {
                    const modelId = row.getAttribute('data-model');
                    const modelAnnotations = data.ai_annotations[modelId];
                    
                    // Hide model row by default
                    row.style.display = 'none';
                    
                    // Only show model row if it has annotations for this row
                    if (modelAnnotations) {
                        Object.entries(modelAnnotations).forEach(([rowId, rowAnnotations]) => {
                            if (Object.keys(rowAnnotations).length > 0) {
                                const annotationRow = row.closest('tr.annotations-row');
                                if (annotationRow && annotationRow.getAttribute('data-row-id') === rowId) {
                                    row.style.display = 'table-row';
                                    
                                    // Update annotation values
                                    Object.entries(rowAnnotations).forEach(([column, value]) => {
                                        const element = row.querySelector(
                                            `.annotation-value[data-model="${modelId}"][data-column="${column}"]`
                                        );
                                        if (element) {
                                            element.textContent = value;
                                            element.style.display = 'inline-block';
                                        }
                                    });
                                }
                            }
                        });
                    }
                });
            }

            // Handle manual annotations
            if (data.manual_annotations) {
                Object.entries(data.manual_annotations).forEach(([rowId, annotations]) => {
                    Object.entries(annotations).forEach(([column, value]) => {
                        const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
                        if (row) {
                            const cells = Array.from(row.cells);
                            const cell = cells.find(cell => cell.textContent.trim().startsWith(column));
                            if (cell) {
                                const btn = cell.querySelector(value ? '.thumbs-up' : '.thumbs-down');
                                if (btn) btn.classList.add('active');
                            }
                        }
                    });
                });
            }
        });
}

// Toggle annotations
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

// Set label
function setLabel(rowId, column, value) {
    const project = document.body.getAttribute('data-project');
    const filename = document.getElementById('fileSelect').value;
    if (!filename) return;

    const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
    const cells = Array.from(row.cells);
    const cell = cells.find(cell => cell.textContent.trim().startsWith(column));
    
    if (cell) {
        const thumbsUp = cell.querySelector('.thumbs-up');
        const thumbsDown = cell.querySelector('.thumbs-down');
        
        thumbsUp.classList.toggle('active', value);
        thumbsDown.classList.toggle('active', !value);

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

// Initialize dark mode
const modeSwitch = document.getElementById('modeSwitch');
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
    modeSwitch.checked = true;
}

modeSwitch.addEventListener('change', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', modeSwitch.checked);
});
