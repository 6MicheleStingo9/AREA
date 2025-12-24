// Charts Configuration - Plotly visualizations

// 1. Risk Distribution by Domain (Stacked Bar Chart)
// Map domain acronyms (D1..D7) to localized full names using translations (d1_title..d7_title)
const mappedDomainNames = chartData.risk_distribution.domains.map((d, i) => {
    const id = d.replace(/^D/i, '');
    return translations['d' + id + '_title'] || chartData.risk_distribution.domain_names[i];
});

const riskDistData = [
    {
        x: chartData.risk_distribution.domains,
        y: chartData.risk_distribution.high,
        name: translations.high || 'HIGH',
        type: 'bar',
        marker: {color: '#DC2626'},
        customdata: mappedDomainNames,
        hovertemplate: '<b>%{customdata}</b><br>' + (translations.high || 'HIGH') + ': %{y}<extra></extra>'
    },
    {
        x: chartData.risk_distribution.domains,
        y: chartData.risk_distribution.medium,
        name: translations.medium || 'MEDIUM',
        type: 'bar',
        marker: {color: '#F59E0B'},
        customdata: mappedDomainNames,
        hovertemplate: '<b>%{customdata}</b><br>' + (translations.medium || 'MEDIUM') + ': %{y}<extra></extra>'
    },
    {
        x: chartData.risk_distribution.domains,
        y: chartData.risk_distribution.low,
        name: translations.low || 'LOW',
        type: 'bar',
        marker: {color: '#10B981'},
        customdata: mappedDomainNames,
        hovertemplate: '<b>%{customdata}</b><br>' + (translations.low || 'LOW') + ': %{y}<extra></extra>'
    }
];

const riskDistLayout = {
    barmode: 'stack',
    xaxis: {
        title: translations.domains || 'Domains'
    },
    yaxis: {
        title: translations.chart_risks_label || 'Number of Risks',
        gridcolor: '#E5E7EB'
    },
    margin: {l: 60, r: 40, t: 60, b: 80},
    plot_bgcolor: '#FAFAFA',
    paper_bgcolor: 'white',
    font: {family: 'inherit', size: 12},
    showlegend: false
};

Plotly.newPlot('risk-distribution-chart', riskDistData, riskDistLayout, {responsive: true});

// 2. Alert Criticality Radar Chart (Dual Profile: Criticality + Safety)
// Convert categorical labels to numeric theta (degrees), build a common axis set
const _mapCritical = {
    'Risk Concentration': translations.risk_concentration || 'Risk Concentration',
    'Operational Exposure': translations.operational_exposure || 'Operational Exposure',
    'Threat Intensity': translations.threat_intensity || 'Threat Intensity',
    'Prevention Deficit': translations.prevention_deficit || 'Prevention Deficit'
};
const _mapSafety = {
    'Impact Control': translations.impact_control || 'Impact Control',
    'Preventability': translations.preventability || 'Preventability',
    'Safety Culture': translations.safety_culture || 'Safety Culture',
    'Human Oversight': translations.human_oversight || 'Human Oversight'
};

const criticalLabels = chartData.alert_criticality.labels.map(l => _mapCritical[l] || l);
const safetyLabels = chartData.alert_criticality.safety_labels.map(l => _mapSafety[l] || l);

// Unified label set (preserve order, avoid duplicates)
const unifiedLabels = [];
[...criticalLabels, ...safetyLabels].forEach(l => { if (unifiedLabels.indexOf(l) === -1) unifiedLabels.push(l); });
const Naxes = unifiedLabels.length || 1;
const thetaVals = unifiedLabels.map((_, i) => i * 360 / Naxes);

function alignValues(sourceLabels, sourceValues) {
    const map = {};
    if (Array.isArray(sourceLabels) && Array.isArray(sourceValues)) {
        sourceLabels.forEach((lab, idx) => { map[lab] = sourceValues[idx] != null ? sourceValues[idx] : 0; });
    }
    return unifiedLabels.map(l => map[l] != null ? map[l] : 0);
}

const criticalR = alignValues(criticalLabels, chartData.alert_criticality.criticality_values);
const safetyR = alignValues(safetyLabels, chartData.alert_criticality.safety_values);

const alertRadarData = [
    {
        type: 'scatterpolar',
        r: criticalR,
        theta: thetaVals,
        text: unifiedLabels,
        fill: 'toself',
        fillcolor: 'rgba(239, 68, 68, 0.35)',
        line: { color: 'rgba(0,0,0,0)', width: 0 },
        marker: { color: '#DC2626', size: 0 },
        name: translations.criticality || 'Alert Criticality',
        hovertemplate: '<b>%{text}</b><br>%{r:.1f}%<extra>' + (translations.criticality || 'Alert Criticality') + '</extra>'
    },
    {
        type: 'scatterpolar',
        r: safetyR,
        theta: thetaVals,
        text: unifiedLabels,
        fill: 'toself',
        fillcolor: 'rgba(16, 185, 129, 0.35)',
        line: { color: 'rgba(0,0,0,0)', width: 0 },
        marker: { color: '#10B981', size: 0 },
        name: translations.safety || 'System Safety',
        hovertemplate: '<b>%{text}</b><br>%{r:.1f}%<extra>' + (translations.safety || 'System Safety') + '</extra>'
    }
];

const alertRadarLayout = {
    polar: {
        radialaxis: {
            visible: true,
            range: [0, 100],
            gridcolor: '#E5E7EB',
            ticksuffix: '%',
            tickfont: {size: 10}
        },
        angularaxis: {
            gridcolor: '#E5E7EB',
            tickfont: {size: 11},
            tickmode: 'array',
            tickvals: thetaVals,
            ticktext: unifiedLabels
        }
    },
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    font: {family: 'inherit', size: 11},
    showlegend: true,
    legend: {
        x: 0.5,
        y: -0.15,
        xanchor: 'center',
        yanchor: 'top',
        orientation: 'h',
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        bordercolor: '#E5E7EB',
        borderwidth: 1
    },
    margin: {l: 80, r: 80, t: 40, b: 100}
};

Plotly.newPlot('alert-criticality-chart', alertRadarData, alertRadarLayout, {responsive: true});

// 4. Causality Flow Sankey Diagram
const sankeyData = [{
    type: 'sankey',
    orientation: 'h',
    node: {
        pad: 15,
        thickness: 20,
        line: {
            color: 'white',
            width: 1
        },
        label: chartData.causality_sankey.nodes.map(n => {
            const map = {
                'AI': translations.entity_ai || 'AI',
                'Human': translations.entity_human || 'Human',
                'Other': translations.entity_other || 'Other',
                'Intentional': translations.intent_intentional || 'Intentional',
                'Unintentional': translations.intent_unintentional || 'Unintentional',
                'Other Intent': translations.intent_other || 'Other Intent',
                'Pre-deployment': translations.timing_pre_deployment || 'Pre-deployment',
                'Post-deployment': translations.timing_post_deployment || 'Post-deployment',
                'Other Timing': translations.timing_other || 'Other Timing'
            };
            return map[n] || n;
        }),
        color: [
            '#3B82F6', '#3B82F6', '#94A3B8',  // Entity: blue tones
            '#F59E0B', '#F59E0B', '#94A3B8',  // Intent: amber tones
            '#14B8A6', '#DC2626', '#94A3B8'   // Timing: teal (pre), red (post), gray (other)
        ],
        customdata: chartData.causality_sankey.nodes.map((node, i) => {
            if (i <= 2) return translations.causality_entity_label || 'Entity';
            if (i <= 5) return translations.causality_intent_label || 'Intent';
            return translations.causality_timing_label || 'Timing';
        }),
        hovertemplate: '<b>%{label}</b><br>' + (translations.category_label || 'Category') + ': %{customdata}<br>' + (translations.chart_risks_label || 'Risks') + ': %{value:d}<extra></extra>'
    },
    link: {
        source: chartData.causality_sankey.sources,
        target: chartData.causality_sankey.targets,
        value: chartData.causality_sankey.values.map(v => Math.round(v)),
        color: 'rgba(0,0,0,0.2)',
        hovertemplate: '%{source.label} → %{target.label}<br>' + (translations.chart_risks_label || 'Risks') + ': %{value:d}<extra></extra>'
    }
}];

const sankeyLayout = {
    font: {family: 'inherit', size: 12},
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    margin: {l: 10, r: 10, t: 10, b: 10}
};

Plotly.newPlot('causality-sankey-chart', sankeyData, sankeyLayout, {responsive: true});

// 3. Patterns Heatmap
const heatmapData = [{
    z: chartData.patterns_heatmap.values,
    x: chartData.patterns_heatmap.patterns,
    y: chartData.patterns_heatmap.categories,
    type: 'heatmap',
    colorscale: [
        [0, '#EFF6FF'],
        [0.3, '#BFDBFE'],
        [0.6, '#60A5FA'],
        [1, '#1E40AF']
    ],
    hovertemplate: '<b>%{y}</b><br>%{x}<br>' + (translations.chart_risks_label || 'Risks') + ': %{z}<extra></extra>',
    colorbar: {
        title: translations.chart_risks_label || 'Risks',
        titleside: 'right',
        tickmode: 'linear',
        tick0: 0
    }
}];

const heatmapLayout = {
    xaxis: {
        title: translations.pattern_type_label || 'Pattern Type',
        tickangle: -45,
        automargin: true
    },
    yaxis: {
        title: translations.category_label || 'Category',
        automargin: true
    },
    margin: {l: 120, r: 100, t: 80, b: 150},
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    font: {family: 'inherit', size: 11}
};

Plotly.newPlot('patterns-heatmap', heatmapData, heatmapLayout, {responsive: true});
