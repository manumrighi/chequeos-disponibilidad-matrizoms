// Dashboard-specific functionality

class Dashboard {
    constructor() {
        this.checkResults = {};
        this.isRunningChecks = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadLastCheckTime();
        this.initializeCheckCards();
    }

    setupEventListeners() {
        // Run all checks button
        const runAllButton = document.getElementById('run-all-checks');
        if (runAllButton) {
            runAllButton.addEventListener('click', () => this.runAllChecks());
        }

        // Refresh status button
        const refreshButton = document.getElementById('refresh-status');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.refreshStatus());
        }

        // Individual check buttons
        document.querySelectorAll('.run-check').forEach(button => {
            button.addEventListener('click', (e) => {
                const endpoint = e.target.closest('.run-check').dataset.endpoint;
                const checkName = e.target.closest('.monitoring-card').dataset.check;
                this.runSingleCheck(endpoint, checkName, e.target);
            });
        });

        // View logs buttons
        document.querySelectorAll('.view-logs').forEach(button => {
            button.addEventListener('click', (e) => {
                const checkName = e.target.closest('.view-logs').dataset.check;
                this.showResults(checkName);
            });
        });

        // Close results modal
        const closeResultsButton = document.getElementById('close-results');
        if (closeResultsButton) {
            closeResultsButton.addEventListener('click', () => {
                app.closeModal('results-modal');
            });
        }
    }

    initializeCheckCards() {
        // Add hover effects and initial animations
        const cards = document.querySelectorAll('.monitoring-card');
        cards.forEach((card, index) => {
            // Stagger the initial animation
            card.style.animationDelay = `${index * 100}ms`;
            card.classList.add('fade-in-on-scroll');
        });
    }

    async runAllChecks() {
        if (this.isRunningChecks) {
            app.showToast('Ya hay chequeos ejecutándose', 'warning');
            return;
        }

        this.isRunningChecks = true;
        app.showModal('loading-modal');
        
        const checks = [
            { endpoint: '/check-admin', name: 'admin', display: 'Admin' },
            { endpoint: '/check-nodes', name: 'nodes', display: 'Nodes' },
            { endpoint: '/check-sessions', name: 'sessions', display: 'Sesiones' },
            { endpoint: '/check-matriz', name: 'matriz', display: 'Matriz' },
            { endpoint: '/check-etrader', name: 'etrader', display: 'eTrader' },
            { endpoint: '/check-webService', name: 'webservice', display: 'Web Service' },
            { endpoint: '/check-accountReport', name: 'account', display: 'Account Report' }
        ];

        const totalChecks = checks.length;
        let completedChecks = 0;

        // Update progress
        const updateProgress = () => {
            const percentage = (completedChecks / totalChecks) * 100;
            app.updateProgress('progress-fill', percentage);
        };

        const updateLoadingMessage = (message) => {
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) {
                loadingMessage.textContent = message;
            }
        };

        try {
            updateLoadingMessage('Iniciando verificaciones...');
            updateProgress();

            // Run checks sequentially to avoid overwhelming the server
            for (const check of checks) {
                updateLoadingMessage(`Ejecutando ${check.display}...`);
                app.updateStatusIndicator(`status-${check.name}`, 'running', 'Ejecutando...');

                try {
                    const result = await app.makeRequest(check.endpoint);
                    this.checkResults[check.name] = {
                        ...result,
                        timestamp: new Date().toISOString(),
                        checkName: check.display
                    };
                    
                    app.updateStatusIndicator(`status-${check.name}`, 'success', 'Completado');
                    app.showToast(`${check.display} completado exitosamente`, 'success', 3000);
                } catch (error) {
                    console.error(`Error in ${check.name}:`, error);
                    this.checkResults[check.name] = {
                        error: error.message,
                        timestamp: new Date().toISOString(),
                        checkName: check.display
                    };
                    app.updateStatusIndicator(`status-${check.name}`, 'error', 'Error');
                    app.showToast(`Error en ${check.display}: ${error.message}`, 'error', 5000);
                }

                completedChecks++;
                updateProgress();
                
                // Small delay between checks
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            updateLoadingMessage('Todos los chequeos completados');
            this.saveLastCheckTime();
            
            // Show completion toast
            app.showToast('Todos los chequeos han sido completados', 'success');
            
            // Close loading modal after a brief delay
            setTimeout(() => {
                app.closeModal('loading-modal');
            }, 1500);

        } catch (error) {
            console.error('Error during bulk check execution:', error);
            app.showToast('Error durante la ejecución de chequeos', 'error');
            app.closeModal('loading-modal');
        } finally {
            this.isRunningChecks = false;
        }
    }

    async runSingleCheck(endpoint, checkName, button) {
        if (this.isRunningChecks) {
            app.showToast('Ya hay chequeos ejecutándose', 'warning');
            return;
        }

        const originalIcon = button.querySelector('i').className;
        
        try {
            app.setLoadingState(button, true);
            app.updateStatusIndicator(`status-${checkName}`, 'running', 'Ejecutando...');

            const result = await app.makeRequest(endpoint);
            
            this.checkResults[checkName] = {
                ...result,
                timestamp: new Date().toISOString(),
                checkName: this.getDisplayName(checkName)
            };

            app.updateStatusIndicator(`status-${checkName}`, 'success', 'Completado');
            app.showToast(`${this.getDisplayName(checkName)} completado exitosamente`, 'success');
            
            // Show results immediately
            this.showResults(checkName);

        } catch (error) {
            console.error(`Error in ${checkName}:`, error);
            this.checkResults[checkName] = {
                error: error.message,
                timestamp: new Date().toISOString(),
                checkName: this.getDisplayName(checkName)
            };
            app.updateStatusIndicator(`status-${checkName}`, 'error', 'Error');
            app.showToast(`Error en ${this.getDisplayName(checkName)}: ${error.message}`, 'error');
        } finally {
            app.setLoadingState(button, false);
            // Restore original icon
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = originalIcon;
            }
        }
    }

    async runAvailabilityCheck() {
        try {
            app.showModal('loading-modal');
            document.getElementById('loading-message').textContent = 'Ejecutando chequeo de disponibilidad...';
            
            const result = await app.makeRequest('/check-disponibility');
            
            this.checkResults['disponibility'] = {
                ...result,
                timestamp: new Date().toISOString(),
                checkName: 'Disponibilidad General'
            };

            app.closeModal('loading-modal');
            this.showResults('disponibility');
            app.showToast('Chequeo de disponibilidad completado', 'success');

        } catch (error) {
            console.error('Error in availability check:', error);
            app.closeModal('loading-modal');
            app.showToast(`Error en chequeo de disponibilidad: ${error.message}`, 'error');
        }
    }

    showResults(checkName) {
        const result = this.checkResults[checkName];
        if (!result) {
            app.showToast('No hay resultados disponibles para este chequeo', 'warning');
            return;
        }

        const resultsContent = document.getElementById('results-content');
        if (!resultsContent) return;

        let html = `
            <div class="results-header">
                <h4>${result.checkName}</h4>
                <p class="results-timestamp">
                    <i class="fas fa-clock"></i>
                    Ejecutado: ${app.formatDate(result.timestamp)}
                </p>
            </div>
        `;

        if (result.error) {
            html += `
                <div class="results-error">
                    <i class="fas fa-exclamation-circle"></i>
                    <h5>Error</h5>
                    <p>${result.error}</p>
                </div>
            `;
        } else {
            html += `
                <div class="results-success">
                    <div class="results-summary">
                        <div class="summary-item">
                            <i class="fas fa-check-circle"></i>
                            <span>Estado: Exitoso</span>
                        </div>
                        <div class="summary-item">
                            <i class="fas fa-database"></i>
                            <span>Logs insertados: ${result.inserted_logs || 0}</span>
                        </div>
                        <div class="summary-item">
                            <i class="fas fa-server"></i>
                            <span>Status: ${result.status || 'ok'}</span>
                        </div>
                    </div>
                </div>
            `;

            // If it's the availability check, show detailed results
            if (checkName === 'disponibility' && typeof result === 'object') {
                html += '<div class="detailed-results">';
                html += '<h5>Resultados Detallados:</h5>';
                
                Object.entries(result).forEach(([service, serviceResult]) => {
                    if (service !== 'timestamp' && service !== 'checkName') {
                        const isSuccess = !serviceResult.error;
                        html += `
                            <div class="service-result ${isSuccess ? 'success' : 'error'}">
                                <div class="service-header">
                                    <i class="fas ${isSuccess ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
                                    <strong>${service.charAt(0).toUpperCase() + service.slice(1)}</strong>
                                </div>
                                <div class="service-details">
                                    <p>Logs insertados: ${serviceResult.inserted_logs || 0}</p>
                                    <p>Status: ${serviceResult.status || 'N/A'}</p>
                                    ${serviceResult.error ? `<p class="error-text">Error: ${serviceResult.error}</p>` : ''}
                                </div>
                            </div>
                        `;
                    }
                });
                html += '</div>';
            }
        }

        resultsContent.innerHTML = html;
        app.showModal('results-modal');
    }

    refreshStatus() {
        // Reset all status indicators to pending
        const statusElements = document.querySelectorAll('[id^="status-"]');
        statusElements.forEach(element => {
            app.updateStatusIndicator(element.id, 'pending', 'Pendiente');
        });

        // Clear stored results
        this.checkResults = {};
        
        app.showToast('Estado actualizado', 'info');
    }

    getDisplayName(checkName) {
        const displayNames = {
            'admin': 'Admin',
            'nodes': 'Nodes',
            'sessions': 'Sesiones',
            'matriz': 'Matriz',
            'etrader': 'eTrader',
            'webservice': 'Web Service',
            'account': 'Account Report'
        };
        return displayNames[checkName] || checkName;
    }

    saveLastCheckTime() {
        const now = new Date().toISOString();
        app.saveToStorage('last-check-time', now);
        this.updateLastCheckDisplay(now);
    }

    loadLastCheckTime() {
        const lastCheck = app.loadFromStorage('last-check-time');
        if (lastCheck) {
            this.updateLastCheckDisplay(lastCheck);
        }
    }

    updateLastCheckDisplay(timestamp) {
        const element = document.getElementById('last-check');
        if (element && timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diffInMinutes = Math.floor((now - date) / (1000 * 60));
            
            if (diffInMinutes < 1) {
                element.textContent = 'Ahora';
            } else if (diffInMinutes < 60) {
                element.textContent = `${diffInMinutes}m`;
            } else if (diffInMinutes < 1440) {
                element.textContent = `${Math.floor(diffInMinutes / 60)}h`;
            } else {
                element.textContent = app.formatDate(timestamp).split(' ')[1]; // Just time
            }
        }
    }

    // Auto-refresh last check time every minute
    startAutoRefresh() {
        setInterval(() => {
            const lastCheck = app.loadFromStorage('last-check-time');
            if (lastCheck) {
                this.updateLastCheckDisplay(lastCheck);
            }
        }, 60000); // Update every minute
    }
}

// Additional CSS for results modal
const dashboardStyles = document.createElement('style');
dashboardStyles.textContent = `
    .results-header {
        text-align: left;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .results-header h4 {
        color: white;
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    
    .results-timestamp {
        color: var(--gray-300);
        font-size: 0.875rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .results-error {
        background: rgba(220, 53, 69, 0.1);
        border: 1px solid var(--danger);
        border-radius: var(--border-radius);
        padding: 1rem;
        text-align: left;
    }
    
    .results-error i {
        color: var(--danger);
        font-size: 1.25rem;
        margin-right: 0.5rem;
    }
    
    .results-error h5 {
        color: var(--danger);
        margin: 0.5rem 0;
    }
    
    .results-success {
        text-align: left;
    }
    
    .results-summary {
        background: rgba(40, 167, 69, 0.1);
        border: 1px solid var(--success);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .summary-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        color: var(--gray-200);
    }
    
    .summary-item:last-child {
        margin-bottom: 0;
    }
    
    .summary-item i {
        color: var(--success);
        width: 20px;
    }
    
    .detailed-results {
        margin-top: 1.5rem;
    }
    
    .detailed-results h5 {
        color: white;
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    
    .service-result {
        border-radius: var(--border-radius);
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid;
    }
    
    .service-result.success {
        background: rgba(40, 167, 69, 0.1);
        border-color: var(--success);
    }
    
    .service-result.error {
        background: rgba(220, 53, 69, 0.1);
        border-color: var(--danger);
    }
    
    .service-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .service-header i {
        font-size: 1rem;
    }
    
    .service-result.success .service-header i {
        color: var(--success);
    }
    
    .service-result.error .service-header i {
        color: var(--danger);
    }
    
    .service-details p {
        margin: 0.25rem 0;
        font-size: 0.875rem;
        color: var(--gray-300);
    }
    
    .error-text {
        color: var(--danger) !important;
        font-weight: 500;
    }
`;
document.head.appendChild(dashboardStyles);

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.dashboard-container')) {
        window.dashboard = new Dashboard();
        dashboard.startAutoRefresh();
    }
}); 