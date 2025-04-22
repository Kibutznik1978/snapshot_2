document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const bidForm = document.getElementById('bidForm');
    const bidData = document.getElementById('bidData');
    const submitBtn = document.getElementById('submitBtn');
    const resetBtn = document.getElementById('resetBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');
    const downloadBtn = document.getElementById('downloadBtn');
    const downloadForm = document.getElementById('downloadForm');
    const resultsData = document.getElementById('resultsData');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');

    // Store the results for downloading
    let currentResults = [];

    // Form submission handler
    bidForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Validate form
        if (!bidForm.checkValidity()) {
            bidForm.classList.add('was-validated');
            return;
        }

        // Hide any previous errors
        errorAlert.classList.add('d-none');
        
        // Show loading state
        submitBtn.disabled = true;
        loadingSpinner.classList.remove('d-none');
        
        try {
            // Send data to the server
            const response = await fetch('/process-bids', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'bid_data': bidData.value
                })
            });
            
            // Check for errors
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.detail || 'An error occurred while processing your request.');
            }
            
            // Parse the response
            const data = await response.json();
            currentResults = data.results;
            
            // Display the results
            displayResults(currentResults);
            
            // Enable download button
            downloadBtn.disabled = false;
            
        } catch (error) {
            // Show error message
            errorMessage.textContent = error.message;
            errorAlert.classList.remove('d-none');
            
            // Clear results
            resultsContainer.innerHTML = '<p class="text-center text-secondary py-5">An error occurred. Please try again.</p>';
            downloadBtn.disabled = true;
            
        } finally {
            // Reset loading state
            submitBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
        }
    });

    // Download button handler
    downloadBtn.addEventListener('click', () => {
        if (currentResults.length === 0) {
            return;
        }
        
        // Populate hidden form field with results data
        resultsData.value = JSON.stringify(currentResults);
        
        // Submit the download form
        downloadForm.submit();
    });
    
    // Reset button handler
    resetBtn.addEventListener('click', () => {
        // Clear the form
        bidForm.reset();
        bidForm.classList.remove('was-validated');
        
        // Clear results
        resultsContainer.innerHTML = '<p class="text-center text-secondary py-5">No results to display yet. Submit bid data to see results here.</p>';
        currentResults = [];
        
        // Disable download button
        downloadBtn.disabled = true;
        
        // Hide error message
        errorAlert.classList.add('d-none');
    });

    // Function to display results in a table
    function displayResults(results) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<p class="text-center text-secondary py-5">No results to display.</p>';
            return;
        }
        
        // Create table HTML
        let tableHtml = `
            <div class="table-responsive">
                <table class="table table-striped table-hover table-sm">
                    <thead>
                        <tr>
                            <th>Bid #</th>
                            <th>Employee ID</th>
                            <th>Employee Name</th>
                            <th>Awarded Line</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add rows for each result
        results.forEach(result => {
            const statusClass = result.awarded_line ? 'text-success' : 'text-danger';
            const statusIcon = result.awarded_line 
                ? '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-check-circle-fill" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/></svg>' 
                : '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-x-circle-fill" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/></svg>';
            const statusMessage = '';
            
            // Highlight the current employee's row with a different background when they have a name
            const isCurrentEmployee = result.employee_name != null && result.employee_name !== '';
            const rowClass = isCurrentEmployee ? 'table-primary' : '';
            
            // For the current employee, show the actual seniority number
            const displayBidPosition = result.bid_position;
            
            tableHtml += `
                <tr class="${rowClass}">
                    <td>${displayBidPosition}</td>
                    <td>${result.employee_id}</td>
                    <td>${result.employee_name || ''}</td>
                    <td>${result.awarded_line || '-'}</td>
                    <td class="${statusClass}">${statusIcon} ${statusMessage}</td>
                </tr>
            `;
        });
        
        // Close table
        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;
        
        // Update the results container
        resultsContainer.innerHTML = tableHtml;
    }
});
