// Filters - Apply filters to risk table

function applyFilters() {
    const severityFilter = document.getElementById('severity-filter').value;
    const entityFilter = document.getElementById('entity-filter').value;
    const timingFilter = document.getElementById('timing-filter').value;
    const intentFilter = document.getElementById('intent-filter').value;
    
    const riskItems = document.querySelectorAll('.risk-item');
    
    riskItems.forEach(item => {
        const severity = item.dataset.severity;
        const entity = item.dataset.entity;
        const timing = item.dataset.timing;
        const intent = item.dataset.intent;
        
        const severityMatch = severityFilter === 'all' || severity === severityFilter;
        const entityMatch = entityFilter === 'all' || entity === entityFilter;
        const timingMatch = timingFilter === 'all' || timing === timingFilter;
        const intentMatch = intentFilter === 'all' || intent === intentFilter;
        
        if (severityMatch && entityMatch && timingMatch && intentMatch) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
    
    updateVisibility();
}

function updateVisibility() {
    // Check subdomains
    document.querySelectorAll('.subdomain-block').forEach(subdomain => {
        const visibleRisks = subdomain.querySelectorAll('.risk-item[style="display: block;"], .risk-item:not([style*="display: none"])');
        if (visibleRisks.length === 0) {
            subdomain.style.display = 'none';
        } else {
            subdomain.style.display = 'block';
        }
    });
    
    // Check domains
    document.querySelectorAll('.domain-block').forEach(domain => {
        const visibleSubdomains = domain.querySelectorAll('.subdomain-block[style="display: block;"], .subdomain-block:not([style*="display: none"])');
        if (visibleSubdomains.length === 0) {
            domain.style.display = 'none';
        } else {
            domain.style.display = 'block';
        }
    });
}
