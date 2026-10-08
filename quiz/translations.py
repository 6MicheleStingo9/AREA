"""Centralised UI translations. Single source of truth for all language strings."""

TRANSLATIONS = {
    "start_button": {
        "en": "Start the Questionnaire",
        "it": "Inizia il Questionario",
    },
    "back_button": {"en": "← Back", "it": "← Indietro"},
    "next_button": {"en": "Next →", "it": "Avanti →"},
    "complete_button": {"en": "✅ Complete", "it": "✅ Completa"},
    "answer_label": {"en": "Answer", "it": "Risposta"},
    "select_option": {"en": "Select an option", "it": "Seleziona un'opzione"},
    "select_applicable": {
        "en": "Select applicable options:",
        "it": "Seleziona le opzioni applicabili:",
    },
    "other_specify": {"en": "Other (specify)", "it": "Altro (specifica)"},
    "specify_other": {"en": "Specify...", "it": "Specifica..."},
    "specify_other_required": {
        "en": "Please specify a value for 'Other'",
        "it": "Specifica un valore per 'Altro'",
    },
    "followup_answer": {"en": "Follow-up answer", "it": "Risposta di follow-up"},
    "followups_nojs_hint": {
        "en": "Answer the follow-up questions below only if they apply to your answer.",
        "it": "Rispondi alle domande di approfondimento qui sotto solo se pertinenti alla tua risposta.",
    },
    "questionnaire_title": {
        "en": "AI Risk Assessment Questionnaire",
        "it": "Questionario di Valutazione Rischi AI",
    },
    "welcome": {"en": "Welcome", "it": "Benvenuto"},
    "this_question_is_required": {
        "en": "This question is required",
        "it": "Questa domanda è obbligatoria",
    },
    "completion_title": {
        "en": "Questionnaire Completed!",
        "it": "Questionario completato!",
    },
    "total_questions": {"en": "Total Questions", "it": "Domande totali"},
    "answers_given": {"en": "Answers Given", "it": "Risposte date"},
    "answers_saved": {
        "en": "Your answers have been successfully saved!",
        "it": "Le tue risposte sono state salvate con successo!",
    },
    "run_analysis_button": {
        "en": "Run Risk Analysis and Generate Report",
        "it": "Avvia analisi rischi e genera report",
    },
    "question_label": {"en": "Question", "it": "Domanda"},
    "analysis_running": {"en": "Running analysis...", "it": "Analisi in corso..."},
    "pipeline_running_hint": {
        "en": "The pipeline is running. This usually takes 1–3 minutes.",
        "it": "La pipeline è in esecuzione. Di solito servono 1–3 minuti.",
    },
    "job_not_found": {
        "en": "Analysis job not found (the server may have restarted). Please start a new analysis.",
        "it": "Analisi non trovata (il server potrebbe essere stato riavviato). Avvia una nuova analisi.",
    },
    "analysis_complete": {
        "en": "Analysis complete! Report generated.",
        "it": "Analisi completata! Report generato.",
    },
    "open_html_report": {"en": "Open Report", "it": "Apri report"},
    "report_not_found": {
        "en": "Analysis completed but report file not found.",
        "it": "Analisi completata ma file report non trovato.",
    },
    "analysis_error": {"en": "Error during analysis", "it": "Errore durante l'analisi"},
    "restart_button": {"en": "Restart", "it": "Ricomincia"},
    "min_length_validation": {
        "en": "The answer must contain at least {min_length} characters",
        "it": "La risposta deve contenere almeno {min_length} caratteri",
    },
    "min_selections_validation": {
        "en": "Select at least {min_selections} option(s)",
        "it": "Seleziona almeno {min_selections} opzione/i",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translate key to the given language, interpolating any kwargs."""
    text = TRANSLATIONS.get(key, {}).get(lang, key)
    return text.format(**kwargs) if kwargs else text
