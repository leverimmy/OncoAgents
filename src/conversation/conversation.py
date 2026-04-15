import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.backend import LanguageModel
from src.emotional_patient import (
    NotEmotionalPatient,
    SimpleEmotionalPatient,
)
from src.mdt import MDT
from src.prompt import (
    DOCTOR_BASELINE_REPLY_PROMPT,
    DOCTOR_REPLY_PROMPT,
    DOCTOR_REPLY_PROMPT_WITH_EXPLANATION,
    DOCTOR_STRATEGY_PROMPT,
    DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE,
    JUDGE_DOCTOR_COVERAGE_PROMPT,
    JUDGE_DOCTOR_HUMANITY_PROMPT,
    JUDGE_DOCTOR_SAFETY_PROMPT,
)
from src.utils import (
    SafeDict,
    logger,
    render_diagnosis_data,
    render_user_profile,
)


class Conversation:
    def __init__(
        self,
        file_name: str,
        patient_data: dict[str, str],
        examination_data: dict[str, str],
        patient_model_name: str,
        strategy_model_name: str,
        reply_model_name: str,
        mdt_model_name: str,
        judge_model_name: str,
        url: str | None = None,
        max_turns: int = 15,
        human_in_the_loop: bool = False,
        has_expert_knowledge: bool = False,
        is_emotional_patient: bool = True,
        is_baseline: bool = False,
        do_eval_patient: bool = False,
        do_eval_doctor: bool = False,
        conversation_history: list[dict[str, str]] | None = None,
    ):
        self.file_name = file_name
        # patient_data 包含 personal_info、symptom 和 reiterated_symptom
        # examination_data 包含 symptom、auxiliary_examination、diagnosis 和 treatment
        self.patient_data = patient_data
        self.examination_data = examination_data

        self.strategy_model = LanguageModel(model_name=strategy_model_name, url=url)
        self.reply_model = LanguageModel(model_name=reply_model_name, url=url)
        self.judge_model = LanguageModel(model_name=judge_model_name, url=url)
        self.mdt = MDT(
            model_name=mdt_model_name,
            url=url,
            examination_data=self.examination_data
        )
        self.url = url

        self.human_in_the_loop = human_in_the_loop
        self.has_expert_knowledge = has_expert_knowledge
        self.is_emotional_patient = is_emotional_patient
        self.is_baseline = is_baseline
        self.do_eval_patient = do_eval_patient
        self.do_eval_doctor = do_eval_doctor

        self.max_turns = max_turns
        self.negotiation_completed = False
        self.negotiation_result = None  # "accept", "reject", "error"
        self.conversation_history = [] if conversation_history is None else conversation_history
        self.completed_turns = 0
        self.judge_doctor_scores = {}
        self.judge_patient_scores = {}
        self.patient_scores = []

        if self.is_emotional_patient:
            self.patient_agent = SimpleEmotionalPatient(
                user_profile=render_user_profile(self.patient_data, "Patient"),
                model_name=patient_model_name,
                url=url,
            )
        else:
            self.patient_agent = NotEmotionalPatient(
                user_profile=render_user_profile(self.patient_data, "Patient"),
                model_name=patient_model_name,
                url=url,
            )
        self.user_profile = render_user_profile(
            patient_data=self.patient_data,
            role="Doctor",
            with_symptoms=True,
        )
        self.diagnosis_data = render_diagnosis_data(
            examination_data=self.examination_data,
            with_exams=True,
        )

    def _get_dialogue_history(self, role: str | None = None) -> list[dict[str, str]]:
        dialogue_history = []
        for turn in self.conversation_history:
            try:
                assert turn["speaker"] in ["Doctor", "Patient"]
                if role is not None and turn["speaker"] != role:
                    continue
                dialogue_history.append(
                    {"speaker": turn["speaker"], "message": turn["message"]["response"]}
                )
            except Exception as e:
                logger.error(f'Error processing turn: {turn}, turn["speaker"]: {e}')
        return json.dumps(dialogue_history, ensure_ascii=False)

    def _run_strategy_model(
        self,
    ) -> tuple[str, str, str, list[str]]:
        if self.has_expert_knowledge:
            format_args = SafeDict(
                user_profile=self.user_profile,
                diagnosis_data=self.diagnosis_data,
                dialogue_history=self._get_dialogue_history(),
            )
            json_result = self.strategy_model.chat(
                prompt=DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE.format_map(format_args),
                json_format=True,
            )
        else:
            format_args = SafeDict(
                user_profile=self.user_profile,
                diagnosis_data=self.diagnosis_data,
                dialogue_history=self._get_dialogue_history(),
            )
            json_result = self.strategy_model.chat(
                prompt=DOCTOR_STRATEGY_PROMPT.format_map(format_args),
                json_format=True,
            )
        stage = json_result.get("stage", "framework")
        analysis = json_result["analysis"]
        strategy = json_result["strategy"]
        keywords = json_result.get("keywords", [])

        logger.info(f"Strategy Model Result: {json_result}")
        return stage, analysis, strategy, keywords

    def _run_reply_model(
        self, stage: str, analysis: str, strategy: str, keywords: list[str],
    ) -> tuple[str, list[dict[str, str]]]:
        explanation = []
        if len(keywords) > 0 and stage in ["知识传递阶段", "决策与总结阶段"]:
            explanation = self.mdt.respond(
                keywords=keywords,
            )
            logger.info(f"Explanation Model Result: {explanation}")

            format_args = SafeDict(
                user_profile=self.user_profile,
                diagnosis_data=render_diagnosis_data(self.examination_data),
                dialogue_history=self._get_dialogue_history(),
                analysis=analysis,
                strategy=strategy,
                explanation=explanation,
            )
            reply = self.reply_model.chat(
                prompt=DOCTOR_REPLY_PROMPT_WITH_EXPLANATION.format_map(format_args),
                json_format=False,
            )
        else:
            format_args = SafeDict(
                user_profile=self.user_profile,
                diagnosis_data=render_diagnosis_data(self.examination_data),
                dialogue_history=self._get_dialogue_history(),
                analysis=analysis,
                strategy=strategy,
            )
            reply = self.reply_model.chat(
                prompt=DOCTOR_REPLY_PROMPT.format_map(format_args),
                json_format=False,
            )
        logger.info(f"Reply Model Result: {reply}")
        return reply, explanation

    def _run_baseline_reply_model(self) -> str:
        format_args = SafeDict(
            user_profile=self.user_profile,
            diagnosis_data=self.diagnosis_data,
            dialogue_history=self._get_dialogue_history(),
        )
        reply = self.reply_model.chat(
            prompt=DOCTOR_BASELINE_REPLY_PROMPT.format_map(format_args),
            json_format=False,
        )
        logger.info(f"Baseline Reply Model Result: {reply}")
        return reply

    def _run_judge_patient_model(self) -> dict[str, int | str]:
        # format_args = SafeDict(
        #     user_profile=render_user_profile(
        #         patient_data=self.patient_data,
        #         role="Doctor",
        #         with_symptoms=False
        #     ),
        #     diagnosis_data=self.diagnosis_data,
        #     dialogue_history=self._get_dialogue_history(),
        # )
        # with ThreadPoolExecutor(max_workers=2) as executor:
        #     judge_patient_persona_future = executor.submit(
        #         self.judge_model.chat,
        #         prompt=JUDGE_PATIENT_PERSONA_PROMPT.format_map(format_args),
        #         json_format=True,
        #     )
        #     judge_patient_humanlikeness_future = executor.submit(
        #         self.judge_model.chat,
        #         prompt=JUDGE_PATIENT_HUMANLIKENESS_PROMPT.format_map(format_args),
        #         json_format=True,
        #     )
        #     json_result_1 = judge_patient_persona_future.result()
        #     json_result_2 = judge_patient_humanlikeness_future.result()

        # json_result = {
        #     "persona_evaluation": json_result_1,
        #     "humanlikeness_evaluation": json_result_2,
        # }
        # logger.info(f"Judge Model Result: {json_result}")
        # return json_result
        return {}
    
    def _run_judge_doctor_model(self) -> dict[str, int | str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            diagnosis_data=render_diagnosis_data(self.examination_data),
            dialogue_history=self._get_dialogue_history(),
        )

        all_stage_cnt = correct_stage_cnt = 0
        if self.has_expert_knowledge:
            last_patient_stage = ""
            for turn in self.conversation_history:
                if turn["speaker"] == "Patient":
                    last_patient_stage = turn["message"]["stage"]
                    all_stage_cnt += 1
                else:
                    current_doctor_stage = turn["message"]["stage"]
                    if last_patient_stage == current_doctor_stage:
                        correct_stage_cnt += 1

        disease_name = self.examination_data.get("diagnosis", {}).get("disease_name", "")
        stage = self.examination_data.get("diagnosis", {}).get("stage", "")
        plan = self.examination_data.get("treatment", {}).get("plan", "")
        course = self.examination_data.get("treatment", {}).get("course", "")

        format_args_2 = SafeDict(
            disease_name=disease_name,
            stage=stage,
            plan=plan,
            course=course,
            dialogue_history=self._get_dialogue_history(role="Doctor"),
        )

        with ThreadPoolExecutor(max_workers=3) as executor:
            judge_response_1 = executor.submit(
                self.judge_model.chat,
                prompt=JUDGE_DOCTOR_SAFETY_PROMPT.format_map(format_args),
                json_format=True,
            )
            judge_response_2 = executor.submit(
                self.judge_model.chat,
                prompt=JUDGE_DOCTOR_HUMANITY_PROMPT.format_map(format_args),
                json_format=True,
            )
            judge_response_3 = executor.submit(
                self.judge_model.chat,
                prompt=JUDGE_DOCTOR_COVERAGE_PROMPT.format_map(format_args_2),
                json_format=True,
            )

            judge_result_1 = judge_response_1.result()
            judge_result_2 = judge_response_2.result()
            judge_result_3 = judge_response_3.result()

        nominator_3 = denominator = 0
        if disease_name != "":
            denominator += 1
            if judge_result_3.get("disease_name", {}).get("covered", False):
                nominator_3 += 1
        if stage != "":
            denominator += 1
            if judge_result_3.get("stage", {}).get("covered", False):
                nominator_3 += 1
        if plan != "":
            denominator += 1
            if judge_result_3.get("plan", {}).get("covered", False):
                nominator_3 += 1
        if course != "":
            denominator += 1
            if judge_result_3.get("course", {}).get("covered", False):
                nominator_3 += 1

        json_result = {
            "safety_evaluation": judge_result_1,
            "humanity_evaluation": judge_result_2,
            "coverage_evaluation": {
                "covered_points": judge_result_3,
                "coverage_percentage": nominator_3 / denominator * 100,
            },
            "stage_correct_percentage": correct_stage_cnt / (all_stage_cnt - 1) * 100 if all_stage_cnt > 1 else 0,
        }
        logger.info(f"Judge Doctor Model Result: {json_result}")
        return json_result

    def run_conversation(self):
        turn_count = len(self.conversation_history) // 2
        while turn_count < self.max_turns:
            turn_success = False
            try:
                if self.human_in_the_loop:
                    doctor_reply = input("Input Doctor Reply: ")
                    doctor_ret = {
                        "stage": "human_input",
                        "analysis": "human_input",
                        "strategy": "human_input",
                        "response": doctor_reply,
                        "explanation": [],
                    }
                    self.conversation_history.append(
                        {
                            "speaker": "Doctor",
                            "message": doctor_ret,
                        }
                    )
                else:
                    if self.is_baseline:
                        doctor_reply = self._run_baseline_reply_model()
                        doctor_ret = {
                            "stage": "baseline",
                            "analysis": "baseline",
                            "strategy": "baseline",
                            "response": doctor_reply,
                            "explanation": [],
                        }
                        self.conversation_history.append(
                            {
                                "speaker": "Doctor",
                                "message": doctor_ret,
                            }
                        )

                    else:
                        stage, analysis, strategy, keywords = self._run_strategy_model()

                        doctor_reply, explanation = self._run_reply_model(
                            stage, analysis, strategy, keywords
                        )
                        doctor_ret = {
                            "stage": stage,
                            "analysis": analysis,
                            "strategy": strategy,
                            "response": doctor_reply,
                            "explanation": explanation,
                        }
                        self.conversation_history.append(
                            {
                                "speaker": "Doctor",
                                "message": doctor_ret,
                            }
                        )

                patient_ret = self.patient_agent.respond(
                    dialogue_history=self._get_dialogue_history()
                )
                self.conversation_history.append(
                    {
                        "speaker": "Patient",
                        "message": patient_ret,
                    }
                )

                self.patient_scores.append(
                    {
                        "ccs_score": patient_ret.get("ccs_score", 0),
                        "ess_score": patient_ret.get("ess_score", 0),
                        "pas_score": patient_ret.get("pas_score", 0),
                    }
                )

                turn_success = True
            except Exception as e:
                logger.error(f"Unexpected error during negotiation: {e}")

            if not turn_success:
                self.negotiation_result = "error"
                break

            turn_count += 1

            if patient_ret["pas_score"] < 10 or patient_ret["ess_score"] >= 90:
                self.negotiation_completed = True
                self.negotiation_result = "reject"
                break
            if patient_ret["pas_score"] >= 90:
                self.negotiation_completed = True
                self.negotiation_result = "accept"
                break
        
        self.completed_turns = turn_count
        if turn_count >= self.max_turns and not self.negotiation_completed:
            self.negotiation_result = "max_turns_reached"

        if self.do_eval_patient:
            self.judge_patient_scores = self._run_judge_patient_model()
        if self.do_eval_doctor:
            self.judge_doctor_scores = self._run_judge_doctor_model()

    def save_conversation(self, output_dir: str) -> dict:
        output_path = Path(output_dir)
        if self.human_in_the_loop:
            output_path = output_path / "human"
        elif self.is_baseline:
            output_path = output_path / "cot"
        else:
            if self.has_expert_knowledge:
                output_path = output_path / "warm"
            else:
                output_path = output_path / "framework"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / self.file_name

        output_data = {
            "file_name": self.file_name,
            "patient_data": self.patient_data,
            "examination_data": self.examination_data,
            "conversation_history": self.conversation_history,
            "completed_turns": self.completed_turns,
            "negotiation_completed": self.negotiation_completed,
            "negotiation_result": self.negotiation_result,
            "scores": {
                "judge_doctor_scores": self.judge_doctor_scores,
                # "judge_patient_scores": self.judge_patient_scores,
                "patient_scores": self.patient_scores,
            },
            "models": {
                "patient": self.patient_agent.model_name,
                "strategy": self.strategy_model.model_name,
                "reply": self.reply_model.model_name,
                "mdt": self.mdt.model_name,
                "judge": self.judge_model.model_name,
                "url": self.url,
            },
            "parameters": {
                "max_turns": self.max_turns,
                "has_expert_knowledge": self.has_expert_knowledge,
                "human_in_the_loop": self.human_in_the_loop,
                "is_emotional_patient": self.is_emotional_patient,
                "is_baseline": self.is_baseline,
                "do_eval_patient": self.do_eval_patient,
                "do_eval_doctor": self.do_eval_doctor,
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        return output_data
