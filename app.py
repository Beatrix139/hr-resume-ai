import streamlit as st
import docx
from pypdf import PdfReader
from openai import OpenAI

# 1. 页面基本配置
st.set_page_config(page_title="AI智能眼业务-HR招聘助手", layout="wide")
st.title("👁️ AI智能眼睛业务 - 简历精准匹配系统 (极速缓存版)")
st.caption("已支持 PDF/Word/TXT，采用多轮对话前缀匹配技术，自动触发 DeepSeek 缓存降本提速")

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

# 3. 核心函数：采用多轮对话结构，100% 触发缓存命中
def analyze_resume_with_deepseek(jd_text, resume_text):
    # 🔒 从 Streamlit 云端的高级设置 (Secrets) 中读取 API Key，安全且免手动输入
    client = OpenAI(
        api_key=st.secrets["DEEPSEEK_API_KEY"], 
        base_url="https://api.deepseek.com/v1"
    )
    
   # 【第一轮：系统角色】加入了防止乱码误判的终极警告
    system_prompt = (
        "你是一位精通“AI智能眼睛/计算机视觉/智能硬件”业务的资深HR专家。"
        "你的任务是严格、客观、一针见血地帮我评估候选人简历与岗位JD的匹配度。"
        "⚠️特别声明：本系统在从PDF提取文本时，可能会因为字体编码问题导致简历中出现部分无意义的乱码、错别字或特殊符号。"
        "这完全是【系统提取文本的技术缺陷】导致的，绝非候选人粗心或简历质量问题！"
        "请你在评估时，【必须完全忽略所有乱码和奇怪的排版符号】，仅根据你能够读懂的正常文本、上下文逻辑来客观评估候选人的经历与能力，绝对不允许在报告中指责候选人简历乱码或不细心！"
    )
    
    # 【第二轮：用户固定输入】把【岗位JD】单独提出来。
    # 当你连续筛选同一个岗位时，由于 system 和这段 jd_content 一个字没变，DeepSeek 会100%强行命中缓存！
    jd_content = (
        f"【当前招聘岗位JD具体要求如下】:\n{jd_text}\n\n"
        f"请记住这个岗位要求。接下来我会为你发送候选人简历，请基于这个JD进行对比分析。"
    )
    
    # 【第三轮：用户变动输入】
    # 💡 优化：用 str() 强行把简历转为纯字符串，并用 .strip() 裁掉可能含有的动态空格或隐形换行
    clean_resume_text = str(resume_text).strip()
    
    resume_content = f"【候选人简历纯文本内容如下】:\n{clean_resume_text}\n\n请严格针对刚才的岗位JD进行深度匹配分析并输出报告。"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": jd_content},      # 
                {"role": "user", "content": resume_content}   # 
            ],
            temperature=0.3, 
        )
        return response.choices[0].message.content
    
    请严格针对刚才的岗位JD进行深度匹配，并严格按照以下格式用 Markdown 漂亮地输出：
    ### 📊 综合匹配度：[请给出得分，如 XX分]
    
    ### 🟢 核心优势（优点）
    1. ...
    
    ### 🔴 潜在风险（缺点/漏项）
    1. ...
    
    ### 🎯 推进建议
    [明确给出：强烈推荐 / 建议电话初筛 / 暂不考虑]
    
    ### 📞 电话初筛提问提纲
    [如果建议推进，请针对简历中的模糊点或我们业务关注的“AI智能眼镜（软硬件协同/CV算法）”特征，生成3-4个定制化电话提问。]
    """
    
    try:
        # 💡 这里就是能够锁死缓存的 3 条消息多轮对话结构
        # 消息 1 (system) -> 消息 2 (user: 固定JD) -> 这前两步在第二份简历时直接进缓存
        # 真正算新钱的只有最后一轮消息 3 (user: 变动简历)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": jd_content},      # 👈 这一步和上一步会被永久缓存！
                {"role": "user", "content": resume_content}   # 👈 只有这一步算新 Token 的钱
            ],
            temperature=0.3, # 降低随机性，让HR评估更客观、稳定
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用 DeepSeek API 出错，错误原因: {str(e)}"

# 4. 前端界面布局设计
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("📝 1. 填写岗位 JD")
    jd_input = st.text_area(
        "请粘贴当前招聘岗位的具体要求（JD）：",
        height=450,
        placeholder="例如：负责智能眼镜的计算机视觉算法研发，要求熟悉SLAM、OpenCV..."
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
        if not jd_input:
            st.error("请先在左侧输入岗位 JD！")
        elif not resume_text:
            st.error("请先上传候选人简历！")
        else:
            with st.spinner("DeepSeek 正在利用缓存加速深度解析中，请稍候..."):
                # 调用优化后的缓存版分析函数
                report = analyze_resume_with_deepseek(jd_input, resume_text)
                
                st.header("📋 DeepSeek 评估报告")
                st.markdown(report)
