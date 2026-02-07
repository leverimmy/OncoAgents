from .mdt import MDT

if __name__ == '__main__':
    mdt_agent = MDT(model_name="gpt-4o", url=None, examination_data={
        "CT 检查结果": "右肺下叶有一个2cm的结节，边界不清。另外通过基因检测发现患者存在 EGFR 19 exon deletion 突变，PD-L1 表达水平为 30%。推断为非小细胞肺癌。",
    })
    result = mdt_agent.respond(
        keywords=[
            "CT 检查结果显示右肺下叶有一个2cm的结节，边界不清。",
            "非小细胞肺癌相关的肿瘤标志物",
        ],
    )
    print(result)
