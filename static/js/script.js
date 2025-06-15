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
    
    // Mobile/touch device detection
    const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    const isMobile = window.innerWidth <= 768;
    
    // Initialize mobile optimizations
    initializeMobileOptimizations();

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
            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                <table class="table table-striped table-hover table-sm">
                    <thead class="sticky-top bg-dark">
                        <tr>
                            <th>Seniority #</th>
                            <th>Employee ID</th>
                            <th>Employee Name</th>
                            <th>Awarded Line</th>
                            <th>Choice Position</th>
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
            const displaySeniorityNumber = result.bid_position;
            
            // Format choice position display
            let choiceDisplay = '-';
            if (result.choice_position) {
                choiceDisplay = result.choice_position;
            } else if (result.message && result.message.includes("No preferred lines available")) {
                choiceDisplay = 'Insufficient Bids';
            }
            
            tableHtml += `
                <tr class="${rowClass}">
                    <td>${displaySeniorityNumber}</td>
                    <td>${result.employee_id}</td>
                    <td>${result.employee_name || ''}</td>
                    <td>${result.awarded_line || '-'}</td>
                    <td class="text-info fw-bold">${choiceDisplay}</td>
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
        
        // Apply mobile optimizations to the new table if needed
        if (isMobile) {
            optimizeTableForMobile();
        }
    }
    
    // Mobile optimization functions
    function initializeMobileOptimizations() {
        // Auto-resize textarea on mobile
        if (isMobile) {
            bidData.addEventListener('focus', () => {
                setTimeout(() => {
                    bidData.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            });
        }
        
        // Add touch feedback for buttons
        if (isTouchDevice) {
            [submitBtn, resetBtn, downloadBtn].forEach(btn => {
                if (btn) {
                    btn.addEventListener('touchstart', function() {
                        this.style.transform = 'scale(0.95)';
                    }, { passive: true });
                    
                    btn.addEventListener('touchend', function() {
                        setTimeout(() => {
                            this.style.transform = '';
                        }, 100);
                    }, { passive: true });
                }
            });
        }
        
        // Optimize form validation for mobile
        bidData.addEventListener('blur', () => {
            if (bidData.value.trim().length > 0) {
                bidData.setCustomValidity('');
            }
        });
        
        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                adjustLayoutForOrientation();
            }, 100);
        });
        
        // Handle window resize for responsive behavior
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                handleWindowResize();
            }, 250);
        });
    }
    
    function optimizeTableForMobile() {
        const tableResponsive = resultsContainer.querySelector('.table-responsive');
        if (tableResponsive && isMobile) {
            // Add horizontal scroll hint for mobile
            tableResponsive.style.position = 'relative';
            
            // Add scroll indicators if content overflows
            const table = tableResponsive.querySelector('table');
            if (table && table.scrollWidth > tableResponsive.clientWidth) {
                tableResponsive.style.background = 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1) 100%)';
            }
        }
    }
    
    function adjustLayoutForOrientation() {
        // Adjust table height based on orientation
        const tableResponsive = resultsContainer.querySelector('.table-responsive');
        if (tableResponsive) {
            const isLandscape = window.innerHeight < window.innerWidth;
            if (isMobile) {
                tableResponsive.style.maxHeight = isLandscape ? '40vh' : '50vh';
            }
        }
    }
    
    function handleWindowResize() {
        const newIsMobile = window.innerWidth <= 768;
        
        // Re-optimize table if switching to/from mobile
        if (newIsMobile !== isMobile && currentResults.length > 0) {
            displayResults(currentResults);
        }
        
        // Update mobile status
        window.isMobile = newIsMobile;
    }
    
    // Enhanced error handling for mobile
    function showMobileOptimizedError(message) {
        errorMessage.textContent = message;
        errorAlert.classList.remove('d-none');
        
        // Scroll to error on mobile
        if (isMobile) {
            errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    // Prevent zoom on double-tap for iOS Safari
    if (isTouchDevice) {
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    // Add keyboard support for mobile users
    bidData.addEventListener('keydown', (e) => {
        // Allow Ctrl+A, Ctrl+V, Ctrl+C on mobile keyboards
        if (e.ctrlKey || e.metaKey) {
            if (['a', 'v', 'c', 'x', 'z'].includes(e.key.toLowerCase())) {
                // Let these through
                return;
            }
        }
    });
    
    // Smooth scrolling for mobile navigation
    function scrollToResults() {
        if (isMobile && currentResults.length > 0) {
            resultsContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start',
                inline: 'nearest'
            });
        }
    }
    
    // Update the form submission to include mobile scroll
    const originalDisplayResults = displayResults;
    displayResults = function(results) {
        originalDisplayResults(results);
        setTimeout(scrollToResults, 100);
    };
});
