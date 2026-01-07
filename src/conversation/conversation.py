import json
import os

from autogen_agentchat.messages import UserMessage

from src.backend import get_client
from src.emotional_patient import EmotionalPatient, NotEmotionalPatient
from src.json_schema import STRATEGY_JSON_SCHEMA, TOM_REASONING_JSON_SCHEMA
from src.prompt import (
    DOCTOR_REPLY_PROMPT,
    DOCTOR_STRATEGY_PROMPT,
    DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE,
    DOCTOR_TOM_PROMPT,
    STAGE_TO_EXPERT_KNOWLEDGE,
)
from src.utils import logger


class Conversation:
    def __init__(
        self,
        patient_id: str,
        patient_data: str,
        diagnosis_id: str,
        diagnosis_data: dict[str, str],
        patient_model_name: str,
        strategy_model_name: str,
        reply_model_name: str,
        tom_model_name: str,
        max_turns: int = 20,
        human_in_the_loop: bool = False,
        has_expert_knowledge: bool = False,
        is_emotional_patient: bool = True,
    ) -> None:
        self.patient_id = patient_id
        self.patient_data = patient_data
        self.diagnosis_id = diagnosis_id
        self.diagnosis_data = diagnosis_data

        self.patient_model_name = patient_model_name
        self.is_emotional_patient = is_emotional_patient
        if is_emotional_patient:
            self.patient_agent = EmotionalPatient(
                user_profile=patient_data, model_name=patient_model_name
            )
        else:
            self.patient_agent = NotEmotionalPatient(
                user_profile=patient_data, model_name=patient_model_name
            )
        self.strategy_model_name = strategy_model_name
        self.strategy_model = get_client(strategy_model_name)
        self.reply_model_name = reply_model_name
        self.reply_model = get_client(reply_model_name)
        self.tom_model_name = tom_model_name
        self.tom_model = get_client(tom_model_name)

        self.human_in_the_loop = human_in_the_loop
        self.has_expert_knowledge = has_expert_knowledge

        self.max_turns = max_turns
        self.negotiation_completed = False
        self.negotiation_result = None  # "accept", "reject", "error"
        self.conversation_history = []
        self.completed_turns = 0
        self.judge_scores = []
        self.patient_scores = []

        self.doctor_strategy_prompt = DOCTOR_STRATEGY_PROMPT
        self.doctor_reply_prompt = DOCTOR_REPLY_PROMPT
        self.doctor_strategy_prompt_with_expert_knowledge = (
            DOCTOR_STRATEGY_PROMPT_WITH_EXPERT_KNOWLEDGE
        )
        self.doctor_tom_prompt = DOCTOR_TOM_PROMPT

    def _get_dialogue_history(self) -> str:
        dialogue_history = []
        for turn in self.conversation_history:
            if turn["speaker"] == "Doctor":
                dialogue_history.append(
                    {"speaker": "Doctor", "message": turn["message"]["response"]}
                )
            else:
                dialogue_history.append(
                    {"speaker": "Patient", "message": turn["message"]["response"]}
                )
        return json.dumps(dialogue_history, ensure_ascii=False)

    def _get_dialogue_history_with_stage(self) -> str:
        dialogue_history = []
        for turn in self.conversation_history:
            if turn["speaker"] == "Doctor":
                dialogue_history.append(
                    {
                        "speaker": "Doctor",
                        "message": turn["message"]["response"],
                        "stage": turn["stage"],
                    }
                )
            else:
                dialogue_history.append(
                    {"speaker": "Patient", "message": turn["message"]["response"]}
                )
        return json.dumps(dialogue_history, ensure_ascii=False)

    async def _run_dialogue(self) -> str:
        """
        Run the dialogue model to generate the next utterance.

        Args:
        Returns:
            str: The generated patient *structured return*.
        """

        patient_ret = await self.patient_agent.respond(
            dialogue_history=self._get_dialogue_history()
        )
        logger.info(f"Patient Return: {patient_ret}")
        return patient_ret

    async def _run_tom_reasoning(self) -> dict[str, str]:
        stage_prompt = self.doctor_tom_prompt.format(
            dialogue_history=self._get_dialogue_history_with_stage()
        )
        tom_reasoning = await self.tom_model.create(
            messages=[UserMessage(content=stage_prompt, source="User")],
            json_output=TOM_REASONING_JSON_SCHEMA,
        )
        json_result = json.loads(tom_reasoning.content)
        logger.info(f"ToM Reasoning Result: {json_result}")
        return json_result

    async def _run_strategy_model(self, stage: str, analysis: str) -> tuple[str, str]:
        """
        Run the strategy model to determine the strategy based on the current stage and analysis.

        Args:
            stage (str): The current stage of the conversation.
            analysis (str): The analysis from previous steps.
        Returns:
            Tuple[str, str]: The generated analysis and strategy.
        """
        if self.has_expert_knowledge:
            prompt = self.doctor_strategy_prompt_with_expert_knowledge.format(
                diagnosis_data=self.diagnosis_data,
                dialogue_history=self._get_dialogue_history(),
                expert_knowledge=STAGE_TO_EXPERT_KNOWLEDGE[stage],
                patient_analysis=analysis,
            )
        else:
            prompt = self.doctor_strategy_prompt.format(
                diagnosis_data=self.diagnosis_data,
                dialogue_history=self._get_dialogue_history(),
            )

        strategy = await self.strategy_model.create(
            messages=[UserMessage(content=prompt, source="User")],
            json_output=STRATEGY_JSON_SCHEMA,
        )
        json_result = json.loads(strategy.content)
        analysis = json_result["analysis"]
        strategy = json_result["strategy"]
        logger.info(f"Strategy Model Result: {json_result}")
        return analysis, strategy

    async def _run_reply_model(self, analysis: str, strategy: str) -> dict[str, str]:
        """
        Run the reply model to generate a reply based on analysis and strategy.

        Args:
            analysis (str): The analysis from previous steps.
            strategy (str): The strategy to be employed.
        Returns:
            str: The generated reply.
        """

        prompt = self.doctor_reply_prompt.format(
            diagnosis_data=self.diagnosis_data,
            dialogue_history=self._get_dialogue_history(),
            analysis=analysis,
            strategy=strategy,
        )

        reply = await self.reply_model.create(
            messages=[UserMessage(content=prompt, source="User")],
        )
        logger.info(f"Reply Model Result: {reply.content}")
        return reply.content

    async def run_conversation(self):
        """
        Run the conversation loop.
        """

        turn_count = 0
        while turn_count < self.max_turns:
            turn_success = False
            try:
                if not self.human_in_the_loop:
                    if self.has_expert_knowledge:
                        if turn_count == 0:
                            tom_reasoning = {
                                "patient_analysis": "null",
                                "stage": "认知与邀请阶段",
                            }
                        else:
                            tom_reasoning = await self._run_tom_reasoning()
                        stage = tom_reasoning["stage"]
                        patient_analysis = tom_reasoning["patient_analysis"]

                        analysis, strategy = await self._run_strategy_model(
                            stage=stage,
                            analysis=patient_analysis,
                        )
                    else:
                        tom_reasoning = {
                            "patient_analysis": "human_input",
                            "stage": "human_input",
                        }
                        analysis, strategy = await self._run_strategy_model(
                            stage="",
                            analysis="",
                        )

                    doctor_reply = await self._run_reply_model(analysis, strategy)
                    doctor_ret = {
                        "analysis": analysis,
                        "strategy": strategy,
                        "response": doctor_reply,
                    }
                    self.conversation_history.append(
                        {
                            "speaker": "Doctor",
                            "tom_reasoning": tom_reasoning,
                            "message": doctor_ret,
                        }
                    )
                else:
                    doctor_reply = input("Input Doctor Reply: ")
                    doctor_ret = {
                        "analysis": "human_input",
                        "strategy": "human_input",
                        "response": doctor_reply,
                    }
                    self.conversation_history.append(
                        {
                            "speaker": "Doctor",
                            "tom_reasoning": {
                                "patient_analysis": "human_input",
                                "stage": "human_input",
                            },
                            "message": doctor_ret,
                        }
                    )

                patient_ret = await self._run_dialogue()

                self.conversation_history.append(
                    {"speaker": "Patient", "message": patient_ret}
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

        logger.info("\n" + "-" * 50)
        logger.info("Negotiation process completed.")
        logger.info(f"Turns completed: {self.completed_turns}")
        logger.info(f"Negotiation result: {self.negotiation_result}")

        return {
            # "judge_scores": self.judge_scores,
            "patient_scores": self.patient_scores,
            "negotiation_result": self.negotiation_result,
            "completed_turns": self.completed_turns,
        }

    def save_conversation(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(
            output_dir, f"dia{self.diagnosis_id}_patient{self.patient_id}.json"
        )

        output_data = {
            "diagnosis_id": self.diagnosis_id,
            "diagnosis_data": self.diagnosis_data,
            "patient_id": self.patient_id,
            "patient_data": self.patient_data,
            "conversation_history": self.conversation_history,
            "completed_turns": self.completed_turns,  # Include the actual number of turns
            "negotiation_completed": self.negotiation_completed,  # Whether negotiation reached conclusion
            "negotiation_result": self.negotiation_result,  # Result of the negotiation
            "models": {
                "patient": self.patient_model_name,
                "strategy": self.strategy_model_name,
                "reply": self.reply_model_name,
                "tom": self.tom_model_name,
            },
            "parameters": {
                "max_turns": self.max_turns,
                "has_expert_knowledge": self.has_expert_knowledge,
                "human_in_the_loop": self.human_in_the_loop,
                "is_emotional_patient": self.is_emotional_patient,
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
