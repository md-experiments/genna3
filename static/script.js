document.addEventListener('DOMContentLoaded', () => {
    const uploadBtn = document.getElementById('uploadBtn');
    const csvFile = document.getElementById('csvFile');
    const dataContainer = document.getElementById('dataContainer');
    const projectList = document.getElementById('projectList');
    const projectSelect = document.getElementById('projectSelect');
    const modeSwitch = document.getElementById('modeSwitch');
    const newProjectBtn = document.getElementById('newProjectBtn');
    const aiAnnotationTemplate = document.getElementById('aiAnnotationTemplate');

    let currentProject = '';
    let currentCsvFilename = '';
    let debounceTimer;
    let originalData = [];
    let categories = {};
    let columns = [];
    let activeFilters = {};
    let aiAnnotators = [];

    uploadBtn.addEventListener('click', uploadCSV);
    modeSwitch.addEventListener('change', toggleDarkMode);
    projectSelect.addEventListener('change', updateProjectSelect);
    newProjectBtn.addEventListener('click', createNewProject);

    // Check for saved mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        modeSwitch.checked = true;
    }

    function toggleDarkMode() {
        document.body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', modeSwitch.checked);
    }

    function updateProjectSelect() {
        currentProject = projectSelect.value;
        loadProjectFiles(currentProject);
    }

    function createNewProject() {
        const projectName = prompt("Enter new project name:");
        if (projectName) {
            fetch('/create_project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ project_name: projectName }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadProjects();
                    alert('Project created successfully!');
                } else {
                    alert('Failed to create project. Please try again.');
                }
            })
            .catch(error => console.error('Error:', error));
        }
    }

    function uploadCSV() {
        const file = csvFile.files[0];
        if (file && currentProject) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('project', currentProject);

            fetch('/upload_csv', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.filename) {
                    loadProjectFiles(currentProject);
                }
            })
            .catch(error => console.error('Error:', error));
        } else {
            alert('Please select a project and a file to upload.');
        }
    }

    function loadProjects() {
        fetch('/get_projects')
        .then(response => response.json())
        .then(projects => {
            projectSelect.innerHTML = '<option value="">Select Project</option>';
            projectList.innerHTML = '';
            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project;
                option.textContent = project;
                projectSelect.appendChild(option);

                const li = document.createElement('li');
                li.className = 'nav-item';
                li.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <a class="nav-link project-link" href="#" data-project="${project}">
                            <i class="bi bi-chevron-right"></i> ${project}
                        </a>
                        <a href="/settings/${project}" class="btn btn-sm btn-outline-secondary me-2" title="Project Settings">
                            <i class="bi bi-gear"></i>
                        </a>
                    </div>
                    <ul class="nav flex-column project-files" style="display: none;"></ul>
                `;
                projectList.appendChild(li);
            });

            // Add event listeners to project links
            document.querySelectorAll('.project-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const projectName = link.getAttribute('data-project');
                    const filesContainer = link.parentElement.nextElementSibling;
                    const chevron = link.querySelector('i');

                    if (filesContainer.style.display === 'none') {
                        loadProjectFiles(projectName, filesContainer);
                        filesContainer.style.display = 'block';
                        chevron.classList.replace('bi-chevron-right', 'bi-chevron-down');
                    } else {
                        filesContainer.style.display = 'none';
                        chevron.classList.replace('bi-chevron-down', 'bi-chevron-right');
                    }
                });
            });
        })
        .catch(error => console.error('Error:', error));
    }

    function loadProjectFiles(project, container = null) {
        fetch(`/get_project_files/${project}`)
        .then(response => response.json())
        .then(files => {
            const filesContainer = container || document.querySelector(`[data-project="${project}"]`).parentElement.nextElementSibling;
            filesContainer.innerHTML = '';
            files.forEach(file => {
                const li = document.createElement('li');
                li.className = 'nav-item d-flex justify-content-between align-items-center';
                const a = document.createElement('a');
                a.className = 'nav-link csv-file';
                a.textContent = file;
                a.href = '#';
                a.onclick = (e) => {
                    e.preventDefault();
                    loadCSV(project, file);
                };
                const deleteIcon = document.createElement('i');
                deleteIcon.className = 'bi bi-trash text-secondary';
                deleteIcon.style.cursor = 'pointer';
                deleteIcon.onclick = (e) => {
                    e.stopPropagation();
                    deleteFile(project, file);
                };
                li.appendChild(a);
                li.appendChild(deleteIcon);
                filesContainer.appendChild(li);
            });
        })
        .catch(error => console.error('Error:', error));
    }

    function deleteFile(project, filename) {
        if (confirm(`Are you sure you want to delete ${filename} and its annotations?`)) {
            fetch('/delete_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ project, filename }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    loadProjectFiles(project);
                    if (currentCsvFilename === filename) {
                        dataContainer.innerHTML = '';
                        currentCsvFilename = '';
                    }
                } else {
                    alert('Error deleting file: ' + data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        }
    }

    function loadCSV(project, filename) {
        currentProject = project;
        currentCsvFilename = filename;
        fetch(`/load_csv/${project}/${filename}`)
            .then(response => response.json())
            .then(data => {
                originalData = data.data;
                categories = data.categories;
                columns = data.columns;
                aiAnnotators = data.ai_annotators || [];
                displayData(data.data);
                createFilters();
                loadAnnotations(project, filename);
                highlightActiveCSV(filename);
            })
            .catch(error => console.error('Error:', error));
    }

    function createAIAnnotationCell() {
        const container = document.createElement('div');
        container.className = 'annotations-container';
        return container;
    }

    function displayData(data) {
        const table = document.createElement('table');
        table.className = 'table table-striped table-sm';
        
        // Create table header
        const thead = table.createTHead();
        const headerRow = thead.insertRow();
        
        // Add data columns
        columns.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });

        // Add manual annotation column
        const manualHeader = document.createElement('th');
        manualHeader.textContent = 'Manual Annotation';
        headerRow.appendChild(manualHeader);

        // Add AI annotations column
        if (aiAnnotators.length > 0) {
            const aiHeader = document.createElement('th');
            aiHeader.textContent = 'AI Annotations';
            headerRow.appendChild(aiHeader);
        }

        // Create table body
        const tbody = table.createTBody();
        data.forEach((row, index) => {
            const tr = tbody.insertRow();
            
            // Add data columns
            columns.forEach(column => {
                const td = tr.insertCell();
                if (typeof row[column] === 'number') {
                    td.innerHTML = row[column];
                    td.style.textAlign = 'right';
                } else if (typeof row[column] === 'string') {
                    td.innerHTML = row[column].replace(/\n/g, '<br>');
                } else {
                    td.innerHTML = row[column];
                }
            });

            // Add manual annotation cell
            const manualCell = tr.insertCell();
            manualCell.className = 'manual-annotation';
            
            // Add thumbs up/down
            const annotationDiv = document.createElement('div');
            annotationDiv.className = 'd-flex align-items-center mb-2';
            
            const thumbsUp = document.createElement('i');
            thumbsUp.className = 'bi bi-hand-thumbs-up thumbs thumbs-up';
            const thumbsDown = document.createElement('i');
            thumbsDown.className = 'bi bi-hand-thumbs-down thumbs thumbs-down';
            
            thumbsUp.onclick = () => {
                thumbsUp.classList.toggle('active');
                thumbsDown.classList.remove('active');
                saveAnnotations();
            };
            thumbsDown.onclick = () => {
                thumbsDown.classList.toggle('active');
                thumbsUp.classList.remove('active');
                saveAnnotations();
            };

            annotationDiv.appendChild(thumbsUp);
            annotationDiv.appendChild(thumbsDown);
            manualCell.appendChild(annotationDiv);

            // Add comment textarea
            const textarea = document.createElement('textarea');
            textarea.className = 'form-control';
            textarea.rows = 1;
            textarea.placeholder = 'Add a comment...';
            textarea.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(saveAnnotations, 500);
            });
            manualCell.appendChild(textarea);

            // Add AI annotations cell if there are AI annotators
            if (aiAnnotators.length > 0) {
                const aiCell = tr.insertCell();
                aiCell.appendChild(createAIAnnotationCell());
            }
        });

        dataContainer.innerHTML = '';
        dataContainer.appendChild(table);
    }

    function saveAnnotations() {
        const table = dataContainer.querySelector('table');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        const manualAnnotations = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            const rowData = {};
            
            // Get data from content columns
            cells.slice(0, columns.length).forEach((cell, index) => {
                rowData[columns[index]] = cell.textContent;
            });
            
            // Get manual annotation
            const manualCell = cells[columns.length];
            const thumbsUp = manualCell.querySelector('.thumbs-up');
            const thumbsDown = manualCell.querySelector('.thumbs-down');
            rowData['annotation'] = thumbsUp.classList.contains('active') ? 'thumbs_up' : 
                                  (thumbsDown.classList.contains('active') ? 'thumbs_down' : 'none');
            rowData['comment'] = manualCell.querySelector('textarea').value;
            
            return rowData;
        });

        fetch('/save_annotations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project: currentProject,
                csv_filename: currentCsvFilename,
                manual_annotations: manualAnnotations,
                ai_annotations: {} // Will be populated when AI annotations are implemented
            }),
        })
        .then(response => response.json())
        .then(data => console.log(data.message))
        .catch((error) => console.error('Error:', error));
    }

    function loadAnnotations(project, csvFilename) {
        fetch(`/load_annotations/${project}/${csvFilename}`)
        .then(response => response.json())
        .then(data => {
            if (data.manual_annotations && data.manual_annotations.length > 0) {
                applyManualAnnotations(data.manual_annotations);
            }
            if (data.ai_annotations) {
                applyAIAnnotations(data.ai_annotations);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function applyManualAnnotations(annotations) {
        const table = dataContainer.querySelector('table');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        rows.forEach((row, index) => {
            const annotation = annotations[index];
            if (annotation) {
                const manualCell = row.cells[columns.length];
                const thumbsUp = manualCell.querySelector('.thumbs-up');
                const thumbsDown = manualCell.querySelector('.thumbs-down');
                const textarea = manualCell.querySelector('textarea');

                thumbsUp.classList.remove('active');
                thumbsDown.classList.remove('active');

                if (annotation.annotation === 'thumbs_up') {
                    thumbsUp.classList.add('active');
                } else if (annotation.annotation === 'thumbs_down') {
                    thumbsDown.classList.add('active');
                }

                textarea.value = annotation.comment || '';
            }
        });
    }

    function applyAIAnnotations(aiAnnotations) {
        const table = dataContainer.querySelector('table');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        rows.forEach((row, index) => {
            if (aiAnnotators.length > 0) {
                const aiCell = row.cells[columns.length + 1];
                const container = aiCell.querySelector('.annotations-container');
                container.innerHTML = '';

                aiAnnotators.forEach(annotator => {
                    const annotations = aiAnnotations[annotator.model_name];
                    if (annotations && annotations[index]) {
                        const annotation = annotations[index];
                        const element = aiAnnotationTemplate.content.cloneNode(true);
                        
                        element.querySelector('.model-name').textContent = annotator.model_name;
                        element.querySelector('.temperature').textContent = `temp: ${annotator.temperature}`;
                        element.querySelector('.ai-annotation-content').textContent = annotation;
                        
                        container.appendChild(element);
                    }
                });
            }
        });
    }

    function highlightActiveCSV(filename) {
        const csvLinks = document.querySelectorAll('.csv-file');
        csvLinks.forEach(link => {
            link.classList.remove('active');
            if (link.textContent === filename) {
                link.classList.add('active');
            }
        });
    }

    function createFilters() {
        const filterContainer = document.createElement('div');
        filterContainer.className = 'filter-container mb-3';

        Object.keys(categories).forEach(column => {
            const select = document.createElement('select');
            select.className = 'form-select me-2';
            select.id = `filter-${column}`;
            select.multiple = true;
            select.innerHTML = `<option value="">All ${column}</option>`;
            categories[column].forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                option.selected = activeFilters[column] && activeFilters[column].includes(category);
                select.appendChild(option);
            });
            select.addEventListener('change', applyFilters);
            
            const label = document.createElement('label');
            label.textContent = `${column}: `;
            label.appendChild(select);

            filterContainer.appendChild(label);
        });

        const existingFilterContainer = document.querySelector('.filter-container');
        if (existingFilterContainer) {
            existingFilterContainer.replaceWith(filterContainer);
        } else {
            dataContainer.insertBefore(filterContainer, dataContainer.firstChild);
        }
    }

    function applyFilters() {
        activeFilters = {};
        Object.keys(categories).forEach(column => {
            const filterSelect = document.getElementById(`filter-${column}`);
            const selectedOptions = Array.from(filterSelect.selectedOptions).map(option => option.value);
            if (selectedOptions.length > 0 && !selectedOptions.includes('')) {
                activeFilters[column] = selectedOptions;
            }
        });

        const filteredData = originalData.filter(row => {
            return Object.keys(activeFilters).every(column => {
                return activeFilters[column].includes(row[column]);
            });
        });

        displayData(filteredData);
        createFilters(); // Recreate filters to reflect current selections
    }
    
    // Load projects on page load
    loadProjects();
});
