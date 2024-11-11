document.addEventListener('DOMContentLoaded', () => {
    const uploadBtn = document.getElementById('uploadBtn');
    const csvFile = document.getElementById('csvFile');
    const dataContainer = document.getElementById('dataContainer');
    const projectList = document.getElementById('projectList');
    const projectSelect = document.getElementById('projectSelect');
    const modeSwitch = document.getElementById('modeSwitch');
    const newProjectBtn = document.getElementById('newProjectBtn');

    let currentProject = '';
    let currentCsvFilename = '';
    let debounceTimer;
    let originalData = [];
    let categories = {};
    let columns = [];
    let activeFilters = {};

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
                displayData(data.data);
                createFilters();
                loadAnnotations(project, filename);
                highlightActiveCSV(filename);
            })
            .catch(error => console.error('Error:', error));
    }

    function displayData(data) {
        const table = document.createElement('table');
        table.className = 'table table-striped table-sm';
        
        // Create table header
        const thead = table.createTHead();
        const headerRow = thead.insertRow();
        columns.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        const annotationHeader = document.createElement('th');
        annotationHeader.textContent = 'Annotation';
        headerRow.appendChild(annotationHeader);
        const commentHeader = document.createElement('th');
        commentHeader.textContent = 'Comment';
        headerRow.appendChild(commentHeader);

        // Create table body
        const tbody = table.createTBody();
        data.forEach((row, index) => {
            const tr = tbody.insertRow();
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

            // Add annotation column
            const annotationCell = tr.insertCell();
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

            annotationCell.appendChild(thumbsUp);
            annotationCell.appendChild(thumbsDown);

            // Add comment column
            const commentCell = tr.insertCell();
            const textarea = document.createElement('textarea');
            textarea.className = 'form-control';
            textarea.rows = 1;
            textarea.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(saveAnnotations, 500);
            });
            commentCell.appendChild(textarea);
        });

        dataContainer.innerHTML = '';
        dataContainer.appendChild(table);
    }

    function saveAnnotations() {
        const table = dataContainer.querySelector('table');
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent);
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        const annotations = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            const rowData = {};
            cells.slice(0, -2).forEach((cell, index) => {
                rowData[headers[index]] = cell.textContent;
            });
            
            const thumbsUp = cells[cells.length - 2].querySelector('.thumbs-up');
            const thumbsDown = cells[cells.length - 2].querySelector('.thumbs-down');
            rowData['Annotation'] = thumbsUp.classList.contains('active') ? 'thumbs_up' : 
                                    (thumbsDown.classList.contains('active') ? 'thumbs_down' : 'none');
            
            rowData['Comment'] = cells[cells.length - 1].querySelector('textarea').value;
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
                annotations: annotations
            }),
        })
        .then(response => response.json())
        .then(data => console.log(data.message))
        .catch((error) => console.error('Error:', error));
    }

    function loadAnnotations(project, csvFilename) {
        fetch(`/load_annotations/${project}/${csvFilename}`)
        .then(response => response.json())
        .then(annotations => {
            if (annotations.length > 0) {
                applyAnnotations(annotations);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function applyAnnotations(annotations) {
        const table = dataContainer.querySelector('table');
        const rows = Array.from(table.querySelectorAll('tbody tr'));

        rows.forEach((row, index) => {
            const annotation = annotations[index];
            if (annotation) {
                const thumbsUp = row.querySelector('.thumbs-up');
                const thumbsDown = row.querySelector('.thumbs-down');
                const textarea = row.querySelector('textarea');

                thumbsUp.classList.remove('active');
                thumbsDown.classList.remove('active');

                if (annotation.Annotation === 'thumbs_up') {
                    thumbsUp.classList.add('active');
                } else if (annotation.Annotation === 'thumbs_down') {
                    thumbsDown.classList.add('active');
                }

                textarea.value = annotation.Comment || '';
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
