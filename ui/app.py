import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import sys
import time
import importlib.util
import sys
from pathlib import Path

# Ensure project root is on sys.path so absolute UI imports work when running from any directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Import orchestrator run function ---
ORCHESTRATOR_PATH = (
    Path(__file__).resolve().parent.parent / "agents" / "orchestrator.py"
)
spec = importlib.util.spec_from_file_location("orchestrator", str(ORCHESTRATOR_PATH))
orchestrator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orchestrator)

from ui.styles import GLOBAL_CSS
from ui.localization import TRANSLATIONS


class StreamlitQuestionnaireApp:
    """Streamlit application for the AI Risk Assessment questionnaire."""

    def t(self, key):
        """Translate a given key based on the selected language."""
        return TRANSLATIONS.get(key, {}).get(self.lang, key)

    def __init__(self, lang: str = "en"):
        self.lang = lang  # Save the language as an instance attribute
        # Resolve questions file path relative to project root (two levels up)
        base_files_dir = Path(__file__).resolve().parent.parent / "files"
        self.questions_path = base_files_dir / f"questions_{self.lang}.json"
        self.load_questions()
        self.init_session_state()

    def load_questions(self) -> None:
        """Load questions from the JSON file."""
        with open(self.questions_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.questions = data["questions"]

    def init_session_state(self) -> None:
        """Initialize the session state."""
        if "current_question" not in st.session_state:
            st.session_state.current_question = 0
        if "answers" not in st.session_state:
            st.session_state.answers = {}
        if "started" not in st.session_state:
            st.session_state.started = False
        if "followups_shown" not in st.session_state:
            st.session_state.followups_shown = {}

    def show_welcome(self) -> None:
        """Show the welcome screen."""

        if hasattr(self, "lang") and self.lang == "en":
            welcome_text = """
                # 🛡️ AI Risk Assessment Questionnaire

                ### Welcome

                This questionnaire is designed to assess potential risks associated with artificial intelligence systems through a structured analysis.

                ### Covered areas:

                1. **Discrimination & Toxicity**
                2. **Privacy & Security**
                3. **Disinformation**
                4. **Malicious Actors**
                5. **Human-Computer Interaction**
                6. **Socioeconomic & Environmental Impacts**
                7. **AI System Safety and Limitations**

                ### How it works:

                - Answer **24 questions** divided into thematic areas
                - Some questions have **follow-ups** that appear based on your answers
                - You can **navigate** between questions using the buttons
                - Answers are **saved automatically**

                ---
                """
        else:
            welcome_text = """
                # 🛡️ Questionario di Valutazione Rischi AI

                ### Benvenuto

                Questo questionario è progettato per valutare i potenziali rischi associati 
                ai sistemi di intelligenza artificiale attraverso un'analisi strutturata.

                ### Aree coperte:

                1. **Discriminazione & Tossicità**
                2. **Privacy & Sicurezza**
                3. **Disinformazione**
                4. **Attori Malintenzionati**
                5. **Interazione Umano-Computer**
                6. **Impatti Socioeconomici & Ambientali**
                7. **Sicurezza e Limitazioni del Sistema AI**

                ### Come funziona:

                - Rispondi a **24 domande** suddivise nelle aree tematiche
                - Alcune domande hanno **follow-up** che appaiono in base alle tue risposte
                - Puoi **navigare** tra le domande usando i pulsanti
                - Le risposte vengono **salvate automaticamente**

                ---
                """

        st.markdown(welcome_text, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(
                self.t("start_button"), use_container_width=True, type="primary"
            ):
                st.session_state.started = True
                st.rerun()

    def render_question(self, question: Dict[str, Any]) -> Any:
        """Render a single question and return the answer."""
        question_id = question["id"]
        question_type = question["type"]

        # Show the question
        st.markdown(f"### {question['question']}")

        # Mostra help text se presente
        if "help_text" in question:
            st.info(question["help_text"])

        answer = None

        # Rendering basato sul tipo
        if question_type == "free_text":
            multiline = question.get("multiline", False)
            placeholder = question.get("placeholder", "")

            if multiline:
                answer = st.text_area(
                    self.t("answer_label"),
                    value=st.session_state.answers.get(question_id, {}).get(
                        "answer", ""
                    ),
                    placeholder=placeholder or self.t("specify_other"),
                    height=150,
                    key=f"q_{question_id}",
                    label_visibility="collapsed",
                )
            else:
                answer = st.text_input(
                    self.t("answer_label"),
                    value=st.session_state.answers.get(question_id, {}).get(
                        "answer", ""
                    ),
                    placeholder=placeholder or self.t("specify_other"),
                    key=f"q_{question_id}",
                    label_visibility="collapsed",
                )

        elif question_type == "multiple_choice":
            options = question["options"]
            saved_answer = st.session_state.answers.get(question_id, {}).get("answer")
            default_index = (
                options.index(saved_answer) if saved_answer in options else 0
            )

            answer = st.radio(
                self.t("select_option"),
                options=options,
                index=default_index,
                key=f"q_{question_id}",
                label_visibility="collapsed",
            )

        elif question_type == "checkbox":
            options = question["options"]
            saved_answer = st.session_state.answers.get(question_id, {}).get(
                "answer", {}
            )
            saved_selected = (
                saved_answer.get("selected", [])
                if isinstance(saved_answer, dict)
                else []
            )

            st.markdown(f"**{self.t('select_applicable')}**")
            selected = []

            cols = st.columns(3)
            for idx, option in enumerate(options):
                with cols[idx % 3]:
                    if st.checkbox(
                        option,
                        value=option in saved_selected,
                        key=f"q_{question_id}_opt_{idx}",
                    ):
                        selected.append(option)

            # Handle "Other"
            other_value = None
            if question.get("allow_other"):
                # Check that "other" exists AND has a non-empty value
                other_checked = (
                    isinstance(saved_answer, dict)
                    and saved_answer.get("other") is not None
                    and saved_answer.get("other") != ""
                )
                if st.checkbox(
                    self.t("other_specify"),
                    value=other_checked,
                    key=f"q_{question_id}_other_check",
                ):
                    other_value = st.text_input(
                        self.t("specify_other"),
                        value=(
                            saved_answer.get("other", "")
                            if isinstance(saved_answer, dict)
                            else ""
                        ),
                        key=f"q_{question_id}_other",
                        placeholder=self.t("specify_other"),
                    )

            answer = {"selected": selected, "other": other_value}

        return answer

    def render_followups(
        self, question: Dict[str, Any], main_answer: Any
    ) -> Dict[str, Any]:
        """Render the follow-up questions and return the answers."""
        followup_answers = {}

        if "follow_ups" not in question or not question["follow_ups"]:
            return followup_answers

        # Check if follow-ups have been "shown" (after first click)
        question_id = question["id"]
        followups_shown = st.session_state.followups_shown.get(question_id, False)

        for idx, followup in enumerate(question["follow_ups"]):
            # Show the follow-up only if: condition met AND shown flag = True
            if (
                self.should_show_followup(followup, main_answer, question["type"])
                and followups_shown
            ):
                st.markdown("---")
                st.markdown(f"**➥ {followup['text']}**")

                if followup.get("help_text"):
                    st.caption(followup["help_text"])

                followup_key = f"followup_{question['id']}_{idx}"
                saved_followup = (
                    st.session_state.answers.get(question["id"], {})
                    .get("followups", {})
                    .get(str(idx))
                )

                if followup.get("multiline", False):
                    followup_answer = st.text_area(
                        self.t("followup_answer"),
                        value=saved_followup or "",
                        height=100,
                        key=followup_key,
                        label_visibility="collapsed",
                    )
                else:
                    followup_answer = st.text_input(
                        self.t("followup_answer"),
                        value=saved_followup or "",
                        key=followup_key,
                        label_visibility="collapsed",
                    )

                followup_answers[str(idx)] = followup_answer

        return followup_answers

    def should_show_followup(
        self, followup: Dict, answer: Any, question_type: str
    ) -> bool:
        """Determine if a follow-up question should be shown based on the answer."""
        condition = followup.get("condition", {})
        condition_type = condition.get("type")

        if condition_type == "always":
            if question_type == "free_text":
                return answer and len(str(answer).strip()) >= 10
            return bool(answer)

        elif condition_type == "option_index":
            value = condition.get("value")
            if question_type == "multiple_choice":
                options = followup.get("_parent_options", [])
                if options and isinstance(answer, str):
                    return (
                        options.index(answer) == value if answer in options else False
                    )

        elif condition_type == "option_index_in":
            values = condition.get("value", [])
            if question_type == "checkbox" and isinstance(answer, dict):
                selected = answer.get("selected", [])
                return any(idx in values for idx in range(len(selected)))

        elif condition_type == "has_other":
            if isinstance(answer, dict):
                return answer.get("other") is not None and answer.get("other") != ""

        return False

    def validate_answer(
        self,
        question: Dict[str, Any],
        answer: Any,
        followup_answers: Dict[str, Any] = None,
    ) -> tuple[bool, str]:
        """Validate the main answer and follow-ups."""
        if question.get("required", False):
            if question["type"] == "free_text":
                if not answer or not str(answer).strip():
                    return False, self.t("this_question_is_required")
                validation = question.get("validation", {})
                min_length = validation.get("min_length", 0)
                if len(answer) < min_length:
                    return (
                        False,
                        f"The answer must contain at least {min_length} characters",
                    )

            elif question["type"] == "checkbox":
                min_selections = question.get("min_selections", 1)
                selected = (
                    answer.get("selected", []) if isinstance(answer, dict) else []
                )
                total = len(selected)
                if answer.get("other"):
                    total += 1
                if total < min_selections:
                    return False, f"Seleziona almeno {min_selections} opzione/i"

        return True, ""

    def save_answers(self) -> Path:
        """Salva le risposte in un file JSON."""
        output_path = (
            Path("files/answers")
            / f"answers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "language": self.lang,
                "total_questions": len(self.questions),
                "answered_questions": len(st.session_state.answers),
            },
            "answers": st.session_state.answers,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        return output_path

    def show_questionnaire(self) -> None:
        """Mostra il questionario principale."""
        # The chat sidebar is rendered centrally in `run()`

        # Main content
        current_idx = st.session_state.current_question
        question = self.questions[current_idx]

        # Progress bar and counter
        progress = (current_idx + 1) / len(self.questions)
        st.progress(progress, text=f"**{current_idx + 1}/{len(self.questions)}**")

        st.markdown("---")

        # Main question
        answer = self.render_question(question)

        # Follow-up
        followup_answers = self.render_followups(question, answer)

        # Check if there are visible follow-ups
        question_id = question["id"]
        has_visible_followups = False
        if question.get("follow_ups"):
            for followup in question["follow_ups"]:
                if self.should_show_followup(followup, answer, question["type"]):
                    has_visible_followups = True
                    break

        # Check if follow-ups have already been shown for this question
        followups_already_shown = st.session_state.followups_shown.get(
            question_id, False
        )

        # Save answers in session state
        st.session_state.answers[question["id"]] = {
            "question": question["question"],
            "answer": answer,
            "followups": followup_answers,
            # "timestamp": datetime.now().isoformat(),
        }

        # Navigation
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            if current_idx > 0:
                if st.button(self.t("back_button"), use_container_width=True):
                    st.session_state.current_question -= 1
                    st.rerun()

        with col2:
            if current_idx < len(self.questions) - 1:
                is_valid, error_msg = self.validate_answer(
                    question, answer, followup_answers
                )
                if st.button(
                    self.t("next_button"), use_container_width=True, type="primary"
                ):
                    if is_valid:
                        # If there are visible follow-ups that have not yet been shown
                        if has_visible_followups and not followups_already_shown:
                            # First click: mark as shown and rerun to render them
                            st.session_state.followups_shown[question_id] = True
                            st.rerun()
                        else:
                            # Second click (or no follow-up): advance to the next question
                            st.session_state.current_question += 1
                            # Reset the flag for the next question
                            if current_idx + 1 < len(self.questions):
                                next_question_id = self.questions[current_idx + 1]["id"]
                                st.session_state.followups_shown[next_question_id] = (
                                    False
                                )
                            st.rerun()
                    else:
                        st.error(error_msg)
            else:
                is_valid, error_msg = self.validate_answer(
                    question, answer, followup_answers
                )
                if st.button(
                    self.t("complete_button"), use_container_width=True, type="primary"
                ):
                    if is_valid:
                        path = self.save_answers()
                        st.session_state.completed = True
                        st.rerun()
                    else:
                        st.error(error_msg)

    def show_completion(self) -> None:
        """Show the completion screen."""
        st.balloons()
        st.markdown(self.t("completion_title"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.metric(self.t("total_questions"), len(self.questions))
        with col2:
            st.metric(self.t("answers_given"), len(st.session_state.answers))
        st.success(self.t("answers_saved"))

        # --- Analysis and report generation ---
        answers_path = self.save_answers()
        if st.button(self.t("run_analysis_button"), type="primary"):
            st.info(self.t("analysis_launching"))
            with st.spinner(self.t("analysis_running")):
                try:
                    final_state = orchestrator.run_orchestrator(str(answers_path))
                    html_path = final_state.get("report_state", {}).get("html_path")
                    if html_path and Path(html_path).exists():
                        st.success(self.t("analysis_complete"))
                        st.markdown(f"[{self.t('open_html_report')}]({html_path})")
                    else:
                        st.error(self.t("report_not_found"))
                except Exception as e:
                    st.error(f"{self.t('analysis_error')}: {e}")
        if st.button(self.t("restart_button"), type="secondary"):
            st.session_state.clear()
            st.rerun()

    def run(self) -> None:
        """Run the application."""
        st.set_page_config(
            page_title="AI Risk Assessment",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Apply custom CSS
        st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

        if not st.session_state.started:
            self.show_welcome()
        elif st.session_state.get("completed", False):
            self.show_completion()
        else:
            self.show_questionnaire()


def main():
    """Entry point for the Streamlit application."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Start the AI Risk Assessment questionnaire"
    )
    parser.add_argument(
        "--lang",
        choices=["it", "en"],
        default="en",
        help="Questionnaire language (default: en)",
    )
    args, _ = parser.parse_known_args(sys.argv[1:])
    app = StreamlitQuestionnaireApp(lang=args.lang)
    app.run()


if __name__ == "__main__":
    main()
