import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.backend import LanguageModel
from src.emotional_patient import NewEmotionalPatient, NotEmotionalPatient
from src.mdt import MDT
from src.prompt import (
    DOCTOR_BASELINE_REPLY_PROMPT,
    DOCTOR_REPLY_PROMPT,
    DOCTOR_REPLY_PROMPT_WITH_EXPLANATION,
    DOCTOR_STRATEGY_PROMPT,
    DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE,
    JUDGE_DOCTOR_COVERAGE_PROMPT,
    JUDGE_DOCTOR_HUMANITY_PROMPT,
    JUDGE_DOCTOR_REITERATION_PROMPT,
    JUDGE_DOCTOR_SAFETY_PROMPT,
    JUDGE_PATIENT_HUMANLIKENESS_PROMPT,
    JUDGE_PATIENT_PERSONA_PROMPT,
)
from src.utils import SafeDict, logger, render_user_profile


class Conversation:
    def __init__(
        self,
        file_name: str,
        patient_data: dict[str, str],
        diagnosis_data: dict[str, str],
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
    ):
        # patient_data 包含 personal_info、symptom 和 reiterated_symptom
        # diagnosis_data 包含 personal_info、symptom、physical_examination、auxiliary_examination、diagnosis 和 treatment
        self.file_name = file_name
        self.patient_data = patient_data
        self.diagnosis_data = diagnosis_data

        self.strategy_model = LanguageModel(model_name=strategy_model_name, url=url)
        self.reply_model = LanguageModel(model_name=reply_model_name, url=url)
        self.judge_model = LanguageModel(model_name=judge_model_name, url=url)
        self.mdt = MDT(
            model_name=mdt_model_name,
            url=url,
            examination_data=self.diagnosis_data
        )

        self.human_in_the_loop = human_in_the_loop
        self.has_expert_knowledge = has_expert_knowledge
        self.is_emotional_patient = is_emotional_patient
        self.is_baseline = is_baseline
        self.do_eval_patient = do_eval_patient
        self.do_eval_doctor = do_eval_doctor

        self.max_turns = max_turns
        self.negotiation_completed = False
        self.negotiation_result = None  # "accept", "reject", "error"
        self.conversation_history = []
        self.completed_turns = 0
        self.judge_doctor_scores = {}
        self.judge_patient_scores = {}
        self.patient_scores = []

        if self.is_emotional_patient:
            self.patient_agent = NewEmotionalPatient(
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
        self.user_profile = render_user_profile(self.patient_data, "Doctor")

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

    # TODO: 这是给 DPO 的时候生成数据用的

    # def _get_dialogue_history_with_stage(self) -> list[dict[str, str]]:
    #     dialogue_history = []
    #     for turn in self.conversation_history:
    #         if turn["speaker"] == "Doctor":
    #             dialogue_history.append(
    #                 {
    #                     "speaker": "Doctor",
    #                     "message": turn["message"]["response"],
    #                 }
    #             )
    #         else:
    #             dialogue_history.append(
    #                 {"speaker": "Patient", "message": turn["message"]["response"]}
    #             )
    #     return json.dumps(dialogue_history, ensure_ascii=False)

    # def _get_dialogue_history_with_strategy(self) -> list[dict[str, str]]:
    #     dialogue_history = []
    #     for i, turn in enumerate(self.conversation_history):
    #         if turn["speaker"] == "Doctor":
    #             dialogue_history.append(
    #                 {
    #                     "speaker": "Doctor",
    #                     "idx": i // 2,
    #                     "strategy": turn["message"]["strategy"],
    #                     "response": turn["message"]["response"],
    #                 }
    #             )
    #         else:
    #             dialogue_history.append(
    #                 {"speaker": "Patient", "response": turn["message"]["response"]}
    #             )
    #     return json.dumps(dialogue_history, ensure_ascii=False)

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
                prompt = DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE.format_map(format_args),
                json_format=True,
            )
        else:
            format_args = SafeDict(
                user_profile=self.user_profile,
                diagnosis_data=self.diagnosis_data,
                dialogue_history=self._get_dialogue_history(),
            )
            json_result = self.strategy_model.chat(
                prompt = DOCTOR_STRATEGY_PROMPT.format_map(format_args),
                json_format=True,
            )
        # TODO: 这里可能会出现解析错误，增加异常处理
        stage = json_result.get("stage", "no_expert_knowledge")
        analysis = json_result["analysis"]
        strategy = json_result["strategy"]
        keywords = json_result.get("keywords", [])

        logger.info(f"Strategy Model Result: {json_result}")
        return stage, analysis, strategy, keywords

    def _run_reply_model(
        self, analysis: str, strategy: str, keywords: list[str],
    ) -> tuple[str, list[dict[str, str]]]:
        explanation = []
        if len(keywords) > 0:
            explanation = self.mdt.respond(
                keywords=keywords,
            )
            logger.info(f"Explanation Model Result: {explanation}")

            format_args = SafeDict(
                user_profile=self.user_profile,
                diagnosis_data=self.diagnosis_data,
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
                diagnosis_data=self.diagnosis_data,
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
        format_args = SafeDict(
            user_profile=render_user_profile(
                patient_data=self.patient_data,
                role="Doctor",
                with_symptom=False
            ),
            diagnosis_data=self.diagnosis_data,
            dialogue_history=self._get_dialogue_history(),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            judge_patient_persona_future = executor.submit(
                self.judge_model.chat,
                prompt=JUDGE_PATIENT_PERSONA_PROMPT.format_map(format_args),
                json_format=True,
            )
            judge_patient_humanlikeness_future = executor.submit(
                self.judge_model.chat,
                prompt=JUDGE_PATIENT_HUMANLIKENESS_PROMPT.format_map(format_args),
                json_format=True,
            )
            json_result_1 = judge_patient_persona_future.result()
            json_result_2 = judge_patient_humanlikeness_future.result()

        json_result = {
            "persona_evaluation": json_result_1,
            "humanlikeness_evaluation": json_result_2,
        }
        logger.info(f"Judge Model Result: {json_result}")
        return json_result
    
    def _run_judge_doctor_model(self) -> dict[str, int | str]:
        format_args = SafeDict(
            user_profile=self.user_profile,
            diagnosis_data=self.diagnosis_data,
            dialogue_history=self._get_dialogue_history(),
        )

        disease_name = self.diagnosis_data.get("diagnosis", {}).get("disease_name", "")
        stage = self.diagnosis_data.get("diagnosis", {}).get("stage", "")
        plan = self.diagnosis_data.get("treatment", {}).get("plan", "")
        course = self.diagnosis_data.get("treatment", {}).get("course", "")

        format_args_2 = SafeDict(
            disease_name=disease_name,
            stage=stage,
            plan=plan,
            course=course,
            dialogue_history=self._get_dialogue_history(role="Doctor"),
            knowledge=self.patient_agent.state.get("knowledge", []),
        )

        with ThreadPoolExecutor(max_workers=4) as executor:
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
            judge_response_4 = executor.submit(
                self.judge_model.chat,
                prompt=JUDGE_DOCTOR_REITERATION_PROMPT.format_map(format_args_2),
                json_format=True,
            )

            judge_result_1 = judge_response_1.result()
            judge_result_2 = judge_response_2.result()
            judge_result_3 = judge_response_3.result()
            judge_result_4 = judge_response_4.result()

        nominator_3 = nominator_4 = denominator = 0
        if disease_name != "":
            denominator += 1
        if stage != "":
            denominator += 1
        if plan != "":
            denominator += 1
        if course != "":
            denominator += 1
        
        for value in judge_result_3.values():
            nominator_3 += 1 if value["covered"] else 0
        for value in judge_result_4.values():
            nominator_4 += 1 if value["covered"] else 0

        json_result = {
            "safety_evaluation": judge_result_1,
            "humanity_evaluation": judge_result_2,
            "coverage_evaluation": {
                "covered_points": judge_result_3,
                "coverage_percentage": nominator_3 / denominator * 100,
            },
            "reiteration_evaluation": {
                "reiterated_points": judge_result_4,
                "reiteration_percentage": nominator_4 / denominator * 100,
            }
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
                            analysis, strategy, keywords
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

            # TODO: 应该有更优美的写法
            if patient_ret["decision"] == "reject":
                self.negotiation_completed = True
                self.negotiation_result = "reject"
                break
            if patient_ret["decision"] == "accept":
                self.negotiation_completed = True
                self.negotiation_result = "accept"
                break
            if patient_ret["pas_score"] >= 100:
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

        logger.info("\n" + "-" * 50)
        logger.info("Negotiation process completed.")
        logger.info(f"Turns completed: {self.completed_turns}")
        logger.info(f"Negotiation result: {self.negotiation_result}")

    def save_conversation(self, output_dir: str):

        output_path = Path(output_dir)
        if self.human_in_the_loop:
            output_path = output_path / "human"
        elif self.is_baseline:
            output_path = output_path / "baseline"
        else:
            if self.has_expert_knowledge:
                output_path = output_path / "expert_knowledge"
            else:
                output_path = output_path / "no_expert_knowledge"
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / self.file_name

        output_data = {
            "file_name": self.file_name,
            "patient_data": self.patient_data,
            "diagnosis_data": self.diagnosis_data,
            "conversation_history": self.conversation_history,
            "completed_turns": self.completed_turns,
            "negotiation_completed": self.negotiation_completed,
            "negotiation_result": self.negotiation_result,
            "scores": {
                "judge_doctor_scores": self.judge_doctor_scores,
                "judge_patient_scores": self.judge_patient_scores,
                "patient_scores": self.patient_scores,
            },
            "models": {
                "patient": self.patient_agent.model_name,
                "strategy": self.strategy_model.model_name,
                "reply": self.reply_model.model_name,
                "mdt": self.mdt.model_name,
                "judge": self.judge_model.model_name,
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
    
    # TODO: 这是给前端界面用的

    # def replay_from_turn(self, turn_index: int, new_doctor_message: str = None):
    #     """
    #     Replay the conversation from a specific turn, optionally with a modified doctor message.
        
    #     Args:
    #         turn_index (int): The turn index to replay from (0-based).
    #         new_doctor_message (str, optional): If provided, replace the doctor's message at this turn.
    #     """
    #     if turn_index < 0 or turn_index >= len(self.conversation_history):
    #         logger.error(f"Invalid turn_index: {turn_index}")
    #         return
        
    #     # Truncate conversation history to the specified turn
    #     self.conversation_history = self.conversation_history[:turn_index]
        
    #     # If a new doctor message is provided, we'll need to regenerate from this point
    #     if new_doctor_message:
    #         # Find the last doctor turn and update it
    #         for i in range(len(self.conversation_history) - 1, -1, -1):
    #             if self.conversation_history[i]["speaker"] == "Doctor":
    #                 self.conversation_history[i]["message"]["response"] = new_doctor_message
    #                 logger.info(f"Updated doctor message at turn {i}")
    #                 break
        
    #     # Reset negotiation state
    #     self.negotiation_completed = False
    #     self.negotiation_result = None
    #     self.completed_turns = len(self.conversation_history)
        
    #     logger.info(f"Replaying from turn {turn_index}, conversation history truncated to {len(self.conversation_history)} turns")

# def load_conversation(json_path: str) -> Conversation:
#     """
#     Load a conversation from a saved JSON file.
    
#     Args:
#         json_path (str): Path to the saved conversation JSON file.
    
#     Returns:
#         None
#     """
#     with open(json_path, encoding="utf-8") as f:
#         data = json.load(f)
    
#     # Create a new Conversation instance with the loaded data
#     conversation = Conversation(
#         patient_id=data["patient_id"],
#         patient_data=data["patient_data"],
#         diagnosis_id=data["diagnosis_id"],
#         diagnosis_data=data["diagnosis_data"],
#         examination_data=data.get("examination_data", {}),
#         diagnosis_keypoints=data.get("diagnosis_keypoints", []),
#         patient_model_name=data["models"]["patient"],
#         strategy_model_name=data["models"]["strategy"],
#         reply_model_name=data["models"]["reply"],
#         mdt_model_name=data["models"]["mdt"],
#         judge_model_name=data["models"]["judge"],
#         max_turns=data["parameters"]["max_turns"],
#         human_in_the_loop=data["parameters"]["human_in_the_loop"],
#         has_expert_knowledge=data["parameters"]["has_expert_knowledge"],
#         is_emotional_patient=data["parameters"]["is_emotional_patient"],
#         is_baseline=data["parameters"]["is_baseline"],
        
#         do_eval_patient=data["parameters"]["do_eval_patient"],
#         do_eval_doctor=data["parameters"]["do_eval_doctor"],
#     )
    
#     conversation.user_profile = data["user_profile"]
#     if conversation.is_emotional_patient:
#         conversation.patient_agent = NewEmotionalPatient(
#             user_profile=conversation.user_profile,
#             model_name=conversation.patient_model_name,
#         )
#     else:
#         conversation.patient_agent = NotEmotionalPatient(
#             user_profile=conversation.user_profile,
#             model_name=conversation.patient_model_name,
#         )

#     # Restore conversation state
#     conversation.judge_doctor_scores = data["scores"]["judge_doctor_scores"]
#     conversation.judge_patient_scores = data["scores"]["judge_patient_scores"]
#     conversation.patient_scores = data["scores"]["patient_scores"]
#     conversation.conversation_history = data["conversation_history"]
#     conversation.completed_turns = data["completed_turns"]
#     conversation.negotiation_completed = data["negotiation_completed"]
#     conversation.negotiation_result = data["negotiation_result"]
    
#     logger.info(f"Loaded conversation with {len(conversation.conversation_history)} turns from {json_path}")

#     return conversation
