import argparse
import glob
import json
import os

# 1. 带分页功能和标题的 CSS 样式
html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>合并聊天记录</title>
    <style>
        body {{
            /* 保证打印或导出 PDF 时背景色能正常显示 */
            -webkit-print-color-adjust: exact; 
            print-color-adjust: exact;
            background-color: #ededed; 
            font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        /* 【新增】分页容器 */
        .page {{
            page-break-after: always; /* 强制分页 */
            padding: 5px; 
            box-sizing: border-box;
        }}
        /* 最后一页不需要多余的空白页 */
        .page:last-child {{
            page-break-after: auto;
        }}
        /* 【新增】左上角黑体标题 */
        .page-title {{
            font-family: "SimHei", "Heiti SC", "Microsoft YaHei", sans-serif; /* 优先使用黑体 */
            font-weight: bold;
            font-size: 14px;
            color: #000000;
            margin-bottom: 6px;
            text-align: left;
        }}
        .chat-container {{
            display: flex;
            flex-direction: column;
            gap: 6px; 
        }}
        .message-row {{
            display: flex;
            width: 100%;
        }}
        .patient-row {{
            justify-content: flex-start;
        }}
        .doctor-row {{
            justify-content: flex-end;
        }}
        .message {{
            display: flex;
            align-items: flex-start;
            max-width: 98%; 
        }}
        .doctor-row .message {{
            flex-direction: row-reverse;
        }}
        .avatar {{
            width: 18px; 
            height: 18px;
            border-radius: 3px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            color: white;
            font-size: 10px; 
            flex-shrink: 0;
        }}
        .patient-row .avatar {{
            background-color: #bbbbbb;
            margin-right: 4px; 
        }}
        .doctor-row .avatar {{
            background-color: #07c160; 
            margin-left: 4px;
        }}
        .bubble {{
            padding: 4px 6px; 
            border-radius: 4px;
            font-size: 10px; 
            line-height: 1.15; 
            word-wrap: break-word;
            word-break: break-all;
            max-width: 92%; 
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        .patient-row .bubble {{
            background-color: #ffffff; 
            color: #333333;
        }}
        .doctor-row .bubble {{
            background-color: #95ec69; 
            color: #111111;
        }}
    </style>
</head>
<body>
    {all_pages_content}
</body>
</html>
"""

def process_multiple_jsons_to_single_html(json_file_paths, output_html_name="Combined_Chats.html"):
    print(f"准备合并 {len(json_file_paths)} 个 JSON 文件...")
    
    all_pages_html = ""
    
    for page_index, json_file_path in enumerate(json_file_paths, start=1):
        print(f"正在读取文件 [{page_index}/{len(json_file_paths)}]: {json_file_path} ...")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # 获取单条记录（兼容列表和字典格式）
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
            elif isinstance(data, dict):
                item = data
            else:
                print(f"⚠️ {json_file_path} 格式未知，已跳过。")
                continue
                
            history = item.get("conversation_history", [])
            
            if not history:
                print(f"⚠️ {json_file_path} 中未找到对话历史，已跳过。")
                continue
                
            chat_content = ""
            
            # 提取当前文件的对话
            for turn in history:
                speaker = turn.get("speaker")
                message_dict = turn.get("message", {})
                text = message_dict.get("response", "") if isinstance(message_dict, dict) else ""
                
                if not text:
                    continue
                    
                if speaker == "Doctor":
                    chat_content += f"""
                    <div class="message-row doctor-row">
                        <div class="message">
                            <div class="avatar">医</div>
                            <div class="bubble">{text}</div>
                        </div>
                    </div>
                    """
                elif speaker == "Patient":
                    chat_content += f"""
                    <div class="message-row patient-row">
                        <div class="message">
                            <div class="avatar">患</div>
                            <div class="bubble">{text}</div>
                        </div>
                    </div>
                    """
            
            # 【核心修改点】将当前文件的对话包裹在 page 容器中，并加上左上角标题
            page_html = f"""
            <div class="page">
                <div class="page-title">对话{page_index}</div>
                <div class="chat-container">
                    {chat_content}
                </div>
            </div>
            """
            
            all_pages_html += page_html
            
        except FileNotFoundError:
            print(f"❌ 找不到文件: {json_file_path}")
        except json.JSONDecodeError as e:
            print(f"❌ {json_file_path} JSON 格式错误: {e}")
        except Exception as e:
            print(f"❌ 处理 {json_file_path} 时发生意外错误: {e}")

    # 将所有生成的页面内容嵌入到主 HTML 模板中
    final_html = html_template.format(all_pages_content=all_pages_html)
    
    print(f"正在生成最终 HTML: {output_html_name} ...")
    with open(output_html_name, 'w', encoding='utf-8') as f:
        f.write(final_html)
        
    print(f"✅ 成功保存为 {output_html_name}！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='合并目录下的 JSON 聊天记录为单个 HTML 文件')
    parser.add_argument('--input_dir', help='要合并的 JSON 文件所在目录（例如: "warm 9"）')
    parser.add_argument('--output', default='Combined_Chats_5_Pages.html', help='输出 HTML 文件名')
    parser.add_argument('--limit', type=int, default=0, help='最多处理多少个文件；0 表示全部')
    parser.add_argument('--recursive', action='store_true', help='是否递归查找子目录中的 JSON 文件')
    args = parser.parse_args()

    if args.input_dir:
        pattern = '**/*.json' if args.recursive else '*.json'
        search_path = os.path.join(args.input_dir, pattern)
        json_paths = glob.glob(search_path, recursive=args.recursive)
        json_paths = [p for p in json_paths if os.path.isfile(p)]
        json_paths.sort()
        if args.limit and args.limit > 0:
            json_paths = json_paths[:args.limit]

        if not json_paths:
            print(f"❌ 未在目录 {args.input_dir} 中找到 JSON 文件。")
        else:
            print(f"找到 {len(json_paths)} 个 JSON 文件，正在合并到 {args.output}...")
            process_multiple_jsons_to_single_html(json_paths, args.output)
    else:
        # 如果未提供 --input_dir，则保留原有的示例文件列表（可按需修改）
        my_json_files = [
            "warm 9/1_case.json",
            "warm 9/2_case.json",
            "warm 9/3_case.json",
            "warm 9/4_case.json",
            "warm 9/5_case.json"
        ]
        process_multiple_jsons_to_single_html(my_json_files, args.output)
