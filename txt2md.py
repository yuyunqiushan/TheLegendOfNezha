import re

# 读取文本文件并转换为 Markdown 格式
def txt_to_md(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as f_md:
        for line in lines:
            # 匹配一级标题 "第XX（中文数字）集"
            match_level_1 = re.match(r'第([一二三四五六七八九十]+)集', line.strip())
            if match_level_1:
                # 保持中文数字不变，写入 Markdown 一级标题
                f_md.write(f'# 第{match_level_1.group(1)}集\n\n')  # 一级标题
            # 匹配二级标题 "1、"、"2、" 等，将 "、" 替换为 "."
            elif re.match(r'^\d+、', line.strip()):
                new_line = line.strip().replace('、', '.')  # 将 "、" 替换为 "."
                f_md.write(f'## {new_line}\n\n')  # 二级标题
            else:
                # 其他普通文本内容，直接写入
                f_md.write(f'{line.strip()}\n\n')

    print(f"文件已成功转换为 {output_file}")

# 使用示例
input_file = '《哪吒传奇》文学剧本.txt'   # 输入的文本文件
output_file = '《哪吒传奇》文学剧本.md'  # 输出的 Markdown 文件
txt_to_md(input_file, output_file)