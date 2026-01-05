import asyncio
import json
import os
from MDT import *
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from typing import Dict
from MDT import initialize_agent_memory

# ---------- helpers ----------
async def init_rag():
    """Initialize RAG memory for all agents."""
    # Assuming running from src/
    base_kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_base")
    
    agents_map = {
        "radiologist": "radiologist",
        "pathologist": "pathologist",
        "radiation_oncologist": "radiation_oncologist",
        "surgeon": "surgeon",
        "medical_oncologist": "medical_oncologist",
        "chief_expert": "chief_expert"
    }
    
    print("Initializing RAG knowledge bases...")
    for agent_key, folder_name in agents_map.items():
        folder_path = os.path.join(base_kb_path, folder_name)
        await initialize_agent_memory(agent_key, folder_path)
    print("RAG initialization complete.")

def parse_patient_case(case: Dict[str, str]) -> str:
    ratings = case.get("physical_examination", {}).get("ratings", {}) or {}
    barthel = ratings.get("Barthel", "未提供")
    kps = ratings.get("KPS", "未提供")
    nrs = ratings.get("NRS2002", "未提供")

    # 辅助检查展开
    aux = case.get("auxiliary_examination", []) or []
    aux_blocks = []
    for i, it in enumerate(aux, 1):
        aux_blocks.append(
            f"""【辅助检查 {i}】
- 检查类型：{it.get("check_type", "")}
- 项目/部位：{it.get("item", "")}
- 结果：
  {it.get("result", "")}
""".strip()
        )
    """
{"- 影像/病理/检查结论：" if it.get("diagnosis", "") != "" else ""}
  {it.get("diagnosis", "")}
    """
    aux_text = "\n\n".join(aux_blocks) if aux_blocks else "（无）"
    """
【病例信息（结构化）】

一、个人信息
- personal_info：{case.get("personal_info", "")}

二、主诉与现病史
- 主诉：{case.get("medical_history", {}).get("main_complaint", "")}
- 现病史：{case.get("medical_history", {}).get("present_illness", "")}
    """
    patient_case = f"""
一、既往史与相关史
- 既往史：{case.get("medical_history", {}).get("past_illness", "")}
- 过敏史：{case.get("medical_history", {}).get("allergy_history", "")}
- 个人史：{case.get("medical_history", {}).get("personal_history", "")}
- 婚育史：{case.get("medical_history", {}).get("marriage_childbearing_history", "")}
- 家族史：{case.get("medical_history", {}).get("family_history", "")}

二、体格检查
- 基本生命体征/体格：{case.get("physical_examination", {}).get("basic_info", "")}
- 功能/营养相关评分：
  - Barthel：{barthel}
  - KPS：{kps}
  - NRS2002：{nrs}
- 一般情况：
  {case.get("physical_examination", {}).get("general_condition", "")}
- 专科查体：
  {case.get("physical_examination", {}).get("special_examination", "")}

三、辅助检查（按时间/类型汇总）
{aux_text}
"""
    return patient_case.strip()

async def main() -> None:
    # await init_rag()
    with open("../data/patient_cases_real/patient_case_real.json", "r", encoding="utf-8") as f:
        patient_case = json.load(f)
        # print(parse_patient_case(patient_case))
        text_termination = TextMentionTermination("CONSENSUS ACHIEVED")
        groupchat = RoundRobinGroupChat(
            participants=[
                radiologist_agent,
                pathologist_agent,
                radiation_oncologist_agent,
                surgeon_agent,
                medical_oncologist_agent,
                chief_expert_agent,
                user_proxy,
            ],
            termination_condition=text_termination,
        )
        task = f"""你是一支多学科肿瘤诊疗团队（MDT）。请基于以下结构化病例信息，协同制定诊疗决策。
【病例信息】
{parse_patient_case(patient_case)}
""".strip()
        response = await Console(groupchat.run_stream(task=task))

        os.makedirs("../data/reports", exist_ok=True)
        with open("../data/reports/patient_case_real_report.txt", "w", encoding="utf-8") as report_file:
            report_file.write(response.messages[-1].content)


if __name__ == '__main__':
    asyncio.run(main())
