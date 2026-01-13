import asyncio

from autogen_agentchat.messages import UserMessage


from src.backend import get_client
from src.prompt import DOCTOR_REPLY_PROMPT, DOCTOR_REPLY_PROMPT_WITH_EXPLANATION

diagnosis_data = {
    "症状": {
        "chief_complaint": "1月+前无明显诱因出现咳嗽，无咳痰，不伴心悸、气促、乏力、咯血、胸痛、头痛、恶心、呕吐等不适。症状进行性加重，2天前无明显诱因出现左侧胸背痛。",
        "additional_symptom": "",
        "symptom_duration": "咳嗽1月+，左侧胸背痛2天。"
    },
    "诊断结果": "左肺恶性肿瘤(cT4N3M1a IVA期)",
    "治疗方案": "有新辅助治疗指征，未见明显化疗治疗禁忌，卡铂400mg d1+紫杉醇210mg d1+替雷利珠单抗200mg d1。期间予抑酸、止吐、补液等对症支持治疗。",
}

dialogue_history = [
    {"speaker": "Doctor", "message": "我想先了解一下，您目前对检查结果或病情有什么了解和想法吗？您现在愿意我详细介绍诊断和后续治疗安排吗？"},
    {"speaker": "Patient", "message": "医生，我现在还不太明白情况，有点担心，请您详细讲讲病情和治疗，尽量说得简单些。"},
]

analysis = "患者对病情了解有限，但已主动请求详细解释，表明其认知处于准备阶段。患者情绪有焦虑，但尚可控，未见强烈情绪宣泄，因此适合继续知识传递。由于患者学历水平不高，应当用通俗易懂的语言，避开专业术语。"

strategy = "先回应情绪，再讲依据来源。语言必须通俗易懂，不允许出现专业术语。给出诊断结果，用 CT 报告辅助解释。"

explanation = """{
    "check_type": "医学影像（CT）检查",
    "item": "下腹部CT平扫加增强（薄层），上腹部CT平扫加增强（含薄层），胸部CT平扫加增强（含层）",
    "result": "胸廓对称，气管居中，双肺肺纹理稍增多。左肺门及左肺上叶、邻近纵隔内软组织密度肿块影，与左肺门及邻近纵隔淋巴结、远端肺实变不张分界不清，大小不易精确测量，增强呈不均匀强化；病灶包埋或紧贴部分支气管及动静脉，致部分支气管狭窄或闭塞，部分动静脉狭窄或显示不清；病灶远侧肺内见斑片、片结影、实变不张影。左肺下叶后基底段见一实性渮小结节影，径约0.3cm，强化不易评价。余纵隔内及右肺门、右锁骨上区数个小及稍大淋巴结，大者短径约0.8cm。心脏形态大小未见异常，心包及左侧胸腔少量积液。右侧胸腔未见积液。左侧胸膜稍增厚。\n肝脏形态、大小未见异常，肝内数个低密度无强化小结节，大者径约0.5cm；肝右叶另见点状高密度影。胆囊不大，壁未见明显增厚，囊腔内未见异常密度影；肝内外胆管未见明显扩张。脾脏形态、大小未见异常，实质密度均匀，增强后未见明显异常强化灶。胰形态、大小未见异常，实质密度均匀，胰周脂肪间隙清晰。双肾各见一低密度无强化小结节大者径约0.3cm。腹膜后未见明显肿大淋巴结影。腹腔未见游离液性密度影。胃呈收缩相，胃壁可疑稍厚。",
    "diagnosis": "胸上下腹部CT平扫及增强（含薄层）：\n1. 左肺门及左肺上叶、邻近纵隔内软组织肿块影，考虑肿瘤性病变可能，结合临床及其他检查；伴左肺上叶阻塞性炎变、实变不张，其内部分片结影性质待定，密切随诊。\n2. 左肺门及纵隔内多发增大淋巴结，余纵隔内及右肺门、右锁骨上区数个小及稍大淋巴结。\n3. 左肺下叶后基底段微小结节，随诊。\n4. 心包微少量积液：左侧胸腔少量积液，左侧胸膜稍增厚。\n5. 肝内小囊肿可能；肝内钙化灶；双肾小囊肿；随诊。\n6. 胃呈收缩相，胃壁可疑稍厚，结合临床随诊。"
},"""

async def main():
    reply_model = get_client("gpt-5-mini")

    prompt = DOCTOR_REPLY_PROMPT_WITH_EXPLANATION.format(
        diagnosis_data=diagnosis_data,
        dialogue_history=dialogue_history,
        analysis=analysis,
        strategy=strategy,
        explanation=explanation,
    )

    reply = await reply_model.create(
        messages=[UserMessage(content=prompt, source="User")],
    )
    print(f"Reply Model Result: {reply.content}")

if __name__ == '__main__':
    asyncio.run(main())
