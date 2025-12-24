% ============================================================================
% AI RISK ANALYSIS - PROLOG KNOWLEDGE BASE
% ============================================================================
% This Prolog knowledge base implements heuristic analysis for AI risk assessment
% based on MIT AI Risk Repository taxonomy. It processes risk data with causality
% attributes (Entity, Intent, Timing) to compute risk scores, identify patterns,
% and provide actionable insights.
%
% Dynamic Facts (asserted at runtime from JSON analysis):
% - domain/2: domain(DomainID, DomainName)
% - subdomain/3: subdomain(DomainID, SubdomainID, SubdomainName)
% - risk/5: risk(Domain, Subdomain, RiskID, Title, Severity)
% - causality_entity/4: causality_entity(Domain, Subdomain, RiskID, Entity)
%   Entity ∈ {ai, human, other}
% - causality_intent/4: causality_intent(Domain, Subdomain, RiskID, Intent)
%   Intent ∈ {intentional, unintentional, other}
% - causality_timing/4: causality_timing(Domain, Subdomain, RiskID, Timing)
%   Timing ∈ {pre-deployment, post-deployment, other}
%
% TODO: Add support for risk mitigation strategies tracking
% TODO: Implement temporal evolution analysis (risk trends over time)
% TODO: Add risk interdependency graph analysis
% TODO: Support for custom risk weighting schemes
% TODO: Implement risk cascade simulation (domino effects)
% ============================================================================

:- dynamic domain/2.
:- dynamic subdomain/3.
:- dynamic risk/5.
:- dynamic causality_entity/4.
:- dynamic causality_intent/4.
:- dynamic causality_timing/4.
:- dynamic risks_in_domain_by_severity/3.
:- dynamic risks_by_severity/2.
:- dynamic global_risk_score/1.
:- dynamic percentage_high_severity/1.


% ============================================================================
% EXECUTIVE SUMMARY - High-Level Risk Metrics
% ============================================================================
% This section provides top-level insights for decision makers: global risk score,
% overall risk level classification, primary concerns, recommended actions, and
% identification of the most critical domains requiring immediate attention.
%
% TODO: Add confidence intervals for risk scores
% TODO: Implement risk velocity metric (rate of risk accumulation)
% TODO: Add comparative benchmarking against industry standards
% TODO: Support for multi-scenario risk scoring (best/worst case)
% TODO: Implement executive dashboard data export format
% ============================================================================

% Global risk score (0-100) weighted by severity: HIGH=10, MEDIUM=5, LOW=1
% Provides a normalized metric for overall system risk level.
global_risk_score(Score) :-
	risks_by_severity(high, H),
	risks_by_severity(medium, M),
	risks_by_severity(low, L),
	total_risks(Total),
	Total > 0,
	WeightedScore is (H*10 + M*5 + L*1),
	MaxPossible is Total*10,
	Score is (WeightedScore*100.0)/MaxPossible.

% Overall risk level classification (critical/high/medium/low)
% Maps numeric score to qualitative risk bands for easier communication.
overall_risk_level(Level) :-
	global_risk_score(Score),
	(Score >= 75 ->
	Level = critical;
	Score >= 50 ->
	Level = high;
	Score >= 25 ->
	Level = medium;
	Level = low).

% Primary concern identification - what is the main problem requiring attention?
% Returns: high_concentration, ai_dominance, active_threats, operational_issues,
% severity_issues, or manageable.
primary_concern(Concern) :-
	(has_critical_risk_concentration ->
	Concern = 'high_concentration';
	has_ai_dominance ->
	Concern = 'ai_dominance';
	has_intentional_threats ->
	Concern = 'active_threats';
	has_operational_risks ->
	Concern = 'operational_issues';
	percentage_high_severity(P),
		P > 30 ->
	Concern = 'severity_issues';
	Concern = 'manageable').

% Recommended primary action based on risk profile
% Returns: focus_prevention, immediate_mitigation, strengthen_predeployment,
% or monitor_and_maintain.
recommended_action(Action) :-
	(preventable_high_risks_count(C),
		C > 0 ->
	Action = 'focus_prevention';
	immediate_action_required_count(C2),
		C2 > 0 ->
	Action = 'immediate_mitigation';
	has_high_preventable_ratio ->
	Action = 'strengthen_predeployment';
	Action = 'monitor_and_maintain').

% Top 3 most critical domains ranked by HIGH severity risk count
% Enables prioritization of remediation efforts across domains.
critical_domain_ranked(Rank, Domain, DomainName, Count) :-
	findall(C - D - N,
		(domain(D, N),
			risks_in_domain_by_severity(D, high, C),
			C > 0),
		Pairs),
	sort(0, @>= , Pairs, Sorted),
	nth1(Rank, Sorted, Count - Domain  - DomainName).

% Single most critical domain (convenience predicate for rank 1)
most_critical_domain(Domain, DomainName, HighCount) :-
	critical_domain_ranked(1, Domain, DomainName, HighCount).

% ============================================================================
% BASIC COUNTING RULES
% ============================================================================
% Fundamental counting predicates for risk aggregation across multiple dimensions:
% domains, subdomains, severity levels, and causality attributes.
%
% TODO: Add time-window based counting (risks detected in last N days)
% TODO: Implement weighted counting (by severity or business impact)
% TODO: Add counting by risk source/origin
% TODO: Support for custom risk grouping taxonomies
% TODO: Implement counting with confidence thresholds
% ============================================================================

% Count total number of risks in the system
total_risks(Count) :-
	findall(R,
		risk(_, _, R, _, _),
		Risks),
	length(Risks, Count).

% Count risks within a specific primary domain
risks_in_domain(Domain, Count) :-
	findall(R,
		risk(Domain, _, R, _, _),
		Risks),
	length(Risks, Count).

% Count risks within a domain filtered by severity level
risks_in_domain_by_severity(Domain, Severity, Count) :-
	domain(Domain, _),
	findall(R,
		risk(Domain, _, R, _, Severity),
		Risks),
	length(Risks, Count).

% Count risks within a specific subdomain
risks_in_subdomain(Domain, SubDomain, Count) :-
	findall(R,
		risk(Domain, SubDomain, R, _, _),
		Risks),
	length(Risks, Count).

% Count risks by severity level (high/medium/low)
risks_by_severity(Severity, Count) :-
	findall(R,
		risk(_, _, R, _, Severity),
		Risks),
	length(Risks, Count).

% Count risks by causality entity (ai/human/other)
risks_by_entity(Entity, Count) :-
	findall(R,
		causality_entity(_, _, R, Entity),
		Risks),
	length(Risks, Count).

% Count risks by causality intent (intentional/unintentional/other)
risks_by_intent(Intent, Count) :-
	findall(R,
		causality_intent(_, _, R, Intent),
		Risks),
	length(Risks, Count).

% Count risks by causality timing (pre-deployment/post-deployment/other)
risks_by_timing(Timing, Count) :-
	findall(R,
		causality_timing(_, _, R, Timing),
		Risks),
	length(Risks, Count).

% ============================================================================
% CRITICAL PATTERNS - High-Risk Combinations
% ============================================================================
% Identifies dangerous combinations of risk attributes that require immediate
% attention. These patterns combine severity, causality entity, intent, and timing
% to highlight the most concerning scenarios (e.g., high-severity AI risks already
% in production, intentional human attacks, systemic AI failures).
%
% TODO: Add pattern confidence scoring
% TODO: Implement dynamic pattern learning from historical incidents
% TODO: Support for custom pattern definitions via external configuration
% TODO: Add pattern evolution tracking over time
% TODO: Implement pattern correlation analysis (co-occurrence patterns)
% ============================================================================

% Pattern 1: HIGH severity risks caused by AI in post-deployment
% Most dangerous scenario: critical AI-driven risks already operational in production.
% These require immediate mitigation as they represent active systemic threats.
critical_ai_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, high),
	causality_entity(Domain, SubDomain, RiskId, ai),
	causality_timing(Domain, SubDomain, RiskId, 'post-deployment').

critical_ai_risks_count(Count) :-
	findall(R,
		critical_ai_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% Pattern 2: Intentional attacks from human actors (active threats)
% Identifies malicious behavior including sabotage, fraud, and targeted manipulation.
% These risks indicate adversarial actions requiring security response.
malicious_human_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, _),
	causality_entity(Domain, SubDomain, RiskId, human),
	causality_intent(Domain, SubDomain, RiskId, intentional).

malicious_human_risks_count(Count) :-
	findall(R,
		malicious_human_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% Pattern 3: HIGH + HUMAN + INTENTIONAL (sabotage/targeted attacks)
% Triple-threat pattern: severe risks from deliberate human malicious activity.
% Represents the most dangerous human-driven threat scenario.
high_threat_attacks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, high),
	causality_entity(Domain, SubDomain, RiskId, human),
	causality_intent(Domain, SubDomain, RiskId, intentional).

high_threat_attacks_count(Count) :-
	findall(R,
		high_threat_attacks(_, _, R, _),
		Risks),
	length(Risks, Count).

% Pattern 4: Unintended AI system failures in post-deployment
% Systemic AI errors already in production - not malicious but still dangerous.
% Indicates issues with robustness, testing, or capability limitations.
unintended_ai_failures(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, _),
	causality_entity(Domain, SubDomain, RiskId, ai),
	causality_intent(Domain, SubDomain, RiskId, unintentional),
	causality_timing(Domain, SubDomain, RiskId, 'post-deployment').

unintended_ai_failures_count(Count) :-
	findall(R,
		unintended_ai_failures(_, _, R, _),
		Risks),
	length(Risks, Count).

% Pattern 5: Unintentional human errors (misuse/negligence)
% User mistakes, lack of training, or improper use of AI systems.
% Addressable through better UX design, training, and safety guardrails.
human_error_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, _),
	causality_entity(Domain, SubDomain, RiskId, human),
	causality_intent(Domain, SubDomain, RiskId, unintentional).

human_error_risks_count(Count) :-
	findall(R,
		human_error_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% ============================================================================
% TIMING PATTERNS - Risk Phase Analysis
% ============================================================================
% Analyzes risks based on deployment phase to prioritize preventive vs reactive
% strategies. Pre-deployment risks can still be prevented through better design,
% testing, or controls. Post-deployment risks require active monitoring and
% incident response capabilities.
%
% TODO: Add deployment phase transition tracking
% TODO: Implement phase-specific mitigation strategy recommendations
% TODO: Support for multi-phase risk lifecycle modeling
% TODO: Add prevention effectiveness metrics
% TODO: Implement cost-benefit analysis for pre vs post-deployment mitigation
% ============================================================================

% Preventable risks in pre-deployment phase
% These risks can still be addressed through design changes, testing, or controls
% before the system goes live. Represents opportunities for proactive risk reduction.
preventable_risks(Domain, SubDomain, RiskId, Title, Severity) :-
	risk(Domain, SubDomain, RiskId, Title, Severity),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

preventable_risks_count(Count) :-
	findall(R,
		preventable_risks(_, _, R, _, _),
		Risks),
	length(Risks, Count).

% HIGH severity preventable risks (maximum priority)
% Critical risks that can still be prevented - highest ROI for mitigation efforts.
preventable_high_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, high),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

preventable_high_risks_count(Count) :-
	findall(R,
		preventable_high_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% ============================================================================
% COMBINED SEVERITY PATTERNS
% ============================================================================
% Cross-references severity levels with other attributes to identify specific
% scenarios requiring different mitigation approaches.
%
% TODO: Add severity trend analysis (escalation detection)
% TODO: Implement severity threshold alerts with custom thresholds
% TODO: Support for multi-criteria severity scoring
% TODO: Add severity impact quantification (business/safety/reputation)
% ============================================================================

% HIGH severity risks requiring immediate action (post-deployment)
% Critical risks already in production that need urgent mitigation.
immediate_action_required(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, high),
	causality_timing(Domain, SubDomain, RiskId, 'post-deployment').

immediate_action_required_count(Count) :-
	findall(R,
		immediate_action_required(_, _, R, _),
		Risks),
	length(Risks, Count).

% MEDIUM severity AI-caused risks (continuous monitoring needed)
% Moderate AI-driven risks that require ongoing surveillance to prevent escalation.
moderate_ai_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, medium),
	causality_entity(Domain, SubDomain, RiskId, ai).

moderate_ai_risks_count(Count) :-
	findall(R,
		 moderate_ai_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% ============================================================================
% AGGREGATE RISK INDICATORS
% ============================================================================
% Boolean indicators that detect concerning patterns in the overall risk profile.
% These serve as alarm triggers for automated alerting and decision support.
%
% TODO: Add configurable threshold parameters
% TODO: Implement composite indicators (multiple condition combinations)
% TODO: Support for indicator sensitivity tuning
% TODO: Add historical indicator tracking for trend analysis
% TODO: Implement indicator correlation matrix
% ============================================================================

% Check if system has critical concentration of HIGH severity risks (>40%)
% Indicates systemic quality or safety issues requiring comprehensive review.
has_critical_risk_concentration :-
	total_risks(Total),
	Total > 0,
	risks_by_severity(high, High),
	Percentage is (High*100.0)/Total,
	Percentage > 40.

% Check if majority of risks are caused by AI (>60%)
% Suggests over-reliance on AI systems or insufficient human oversight mechanisms.
has_ai_dominance :-
	total_risks(Total),
	Total > 0,
	risks_by_entity(ai, AiRisks),
	Percentage is (AiRisks*100.0)/Total,
	Percentage > 60.

% Check if there are significant intentional threats (>3 risks)
% Indicates presence of adversarial actors requiring security countermeasures.
has_intentional_threats :-
	risks_by_intent(intentional, Count),
	Count > 3.

% Check if majority of risks are post-deployment (>70%)
% Suggests insufficient pre-deployment testing or reactive rather than proactive approach.
has_operational_risks :-
	total_risks(Total),
	Total > 0,
	risks_by_timing('post-deployment', PostDep),
	Percentage is (PostDep*100.0)/Total,
	Percentage > 70.

% Check if there are many unaddressed preventable risks (>40%)
% Indicates missed opportunities for proactive risk mitigation before deployment.
has_high_preventable_ratio :-
	total_risks(Total),
	Total > 0,
	risks_by_timing('pre-deployment', PreDep),
	Percentage is (PreDep*100.0)/Total,
	Percentage > 40.

% HIGH severity percentage helper (used by other rules)
% Calculates what proportion of risks are critical severity.
percentage_high_severity(Percentage) :-
	total_risks(Total),
	Total > 0,
	risks_by_severity(high, High),
	Percentage is (High*100.0)/Total.

% ============================================================================
% CONTEXT AND COMPARISON
% ============================================================================
% Provides comparative analysis and contextualization of risk profile against
% baselines, identifies dominant patterns, and measures data completeness.
%
% TODO: Add support for custom baseline profiles (industry/domain specific)
% TODO: Implement historical baseline tracking (trend vs baseline)
% TODO: Support for peer benchmarking data integration
% TODO: Add statistical significance testing for comparisons
% TODO: Implement risk profile clustering and classification
% ============================================================================

% Compare risk profile against typical baseline (severity distribution)
% Categorizes risk profile as: above_critical, above_average, average, below_average.
risk_profile_comparison(Comparison) :-
	percentage_high_severity(P),
	(P > 50 ->
	Comparison = 'above_critical';
	P > 35 ->
	Comparison = 'above_average';
	P > 20 ->
	Comparison = 'average';
	Comparison = 'below_average').

% Identify dominant pattern in the system (most frequent entity+intent+timing combination)
% Reveals the primary risk archetype characterizing the overall risk landscape.
dominant_pattern(Entity, Intent, Timing, Count) :-
	findall(C - E - I - T,
		((E = ai, I =  intentional, T = 'pre-deployment');
(E = ai, I =  intentional, T = 'post-deployment');
(E = ai, I = unintentional, T = 'pre-deployment');
(E = ai, I = unintentional, T = 'post-deployment');
(E = human, I =  intentional, T = 'pre-deployment');
(E = human, I =  intentional, T = 'post-deployment');
(E = human, I = unintentional, T = 'pre-deployment');
(E = human, I = unintentional, T = 'post-deployment'),
			risks_by_entity_intent_timing(E, I, T, C),
			C > 0),
		Patterns),
	sort(0, @>= , Patterns, [Count - Entity - Intent - Timing|_]).

% Helper: count risks by entity+intent+timing triple
% Supports dominant pattern identification by counting each combination.
risks_by_entity_intent_timing(Entity, Intent, Timing, Count) :-
	findall(R,
		(risk(D, SD, R, _, _),
			causality_entity(D, SD, R, Entity),
			causality_intent(D, SD, R, Intent),
			causality_timing(D, SD, R, Timing)),
		Risks),
	length(Risks, Count).

% Percentage of risks with fully defined causality (no "other" values)
% Data quality metric - higher percentages indicate more confident causal analysis.
fully_defined_causality_percentage(Percentage) :-
	total_risks(Total),
	Total > 0,
	findall((D, SD, R),
		(risk(D, SD, R, _, _),
			causality_entity(D, SD, R, E),
			E \= other,
			causality_intent(D, SD, R, I),
			I \= other,
			causality_timing(D, SD, R, T),
			T \= other),
		Risks),
	length(Risks, Defined),
	Percentage is (Defined*100.0)/Total.

% Domain coverage: percentage of domains with at least one risk
% Measures breadth of risk assessment across MIT taxonomy domains (out of 7 total).
domain_coverage_percentage(Percentage) :-
	findall(D,
		(domain(D, _),
			risks_in_domain(D, C),
			C > 0),
		ActiveDomains),
	list_to_set(ActiveDomains, UniqueActive),
	length(UniqueActive, ActiveCount),
	Percentage is (ActiveCount*100.0)/7.

% Subdomain coverage: percentage of subdomains explored
% Measures granularity of risk assessment across MIT taxonomy subdomains (26 total).
subdomain_coverage_percentage(Percentage) :-
	findall(D - SD,
		subdomain(D, SD, _),
		AllSubdomains),
	length(AllSubdomains, Total),
	Total > 0,
	findall(D - SD,
		(subdomain(D, SD, _),
			risks_in_subdomain(D, SD, C),
			C > 0),
		Active),
	length(Active, ActiveCount),
	Percentage is (ActiveCount*100.0)/Total.

% ============================================================================
% ADDITIONAL RELEVANT PATTERNS
% ============================================================================
% Extended pattern library covering additional risk scenarios beyond critical
% patterns. Includes AI intentionality, preventable critical AI risks, severe
% human errors, and low-priority preventable risks for comprehensive analysis.
%
% TODO: Add pattern dependency mapping (which patterns co-occur)
% TODO: Implement pattern severity escalation paths
% TODO: Support for user-defined custom patterns
% TODO: Add pattern-specific mitigation strategy database
% TODO: Implement pattern prediction (early warning signals)
% ============================================================================

% AI acting with intentional behavior (e.g., goal misalignment scenarios)
% Represents AI systems pursuing objectives misaligned with human values or intent.
intentional_ai_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, _),
	causality_entity(Domain, SubDomain, RiskId, ai),
	causality_intent(Domain, SubDomain, RiskId, intentional).

intentional_ai_risks_count(Count) :-
	findall(R,
			intentional_ai_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% HIGH severity AI-caused risks still preventable (pre-deployment)
% Critical AI risks that can still be mitigated through design, testing, or controls.
preventable_critical_ai_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, high),
	causality_entity(Domain, SubDomain, RiskId, ai),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

preventable_critical_ai_risks_count(Count) :-
	findall(R,
		preventable_critical_ai_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% Critical unintentional human errors
% Severe human mistakes requiring improved training, UX design, or safety guardrails.
critical_human_errors(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, high),
	causality_entity(Domain, SubDomain, RiskId, human),
	causality_intent(Domain, SubDomain, RiskId, unintentional).

critical_human_errors_count(Count) :-
	findall(R,
		critical_human_errors(_, _, R, _),
		Risks),
	length(Risks, Count).

% LOW/MEDIUM severity risks in pre-deployment (preventive monitoring)
% Lower priority risks that should be tracked but don't require immediate action.
low_priority_preventable(Domain, SubDomain, RiskId, Title, Severity) :-
	risk(Domain, SubDomain, RiskId, Title, Severity),
	(Severity = low;
Severity = medium),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

low_priority_preventable_count(Count) :-
	findall(R,
		low_priority_preventable(_, _, R, _, _),
		Risks),
	length(Risks, Count).

% ============================================================================
% SUBDOMAIN ANALYSIS
% ============================================================================
% Granular analysis at subdomain level to identify specific areas of highest
% concern within broader domains. Enables targeted interventions at the most
% granular level of the MIT taxonomy (26 subdomains across 7 domains).
%
% TODO: Add subdomain risk density analysis (risks per subdomain area)
% TODO: Implement subdomain interdependency mapping
% TODO: Support for subdomain-specific KPIs and thresholds
% TODO: Add subdomain evolution tracking over time
% TODO: Implement subdomain clustering by risk profile similarity
% ============================================================================

% Count HIGH severity risks within a specific subdomain
subdomain_high_risk_count(Domain, SubDomain, Count) :-
	subdomain(Domain, SubDomain, _),
	findall(R,
		risk(Domain, SubDomain, R, _, high),
		Risks),
	length(Risks, Count).

% Count total risks within a subdomain (all severity levels)
subdomain_total_risk_count(Domain, SubDomain, Count) :-
	findall(R,
		risk(Domain, SubDomain, R, _, _),
		Risks),
	length(Risks, Count).

% Most critical subdomain overall (maximum HIGH severity risks across all domains)
most_critical_subdomain(Domain, SubDomain, SubDomainName, Count) :-
	findall(C - D - SD - N,
		(subdomain_high_risk_count(D, SD, C),
			C > 0,
			subdomain(D, SD, N)),
		Pairs),
	sort(0, @>= , Pairs, [Count - Domain  - SubDomain  - SubDomainName|_]).

% Most critical subdomain within the most critical domain
% Identifies the specific subdomain requiring most urgent attention in top-priority domain.
most_critical_subdomain_in_top_domain(Domain, SubDomain, SubDomainName, Count) :-
	most_critical_domain(Domain, _, _),
	subdomain_high_risk_count(Domain, SubDomain, Count),
	Count > 0,
	 \+ (subdomain_high_risk_count(Domain, _SD2, C2),
		C2 > Count),
	subdomain(Domain, SubDomain, SubDomainName).

% ============================================================================
% DISTRIBUTION METRICS
% ============================================================================
% Statistical distribution analysis of risks across multiple dimensions.
% Provides insights into risk concentration, entity balance, and phase distribution
% to inform strategic decision-making.
%
% TODO: Add distribution skewness and kurtosis metrics
% TODO: Implement entropy-based diversity metrics
% TODO: Support for custom distribution visualizations
% TODO: Add distribution comparison over time (shifting distributions)
% TODO: Implement Gini coefficient for risk inequality measurement
% ============================================================================

% Percentage of AI risks in pre-deployment phase
% Measures how much AI risk can still be prevented before going live.
percentage_ai_predeployment(Percentage) :-
	risks_by_entity(ai, TotalAI),
	TotalAI > 0,
	findall(R,
		(risk(D, SD, R, _, _),
			causality_entity(D, SD, R, ai),
			causality_timing(D, SD, R, 'pre-deployment')),
		Risks),
	length(Risks, PreDep),
	Percentage is (PreDep*100.0)/TotalAI.

% Percentage of HIGH severity risks that are intentional
% Indicates proportion of critical risks driven by deliberate actions (malicious or goal-driven).
percentage_high_intentional(Percentage) :-
	risks_by_severity(high, TotalHigh),
	TotalHigh > 0,
	findall(R,
		(risk(D, SD, R, _, high),
			causality_intent(D, SD, R, intentional)),
		Risks),
	length(Risks, HighIntent),
	Percentage is (HighIntent*100.0)/TotalHigh.

% AI to HUMAN risk ratio
% Measures relative contribution of AI vs human factors to overall risk landscape.
ai_human_ratio(Ratio) :-
	risks_by_entity(ai, AI),
	risks_by_entity(human, Human),
	Human > 0,
	Ratio is AI/Human.

% ============================================================================
% ADDITIONAL PATTERNS FOR COMPREHENSIVE COVERAGE
% ============================================================================
% Extended pattern set covering moderate severity risks, timing-entity combinations,
% and operational risk scenarios. Ensures no risk archetype is missed in analysis.
%
% TODO: Add pattern completeness validation (ensure all combinations covered)
% TODO: Implement pattern gap detection (missing risk archetypes)
% TODO: Support for probabilistic pattern matching (fuzzy patterns)
% TODO: Add pattern evolution modeling (how patterns change over lifecycle)
% TODO: Implement pattern-based risk forecasting
% ============================================================================

% MEDIUM + post-deployment pattern (active risks requiring monitoring)
% Moderate operational risks that need surveillance to prevent escalation.
moderate_operational_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, medium),
	causality_timing(Domain, SubDomain, RiskId, 'post-deployment').

moderate_operational_risks_count(Count) :-
	findall(R,
			moderate_operational_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% HUMAN + pre-deployment pattern (preventable human errors)
% Human-caused risks that can be addressed through training, UX improvements, or controls.
preventable_human_risks(Domain, SubDomain, RiskId, _Title) :-
	causality_entity(Domain, SubDomain, RiskId, human),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

preventable_human_risks_count(Count) :-
	findall(R,
		preventable_human_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% AI + pre-deployment pattern (all preventable AI risks, not just HIGH)
% Comprehensive view of AI risks that can be mitigated before deployment.
preventable_ai_risks(Domain, SubDomain, RiskId, _Title) :-
	causality_entity(Domain, SubDomain, RiskId, ai),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

preventable_ai_risks_count(Count) :-
	findall(R,
		preventable_ai_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% Intentional + pre-deployment pattern (preventable threats)
% Adversarial risks that can be mitigated through security controls before deployment.
preventable_intentional_threats(Domain, SubDomain, RiskId, _Title) :-
	causality_intent(Domain, SubDomain, RiskId, intentional),
	causality_timing(Domain, SubDomain, RiskId, 'pre-deployment').

preventable_intentional_threats_count(Count) :-
	findall(R,
		preventable_intentional_threats(_, _, R, _),
		Risks),
	length(Risks, Count).

% MEDIUM + HUMAN pattern (moderate human errors)
% Mid-level human-driven risks requiring attention but not critical urgency.
moderate_human_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, medium),
	causality_entity(Domain, SubDomain, RiskId, human).

moderate_human_risks_count(Count) :-
	findall(R,
			moderate_human_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% MEDIUM + AI + intentional pattern
% Moderate risks from AI systems acting with intentional behavior (e.g., partial goal misalignment).
moderate_intentional_ai_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, medium),
	causality_entity(Domain, SubDomain, RiskId, ai),
	causality_intent(Domain, SubDomain, RiskId, intentional).

moderate_intentional_ai_risks_count(Count) :-
	findall(R,
			moderate_intentional_ai_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% MEDIUM + HUMAN + intentional pattern
% Moderate deliberate human actions (semi-serious attacks, minor fraud, etc.).
moderate_human_intentional_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, medium),
	causality_entity(Domain, SubDomain, RiskId, human),
	causality_intent(Domain, SubDomain, RiskId, intentional).

moderate_human_intentional_risks_count(Count) :-
	findall(R,
			moderate_human_intentional_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% LOW severity + post-deployment pattern (minor operational risks)
% Low-priority operational risks that require minimal monitoring.
low_operational_risks(Domain, SubDomain, RiskId, Title) :-
	risk(Domain, SubDomain, RiskId, Title, low),
	causality_timing(Domain, SubDomain, RiskId, 'post-deployment').

low_operational_risks_count(Count) :-
	findall(R,
		low_operational_risks(_, _, R, _),
		Risks),
	length(Risks, Count).

% ============================================================================
% ADDITIONAL ALERT INDICATORS
% ============================================================================
% Supplementary boolean indicators for detecting less common but still important
% risk concentration patterns (MEDIUM accumulation, human error dominance).
%
% TODO: Add machine learning-based anomaly detection indicators
% TODO: Implement adaptive threshold adjustment based on historical data
% TODO: Support for composite alert indicators (multi-condition triggers)
% TODO: Add alert priority ranking and clustering
% TODO: Implement alert fatigue prevention (smart aggregation)
% ============================================================================

% Check if MEDIUM severity risks are being neglected (>40% of total)
% Suggests accumulation of unaddressed moderate risks that could escalate.
has_medium_risk_accumulation :-
	total_risks(Total),
	Total > 0,
	risks_by_severity(medium, Medium),
	Percentage is (Medium*100.0)/Total,
	Percentage > 40.

% Check if human errors are predominant (>50% of risks)
% Indicates need for improved training, UX design, or human oversight mechanisms.
human_error_dominance :-
	total_risks(Total),
	Total > 0,
	risks_by_entity(human, Human),
	Percentage is (Human*100.0)/Total,
	Percentage > 50.