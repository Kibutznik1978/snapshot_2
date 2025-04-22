document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const bidForm = document.getElementById('bidForm');
    const bidData = document.getElementById('bidData');
    const submitBtn = document.getElementById('submitBtn');
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
                throw new Error(errorData.error || 'An error occurred while processing your request.');
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

    // Function to display results in a table
    function displayResults(results) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<p class="text-center text-secondary py-4 small">No results to display.</p>';
            return;
        }
        
        // Create a summary of results
        const totalBids = results.length;
        const awardedCount = results.filter(r => r.awarded_line).length;
        
        // Create table HTML with summary at the top
        let tableHtml = `
            <div class="mb-3 small">
                <div class="d-flex justify-content-between mb-2">
                    <span>Total Bids: <strong>${totalBids}</strong></span>
                    <span>Awarded: <strong class="text-success">${awardedCount}</strong></span>
                </div>
                <div class="progress" style="height: 8px">
                    <div class="progress-bar bg-success" role="progressbar" style="width: ${(awardedCount/totalBids*100).toFixed(1)}%" 
                        aria-valuenow="${awardedCount}" aria-valuemin="0" aria-valuemax="${totalBids}"></div>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th width="20%">Position</th>
                            <th width="25%">Employee ID</th>
                            <th width="20%">Line</th>
                            <th width="35%">Status</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add rows for each result
        results.forEach(result => {
            const statusClass = result.awarded_line ? 'text-success' : 'text-danger';
            const statusIcon = result.awarded_line 
                ? '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" class="bi bi-check-circle-fill me-1" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/></svg>' 
                : '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" class="bi bi-exclamation-circle-fill me-1" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/></svg>';
            const statusMessage = result.awarded_line ? 'Awarded' : (result.message || 'Not assigned');
            
            tableHtml += `
                <tr>
                    <td>${result.bid_position}</td>
                    <td>${result.employee_id}</td>
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
