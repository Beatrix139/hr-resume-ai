import streamlit as st
import docx
from pypdf import PdfReader  # 用于解析PDF
from openai import OpenAI  # DeepSeek官方推荐使用OpenAI SDK进行标准对接

# 1. 页面基本配置
st.set_page_config(page_title="AI智能眼业务-HR招聘助手", layout="wide")
st.title("👁️ AI智能眼睛业务 - 简历精准匹配系统 (DeepSeek版)")
st.caption("已支持 PDF/Word/TXT，一键调用 DeepSeek 接口生成深度匹配报告与面试提纲")

# 2. 文本提取辅助函数
def extract_text_from_pdf(file):
    """从 PDF 文件中提取纯文本"""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        return f"PDF解析失败: {str(e)}"

def extract_text_from_docx(file):
    """从 Word 文件中提取纯文本"""
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Word解析失败: {str(e)}"

# 3. 真实对接 DeepSeek 模型的函数
def analyze_resume_with_deepseek(api_key, jd_text, resume_text):
    # 💡 实例化 OpenAI 客户端（DeepSeek 的 API 接口全面兼容 OpenAI SDK 格式）
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"  # 这是 DeepSeek 官方的 API 直连网址
    )
    
    # 构造发送给 DeepSeek 的核心高级 HR 提示词
    system_prompt = "你是一位精通“AI智能眼睛/计算机视觉/智能硬件”业务的资深HR专家。你的任务是严格、客观、一针见血地帮我评估候选人简历与岗位JD的匹配度。"
    
    user_content = f"""
    请帮我分析以下【岗位JD】和【候选人简历】，并输出匹配度评分、优缺点、推进建议及电话初筛提纲。
    
    【岗位JD】：
    {jd_text}
    
    【候选人简历】：
    {resume_text}
    
    请严格按照以下格式用 Markdown 漂亮地输出：
    ### 📊 综合匹配度：[请给出得分，如 XX分]
    
    ### 🟢 核心优势（优点）
    1. ...
    2. ...
    
    ### 🔴 潜在风险（缺点/漏项）
    1. ...
    2. ...
    
    ### 🎯 推进建议
    [请明确给出：强烈推荐 / 建议电话初筛 / 暂不考虑]
    
    ### 📞 电话初筛提问提纲
    [如果建议推进，请针对简历中的模糊点或我们业务关注的“AI智能眼镜（软硬件协同/CV算法）”特征，生成3-4个定制化电话提问。]
    """
    
    try:
        # 调用 DeepSeek 目前最标准且高性价比的对话模型 deepseek-chat
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3, # 降低随机性，让HR评估更客观、稳定
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用 DeepSeek API 出错，错误原因: {str(e)}"

# 4. 前端界面布局设计：左侧放配置和JD，右侧放简历和结果
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("⚙️ 1. 密钥与岗位 JD")
    
    # 在页面上直接安全地输入 API Key，采用密码隐藏模式，不留痕迹
    api_key_input = st.text_input(
        "请输入您的 DeepSeek API Key:", 
        type="password",
        placeholder="sk-..."
    )
    
    st.write("---")
    
    jd_input = st.text_area(
        "请粘贴当前招聘岗位的具体要求（JD）：",
        height=350,
        placeholder="例如：负责智能眼镜的计算机视觉算法研发，要求熟悉SLAM、OpenCV，有硬件调试经验者优先..."
    )

with col_right:
    st.header("📄 2. 上传候选人简历")
    uploaded_file = st.file_uploader("支持 PDF (.pdf)、Word (.docx) 或 文本 (.txt) 文件", type=["pdf", "docx", "txt"])
    
    resume_text = ""
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        if file_type == 'pdf':
            resume_text = extract_text_from_pdf(uploaded_file)
        elif file_type == 'docx':
            resume_text = extract_text_from_docx(uploaded_file)
        elif file_type == 'txt':
            resume_text = uploaded_file.read().decode("utf-8")
        
        if resume_text.strip():
            st.success(f"成功读取简历：{uploaded_file.name} (共 {len(resume_text)} 字)")
            with st.expander("查看简历原文预览"):
                st.text(resume_text)
        else:
            st.error("未能从文件中提取出有效文本，请确认文件是否加密或为纯图片。")
            
    st.write("---")
    
    # 5. 触发分析按钮
    if st.button("🚀 开始 AI 智能匹配分析", type="primary"):
        if not api_key_input:
            st.error("请输入您的 DeepSeek API Key！")
        elif not jd_input:
            st.error("请先在左侧输入岗位 JD！")
        elif not resume_text:
            st.error("请先上传候选人简历！")
        else:
            with st.spinner("DeepSeek 正在深度解析简历并匹配中，请稍候..."):
                # 真正开始调用 DeepSeek 接口
                report = analyze_resume_with_deepseek(api_key_input, jd_input, resume_text)
                
                st.header("📋 DeepSeek 实时评估报告")
                st.markdown(report)