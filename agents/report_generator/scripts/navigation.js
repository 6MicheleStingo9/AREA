// Navigation - Toggle functions for hierarchical tree

function toggleDomain(header) {
    const content = header.nextElementSibling;
    const isCollapsed = header.classList.contains('collapsed');
    
    if (isCollapsed) {
        header.classList.remove('collapsed');
        content.style.display = 'block';
    } else {
        header.classList.add('collapsed');
        content.style.display = 'none';
    }
}

function togglePatternInfo() {
    const infoBox = document.getElementById('pattern-info');
    infoBox.classList.toggle('collapsed');
}

function toggleDomainInfo() {
    const infoBox = document.getElementById('domain-info');
    infoBox.classList.toggle('collapsed');
}

function toggleAlertInfo() {
    const infoBox = document.getElementById('alert-info');
    infoBox.classList.toggle('collapsed');
}

function toggleSankeyInfo() {
    const infoBox = document.getElementById('sankey-info');
    infoBox.classList.toggle('collapsed');
}

function toggleSubdomain(header) {
    const content = header.nextElementSibling;
    const isCollapsed = header.classList.contains('collapsed');
    
    if (isCollapsed) {
        header.classList.remove('collapsed');
        content.style.display = 'block';
    } else {
        header.classList.add('collapsed');
        content.style.display = 'none';
    }
}

function toggleRiskDetails(item) {
    const details = item.querySelector('.risk-details');
    details.classList.toggle('expanded');
}
