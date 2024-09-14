import re
import chardet
import json
import subprocess
import os

class LatexGenerator:
    def __init__(self, config_file):
        self.load_config(config_file)

    def load_config(self, config_file):
        """
        从 JSON 配置文件中加载配置信息
        :param config_file: 配置文件路径
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.input_file = config["input_file"]
        self.config_file = config["config_file"]
        self.compiler = config["compiler"]
        
        # 固定 tex 文件名为 output.tex
        self.output_tex_file = "output.tex"
        
        # 生成 PDF 文件名，使用输入文件名 + "LaTeX排版"
        input_file_name = os.path.splitext(os.path.basename(self.input_file))[0]
        self.output_pdf_file = input_file_name + "_LaTeX排版.pdf"

    def detect_encoding(self):
        """
        自动检测文件编码
        :return: 检测到的文件编码
        """
        with open(self.input_file, 'rb') as f:
            rawdata = f.read(10000)  # 读取最开始的一部分数据用于检测
        result = chardet.detect(rawdata)
        return result['encoding']

    def parse_text_file(self):
        """
        解析文本文件，提取章节和小节内容
        :return: 章节列表，每个章节包含标题和小节内容
        """
        encoding = self.detect_encoding()
        print(f"检测到的编码: {encoding}")

        chapters = []
        current_chapter = None
        current_section = None
        current_content = []

        with open(self.input_file, 'r', encoding=encoding) as f:
            for line in f:
                line = line.strip()

                # 检测章节标题
                if re.match(r"^第[一二三四五六七八九十百千万]+集", line):
                    # 如果有当前章节，保存它
                    if current_chapter:
                        if current_section:
                            current_chapter['sections'].append((current_section, current_content))
                        chapters.append(current_chapter)

                    # 在 "第X集" 后添加空格，保持 "第X集" 形式不变
                    chapter_title = re.sub(r"(第[一二三四五六七八九十百千万]+集)", r"\1 ", line)

                    # 开始新的章节
                    current_chapter = {
                        'chapter_title': chapter_title,
                        'sections': []
                    }
                    current_section = None
                    current_content = []

                # 检测小节标题，替换 "、" 为 "."
                elif re.match(r"^\d+、", line):
                    # 如果有当前小节，保存它
                    if current_section:
                        current_chapter['sections'].append((current_section, current_content))

                    # 替换小节标题中的 "、" 为 "."
                    section_title = re.sub(r"、", ".", line)

                    # 开始新的小节
                    current_section = section_title
                    current_content = []

                # 处理正文
                elif line:
                    current_content.append(line)

            # 捕捉最后一个章节和小节
            if current_chapter:
                if current_section:
                    current_chapter['sections'].append((current_section, current_content))
                chapters.append(current_chapter)

        return chapters

    def generate_latex(self, chapters):
        """
        根据章节数据生成 LaTeX 文档内容
        :param chapters: 从文本文件解析出的章节数据
        :return: LaTeX 文本
        """
        # 获取 LaTeX 文档的头部定义
        latex_start = self.get_latex_start()
    
        latex_body = ""
    
        # 遍历每个章节
        for chapter in chapters:
            # 保持章节标题格式一致
            chapter_title = chapter['chapter_title']
    
            # 在正文中使用不可断开的空格 "~"
            chapter_title_with_nonbreaking_space = chapter_title.replace(" ", "~")
            
            # 在目录中使用 LaTeX 可断开的空格 "\ "
            chapter_title_with_breakable_space = chapter_title.replace(" ", r"\ ")
    
            # \chapter[目录中的章节标题]{正文中的章节标题}
            latex_body += f"\n\\chapter[{chapter_title_with_breakable_space}]{{{chapter_title_with_nonbreaking_space}}}\n"
            # 使用 \markboth 而不是 \chaptermark 来确保章节标题显示在页眉中
            latex_body += f"\\markboth{{{chapter_title_with_nonbreaking_space}}}{{}}\n"
    
            # 遍历章节中的每个小节
            for section_title, content in chapter['sections']:
                # 使用 \numfont 包裹数字来显示 Times New Roman 字体
                section_title = re.sub(r"(\d+)", r"\\numfont{\1}", section_title)
                latex_body += f"\\subsection*{{{section_title}}}\n"  # 使用大标题并另起一行
    
                # 将段落内容补充到章节中
                for paragraph in content:
                    latex_body += paragraph + "\n\n"  # 确保段落之间有空行
    
        latex_end = r"""
    \end{document} % 结束文档
            """
        return latex_start + latex_body + latex_end

    def get_latex_start(self):
        """
        从配置文件中读取 LaTeX 文档的头部定义
        :return: LaTeX 文档头部定义
        """
        with open(self.config_file, 'r', encoding='utf-8') as f:
            latex_start = f.read()
        return latex_start

    def save_latex_file(self, latex_code):
        """
        将生成的 LaTeX 文件保存到输出路径
        :param latex_code: 生成的 LaTeX 文本
        """
        with open(self.output_tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        print(f"LaTeX 文件 '{self.output_tex_file}' 生成成功！")

    def compile_pdf(self):
        """
        调用 LaTeX 编译器生成 PDF 文件，至少编译两次以确保目录正确生成
        """
        try:
            # 第一次编译，保持 tex 文件名为 output.tex，使用自定义的 PDF 文件名
            subprocess.run(
                [self.compiler, "-jobname", os.path.splitext(self.output_pdf_file)[0], self.output_tex_file],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"第一次编译成功，生成了 PDF 文件 '{self.output_pdf_file}' 和辅助文件（如 .toc）。")

            # 第二次编译，确保目录生成
            subprocess.run(
                [self.compiler, "-jobname", os.path.splitext(self.output_pdf_file)[0], self.output_tex_file],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"第二次编译成功，目录已经生成。")
        except subprocess.CalledProcessError as e:
            print(f"编译 PDF 失败: {e.stderr.decode('utf-8')}")
        except FileNotFoundError:
            print(f"编译器 {self.compiler} 未找到，请确保已正确安装 LaTeX 发行版。")

    def run(self):
        """
        运行整个生成流程
        """
        # 解析文本文件
        chapters = self.parse_text_file()
        # 生成 LaTeX 文本
        latex_code = self.generate_latex(chapters)
        # 输出 LaTeX 文件
        self.save_latex_file(latex_code)
        # 编译成 PDF
        self.compile_pdf()

if __name__ == "__main__":
    config_file = 'config.json'
    generator = LatexGenerator(config_file)
    generator.run()