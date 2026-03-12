import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import os
import requests
from datetime import datetime, timedelta, timezone
import streamlit.components.v1 as components
import urllib.parse 
import random 
import google.generativeai as genai
from PIL import Image

# ==========================================
# 🔑 极度机密：API Key 轮询池与安全隔离机制
# ==========================================
API_KEYS = []
try:
    if "GEMINI_API_KEYS" in st.secrets:
        API_KEYS = [k.strip() for k in st.secrets["GEMINI_API_KEYS"].split(",") if k.strip()]
    elif "GEMINI_API_KEY" in st.secrets:
        API_KEYS = [st.secrets["GEMINI_API_KEY"].strip()]
except Exception:
    pass

# --- 双擎数据库配置 (本地+云端) ---
DATA_FILE = "bowu_records.json"
CLOUD_CFG_FILE = "cloud_config.json"

def get_cloud_cfg():
    cfg = {}
    # 🚀 史诗级修复：优先读取 Streamlit Secrets 里的高级金库密钥，彻底防止云端休眠导致代理商掉线和存不上档！
    if "JSONBIN_API_KEY" in st.secrets and "JSONBIN_BIN_ID" in st.secrets:
        cfg["api_key"] = st.secrets["JSONBIN_API_KEY"].strip()
        cfg["bin_id"] = st.secrets["JSONBIN_BIN_ID"].strip()
        return cfg
        
    if os.path.exists(CLOUD_CFG_FILE):
        try:
            with open(CLOUD_CFG_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {}

def load_records():
    cfg = get_cloud_cfg()
    if cfg.get("api_key") and cfg.get("bin_id"):
        try:
            headers = {"X-Master-Key": cfg["api_key"]}
            res = requests.get(f"https://api.jsonbin.io/v3/b/{cfg['bin_id']}/latest", headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json().get("record", {})
                if "合盘版" not in data: data["合盘版"] = {}
                if "财富版" not in data: data["财富版"] = {}
                if "授权池" not in data: data["授权池"] = {} 
                total_records = sum(len(v) for v in data.values() if isinstance(v, dict))
                st.session_state.cloud_debug_msg = f"✅ 连接成功！当前云端金库共有 {total_records} 条档案数据。"
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data
            else:
                st.session_state.cloud_debug_msg = f"❌ 连接被拒 (错误码:{res.status_code})。请检查 API Key 和 Bin ID 是否填错或多复制了空格！"
        except Exception as e:
            st.session_state.cloud_debug_msg = f"⚠️ 网络连接异常，正在读取本地缓存。"
    else:
        st.session_state.cloud_debug_msg = "⚪ 尚未连接云端，当前为本地断网模式。"
        
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "合盘版" not in data: data["合盘版"] = {}
                if "财富版" not in data: data["财富版"] = {} 
                if "授权池" not in data: data["授权池"] = {} 
                return data
        except Exception: return {"运势版": {}, "人格版": {}, "合盘版": {}, "财富版": {}, "授权池": {}}
    return {"运势版": {}, "人格版": {}, "合盘版": {}, "财富版": {}, "授权池": {}}

def sync_to_cloud(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    cfg = get_cloud_cfg()
    if cfg.get("api_key") and cfg.get("bin_id"):
        try:
            headers = {"X-Master-Key": cfg["api_key"], "Content-Type": "application/json"}
            requests.put(f"https://api.jsonbin.io/v3/b/{cfg['bin_id']}", json=data, headers=headers, timeout=5)
        except Exception: pass

def save_record(category, name, data):
    records = load_records()
    tz_beijing = timezone(timedelta(hours=8))
    timestamp = datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")
    record_key = f"{name} ({timestamp})"
    
    # 🚀 核心防越权：悄悄打上代理商的思想钢印 (创建者ID)
    data["_creator"] = st.session_state.get("current_user", "unknown")
    
    if category not in records: records[category] = {}
    records[category][record_key] = data
    
    sync_to_cloud(records) 
    return record_key

def delete_record(category, record_key):
    records = load_records()
    if category in records and record_key in records[category]:
        del records[category][record_key]
        sync_to_cloud(records) 
        return True
    return False

def parse_clean_json(raw_str):
    start_idx = raw_str.find('{')
    end_idx = raw_str.rfind('}')
    if start_idx != -1 and end_idx != -1:
        clean_str = raw_str[start_idx:end_idx+1]
        return json.loads(clean_str)
    return json.loads(raw_str)

def get_json_template(engine_name):
    if engine_name == "📊 全息能量档案":
        return """{
  "总览": {
    "性格底色": "生成专属文案：一针见血的命理性格定调",
    "周期总结": "生成专属文案：近期的核心破局策略"
  },
  "折线图": [
    {"日期": "填入日期如 5月1日", "财富": 80, "感情": 60, "事业": 70, "健康": 90}
  ],
  "每日详情": [
    {
      "日期": "填入对应日期如 5月1日",
      "战袍": "颜色或穿搭建议",
      "吉位": "方位如 正北",
      "预警": "今日可能发生的倒霉事预警",
      "禁忌": "绝对不能做的事"
    }
  ]
}"""
    elif engine_name == "👁️ 内核透视矩阵":
        return """{
  "雷达图": {
    "情绪稳定性": 80, "控制欲": 90, "共情与包容": 30, 
    "物质现实度": 85, "精神共鸣需求": 40, "面具伪装度": 95
  },
  "深度解析": {
    "暗影特质与预警": "一针见血指出其人性暗面或极端特质",
    "内核画像与高光": "其潜意识的真实诉求与性格高光",
    "社交面具反差": "对外装什么样，对内实际上什么样",
    "相处与破局指南": "针对这种人，求测者该如何相处或防御"
  }
}"""
    elif engine_name == "💞 双人宿命羁绊 (合盘版)":
        return """{
  "合盘总评": {
    "契合度分数": 85,
    "关系定性": "宿命正缘 / 讨债孽缘 / 露水情缘 / 灵魂伴侣 (选一并解释)",
    "权力格局": "指明谁占主导，谁在情感吸血",
    "宿命羁绊定调": "一句话概括这段关系的本质带点宿命感"
  },
  "核心风险预警": {
    "第三方介入风险": "明确指出是否有出轨、聊骚、多角恋倾向及原因",
    "财务纠葛": "指出两人在一起是互旺还是破财？谁消耗谁？"
  },
  "双人雷达图": {
    "维度": ["情绪稳定性", "控制欲", "共情与包容", "物质与现实", "精神共鸣"],
    "A方": [80, 50, 90, 60, 85],
    "B方": [60, 80, 40, 90, 50]
  },
  "深度交叉解析": {
    "核心吸引力": "指出两人当初为何会互相吸引",
    "雷区引爆点": "相处中最致命的矛盾",
    "终极相处建议": "给求测者的高阶破局法与防坑建议"
  }
}"""
    elif engine_name == "💰 流年财富透视矩阵 (搞钱专属)":
        return """{
  "财富总览": {
    "财富格局定调": "一针见血指出其一生的财富级别与搞钱模式",
    "搞钱天命主场": "根据喜用神指出最旺的赛道。并给出身份建议"
  },
  "流年财运动态": {
    "爆发节点": "指出今年哪几个月是进财/升职的最高峰，建议猛烈出击",
    "破财黑洞预警": "指出今年哪几个月容易破财、被骗或背锅，必须空仓蛰伏"
  },
  "搞钱六维雷达图": {
    "维度": ["偏财爆发运", "正财长线运", "守财护城河", "贵人相助运", "商业直觉力", "落地执行力"],
    "分值": [90, 60, 40, 80, 85, 70]
  },
  "深度搞钱建议": {
    "合作与避坑指南": "防范什么样的职场小人或容易被哪类合伙人坑",
    "能量风水加持": "定制日常旺财/升职行为"
  }
}"""

def analyze_bazi_image(image_file, persona, background, engine_type, model_name):
    if not API_KEYS:
        return "❌ 致命错误：未检测到 API Key！请去 Streamlit 云端后台的 Advanced settings -> Secrets 中配置 `GEMINI_API_KEYS = \"你的密钥\"`！"
    
    try:
        current_key = random.choice(API_KEYS)
        genai.configure(api_key=current_key)
        
        img = Image.open(image_file)
        json_template = get_json_template(engine_type)
        today_str = datetime.now().strftime('%Y年%m月%d日')
        
        prompt = f"""你现在是《拨雾计划》的顶尖盲派命理宗师兼商业心理顾问。
我上传了一张或多张客户的八字排盘截图，请你仔细读取图片中的天干地支、五行旺衰、大运流年等信息。

【今日现实时间】：{today_str} (请以此为基准开始推演)
【客户现实身份】：{persona}
【补充背景】：{background}

【你的任务】：
请务必结合客户的【现实身份标签】和【排盘图片】，用极其犀利、充满现实指导意义（带点降维打击和压迫感）的风格进行断语。

🚨 【日期防伪警告（极其重要）】："折线图"和"每日详情"中的日期，**必须从今日（{today_str}）开始，连续往后推算 7 天**！绝对不允许照抄 JSON 模板里“5月1日”这种虚假示例日期！

🚨 【折线图数据防伪警告（极其重要）】：
折线图中的“财富、感情、事业、健康”四条曲线**绝对不能是平行的**！真实的人生必定存在能量守恒与博弈（例如：事业冲高时，健康或感情必然下滑；财富暴增时，容易遭遇烂桃花破财）。
你必须让这四条线产生**极其明显的交叉、反向波动和独立的峰谷**！绝不能呈现出同步涨跌的“平行线”敷衍状态，否则客户会一眼看穿这是机器生成的假数据！

🚨 【防同质化极度警告】：下方 JSON 模板中出现的所有数值仅仅是占位符！你**必须**根据该客户真实的生辰八字，重新推演并打出全新的分数（1-100的整数）！**绝对不允许照抄模板中的示例数值！** 请严格按照以下 JSON 格式输出报告，**只输出 JSON 代码，不要包含任何前缀后缀**：

```json
{json_template}
```"""
        
        sys_instruct = "你现在是《拨雾计划》的顶尖盲派命理宗师兼商业心理顾问。你的语言风格极其犀利、充满现实指导意义，且带有强烈的降维打击和压迫感。你绝不说正确的废话，直击人性暗面与现实痛点。"
        gen_config = genai.types.GenerationConfig(temperature=0.8, top_p=0.9)

        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=sys_instruct, generation_config=gen_config)
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e1:
            error_msg = str(e1)
            # 🚀 终极防弹机制：如果 Pro 额度耗尽(429)或被锁死，底层无缝静默降级到 Flash 引擎，绝不让客户/代理商看到英文报错！
            if "429" in error_msg and "pro" in model_name.lower():
                try:
                    fallback_model = model_name.replace("pro", "flash")
                    model2 = genai.GenerativeModel(model_name=fallback_model, system_instruction=sys_instruct, generation_config=gen_config)
                    res2 = model2.generate_content([prompt, img])
                    return res2.text
                except Exception as e2:
                    return f"❌ 引擎级联崩溃。主引擎及备用引擎均无响应: {str(e2)}"
            
            return f"❌ 请求失败，错误信息: {error_msg}"
                
    except Exception as e:
        return f"❌ 引擎运行时发生系统级错误。详细信息: {str(e)}"

# 1. 全局页面配置
st.set_page_config(page_title="拨雾计划 - 商业矩阵终端", layout="wide", page_icon="🔮", initial_sidebar_state="expanded")

all_records = load_records()

st.markdown("""
    <style>
    #MainMenu { display: none !important; }
    .stDeployButton { display: none !important; }
    footer { display: none !important; }
    .viewerBadge_container, .viewerBadge_link, .viewerBadge_text { display: none !important; }
    [data-testid="stViewerBadge"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

query_params = st.query_params
client_cat = query_params.get("cat")
client_id = query_params.get("id")
is_client_mode = bool(client_cat and client_id)

if is_client_mode:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        header { display: none !important; } 
        .block-container { 
            padding-top: 2rem; padding-bottom: 2rem; max-width: 900px !important; margin: 0 auto;
            background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' version='1.1' height='200px' width='200px'><text x='-30' y='100' fill='rgba(255,255,255,0.02)' font-size='24' transform='rotate(-45)'>拨雾计划 BOWU.PRO</text></svg>");
        }
        @keyframes fadeSlideUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
        div[data-testid="stVerticalBlock"] > div.element-container { animation: fadeSlideUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(1) { animation-delay: 0.05s; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(2) { animation-delay: 0.1s; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(3) { animation-delay: 0.15s; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(4) { animation-delay: 0.2s; }
        div.row-widget.stRadio > div { flex-direction: row; align-items: center; }
        </style>
    """, unsafe_allow_html=True)
    
    page_map = {"运势版": "📊 全息能量档案", "人格版": "👁️ 内核透视矩阵", "合盘版": "💞 双人宿命羁绊 (合盘版)", "财富版": "💰 流年财富透视矩阵 (搞钱专属)"}
    page_selection = page_map.get(client_cat, "📊 全息能量档案")
    show_teleprompter = False 
    st.markdown("<h4 style='text-align:center; color:#888; letter-spacing: 5px; font-weight: 300; margin-bottom: 30px;'>— 拨雾计划 专属数字档案 —</h4>", unsafe_allow_html=True)

else:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        st.markdown("""
            <style>
            .block-container { max-width: 500px; padding-top: 100px; }
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            header { display: none !important; }
            </style>
        """, unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; margin-bottom: 30px; color: #00E5FF; letter-spacing: 2px;'>🔒 拨雾计划引擎终端</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color: #888; margin-bottom: 30px;'>系统授权验证 / Access Verification</p>", unsafe_allow_html=True)
        
        db_records = load_records()
        if "授权池" not in db_records: db_records["授权池"] = {}
        
        with st.form(key="login_form"):
            pwd = st.text_input("请输入系统授权密钥：", type="password", placeholder="Press Enter to login...")
            submit_btn = st.form_submit_button("🔑 验证登入", use_container_width=True, type="primary")
            
            if submit_btn:
                if pwd == "bowu888":  
                    st.session_state.authenticated = True
                    st.session_state.role = "master" 
                    st.session_state.current_user = "master"
                    st.rerun()
                elif pwd in db_records["授权池"]:
                    auth_info = db_records["授权池"][pwd]
                    
                    if auth_info.get("type") == "date":
                        tz_beijing = timezone(timedelta(hours=8))
                        today = datetime.now(tz_beijing).date()
                        expire_date = datetime.strptime(auth_info["expire_date"], "%Y-%m-%d").date()
                        if today <= expire_date:
                            st.session_state.authenticated = True
                            st.session_state.role = "guest"
                            st.session_state.current_user = pwd
                            st.rerun()
                        else:
                            st.error(f"❌ 账号已于 {auth_info['expire_date']} 过期！请联系主理人续费。")
                            
                    elif auth_info.get("type") == "count":
                        if auth_info["remaining_uses"] > 0:
                            db_records["授权池"][pwd]["remaining_uses"] -= 1
                            sync_to_cloud(db_records)
                            st.session_state.authenticated = True
                            st.session_state.role = "guest"
                            st.session_state.current_user = pwd
                            st.rerun()
                        else:
                            st.error("❌ 该授权码的使用次数（次卡）已耗尽！请联系主理人续费。")
                else:
                    st.error("❌ 密钥错误或不存在，拒绝访问！触发防盗刷警报。")
                
        st.stop() 

    st.markdown("""
        <style>
        .block-container { 
            padding-top: 2rem; padding-bottom: 2rem;
            background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' version='1.1' height='200px' width='200px'><text x='-30' y='100' fill='rgba(255,255,255,0.02)' font-size='24' transform='rotate(-45)'>拨雾计划 BOWU.PRO</text></svg>");
        }
        @keyframes fadeSlideUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
        div[data-testid="stVerticalBlock"] > div.element-container { animation: fadeSlideUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(1) { animation-delay: 0.05s; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(2) { animation-delay: 0.1s; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(3) { animation-delay: 0.15s; }
        div[data-testid="stVerticalBlock"] > div.element-container:nth-child(4) { animation-delay: 0.2s; }
        .empty-state { text-align: center; padding: 100px 20px; border-radius: 10px; background-color: rgba(255, 255, 255, 0.02); border: 1px dashed rgba(255, 255, 255, 0.1); margin-top: 50px; }
        .save-module { background-color: rgba(0, 229, 255, 0.05); padding: 20px; border-radius: 10px; border-left: 4px solid #00E5FF; margin-top: 40px; }
        .teleprompter { background-color: rgba(255, 215, 0, 0.1); border: 1px solid #FFD700; border-radius: 10px; padding: 15px; margin-bottom: 20px; color: #FFD700; }
        div.row-widget.stRadio > div { flex-direction: row; align-items: center; }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("🧭 拨雾计划引擎矩阵")
    
    # 动态显示角色身份与全局强制同步按钮
    if st.session_state.get("role") == "master":
        st.sidebar.markdown("<div style='background-color:rgba(255,165,0,0.1); padding:8px; border-radius:5px; border-left:3px solid #FFA500; margin-bottom:15px;'><span style='color:#FFA500; font-size:12px; font-weight:bold;'>👑 状态：主理人上帝模式</span></div>", unsafe_allow_html=True)
        if st.sidebar.button("🔄 强制同步全网云端数据", use_container_width=True, type="primary"):
            st.rerun()
    else:
        st.sidebar.markdown("<div style='background-color:rgba(0,229,255,0.1); padding:8px; border-radius:5px; border-left:3px solid #00E5FF; margin-bottom:15px;'><span style='color:#00E5FF; font-size:12px; font-weight:bold;'>🔒 状态：代理商沙盒模式</span></div>", unsafe_allow_html=True)
    
    page_selection = st.sidebar.radio("请选择要生成的交付报告：", ["📊 全息能量档案", "👁️ 内核透视矩阵", "💞 双人宿命羁绊 (合盘版)", "💰 流年财富透视矩阵 (搞钱专属)"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 旗舰版 AI 视觉解析舱")
    
    persona_options = {
        "📊 全息能量档案": ["🎯 迷茫求变/寻找破局点", "💼 创业者/搞钱主力军", "🏢 职场打工人/大厂牛马", "🏡 感情至上/生活维稳期"],
        "👁️ 内核透视矩阵": ["💔 感情受挫/遭遇海王吸血", "🏢 职场被孤立/遇小人", "🤝 商业合伙/考察对方人品", "🪞 深度自我探索"],
        "💞 双人宿命羁绊 (合盘版)": ["💍 适婚年龄看正缘/结婚", "💔 怀疑对方出轨/海王海后", "💰 看双方是否旺财/利益纠葛", "🌪️ 虐恋纠缠/断联期"],
        "💰 流年财富透视矩阵 (搞钱专属)": ["🏢 大厂/体制内打工人 (求加薪/副业)", "💼 创业老板/投资客 (求避坑/爆发)", "🏡 待业/自由职业/宝妈 (求方向/翻身)", "💻 搞流量/做自媒体 (求风口/变现)"]
    }
    
    with st.sidebar.expander("🚀 一键上传断盘", expanded=True):
        st.caption("直接拖入【问真八字】截图，系统将自动读取并生成最终报告！")
        
        uploaded_img = st.file_uploader("📥 拖入或点击上传排盘截图", type=["png", "jpg", "jpeg"])
        
        # 🚀 核心升级：隐藏代理商的 Pro 选项，强制其使用 Flash 极速版！
        if st.session_state.get("role") == "master":
            model_choice = st.radio("🤖 选择 AI 引擎算力档位：", 
                ["⚡ 极速版 (Flash - 适合快速测试/无限次)", "🧠 深度旗舰版 (Pro - 极度聪明/出单专用)"],
                help="【Flash极速版】速度极快，随便测不限流；【Pro旗舰版】算力最强、文案最狠，但免费版限流(一分钟最多点2次)！建议接单时用 Pro！"
            )
            actual_model_name = "gemini-2.5-pro" if "Pro" in model_choice else "gemini-2.5-flash"
        else:
            model_choice = st.radio("🤖 选择 AI 引擎算力档位：", 
                ["⚡ 极速版 (Flash - 代理商专属/不限流)"],
                help="当前为代理商沙盒模式，默认调用稳定不限流的极速引擎。如需开启 Pro 极限算力，请联系主理人！"
            )
            actual_model_name = "gemini-2.5-flash"
            
        persona_tag = st.selectbox("1. 选择客户现实标签：", persona_options[page_selection])
        birth_info_tag = st.text_input("2. 简短备注(可选)：", placeholder="例如：最近刚离职...")

        if "auto_json_result" not in st.session_state:
            st.session_state.auto_json_result = ""

        # 按钮文案也跟着角色变身
        button_label = "🔥 启动 Pro 视觉解析引擎" if "Pro" in model_choice else "⚡ 启动 Flash 极速解析"
        
        if st.button(button_label, type="primary", use_container_width=True):
            if uploaded_img is None:
                st.error("⚠️ 请先上传一张排盘截图！")
            else:
                loading_msg = "🔮 拨雾引擎正在深度扫描排盘数据... (需15-30秒，请勿频繁点击)" if "Pro" in model_choice else "⚡ 拨雾引擎正在极速扫描排盘数据... (需5-10秒)"
                with st.spinner(loading_msg):
                    result_text = analyze_bazi_image(uploaded_img, persona_tag, birth_info_tag, page_selection, actual_model_name)
                    
                    if "❌" in result_text:
                        st.error(result_text)
                    else:
                        st.session_state.auto_json_result = result_text
                        st.success("✅ 解析完成！报告数据已自动填充，请在右侧查阅。")

    st.sidebar.markdown("---")
    
    # 只有主理人才能配置云端，防止代理商搞破坏
    if st.session_state.get("role") == "master":
        with st.sidebar.expander("👑 SaaS 租户授权管理中心", expanded=False):
            st.caption("无需改代码，在这里一键生成代理商的专属密码！")
            
            auth_tab1, auth_tab2 = st.tabs(["➕ 生成密码", "📋 密码列表"])
            
            with auth_tab1:
                new_pwd = st.text_input("自定义新密码：", placeholder="如: guest01", key="new_pwd_input")
                pwd_memo = st.text_input("备注(发给谁的)：", placeholder="如: 上海代理老王", key="pwd_memo_input")
                pwd_type = st.radio("授权类型：", ["📅 按日期到期", "🔢 按次消耗(次卡)"], horizontal=True)
                
                if "日期" in pwd_type:
                    expire_d = st.date_input("选择到期日期：")
                    if st.button("✅ 生成日期卡", use_container_width=True):
                        if new_pwd.strip():
                            all_records["授权池"][new_pwd.strip()] = {"type": "date", "expire_date": str(expire_d), "memo": pwd_memo}
                            sync_to_cloud(all_records)
                            st.success(f"密码 {new_pwd} 已生效！"); st.rerun()
                        else: st.error("请填写密码！")
                else:
                    use_count = st.number_input("设置可用登录次数：", min_value=1, value=10, step=1)
                    if st.button("✅ 生成次卡", use_container_width=True):
                        if new_pwd.strip():
                            all_records["授权池"][new_pwd.strip()] = {"type": "count", "remaining_uses": int(use_count), "memo": pwd_memo}
                            sync_to_cloud(all_records)
                            st.success(f"密码 {new_pwd} 已生效！"); st.rerun()
                        else: st.error("请填写密码！")
                        
            with auth_tab2:
                if st.button("🔄 刷新最新使用情况", use_container_width=True):
                    st.rerun()
                    
                if not all_records.get("授权池"):
                    st.info("当前没有分发任何密码。")
                else:
                    for p, info in all_records.get("授权池", {}).items():
                        status_txt = f"📅 期限: {info.get('expire_date')}" if info.get('type') == 'date' else f"🔢 剩余: {info.get('remaining_uses')} 次"
                        st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:5px; margin-bottom:10px; border-left:3px solid #00E5FF;'><b>密码:</b> <code style='color:#00E5FF;'>{p}</code><br><span style='font-size:12px; color:#888;'>备注: {info.get('memo', '无')} | {status_txt}</span></div>", unsafe_allow_html=True)
                        if st.button(f"🗑️ 删除 {p}", key=f"del_pwd_{p}"):
                            del all_records["授权池"][p]
                            sync_to_cloud(all_records)
                            st.rerun()
        st.sidebar.markdown("---")

    st.sidebar.markdown("### 🛠️ 商业转化工具")
    show_teleprompter = st.sidebar.checkbox("👁️ 开启主理人销讲提词器", value=False)
    st.sidebar.markdown("---")

# ================= 🚀 核心重构：上帝视角与沙盒隔离提取器 =================
def render_history_sidebar(cat_name, state_key):
    st.sidebar.markdown("### 📂 客户历史档案库")
    
    if st.session_state.get("role") == "master":
        # 抓取所有创建者
        creators = set()
        for k, v in all_records.get(cat_name, {}).items():
            if isinstance(v, dict): creators.add(v.get("_creator", "unknown"))
        
        # 组装下拉选项
        filter_opts = ["🌍 全网所有数据 (上帝视角)"]
        if "master" in creators: filter_opts.append("👑 我的专属数据")
        for c in sorted(creators):
            if c not in ["master", "unknown"]: filter_opts.append(f"🔒 代理商: {c}")
        if "unknown" in creators: filter_opts.append("❓ 早期未分类数据")
        
        view_filter = st.sidebar.selectbox("👁️ 数据筛选器", filter_opts, key=f"filter_{state_key}")
        
        # 根据筛选器过滤列表
        history_list = []
        for k, v in all_records.get(cat_name, {}).items():
            if isinstance(v, dict):
                c = v.get("_creator", "unknown")
                if view_filter.startswith("🌍"): history_list.append(k)
                elif view_filter.startswith("👑") and c == "master": history_list.append(k)
                elif view_filter.startswith("🔒") and c == view_filter.replace("🔒 代理商: ", ""): history_list.append(k)
                elif view_filter.startswith("❓") and c == "unknown": history_list.append(k)
    else:
        st.sidebar.caption("🔒 代理沙盒：仅显示你个人的客户数据")
        history_list = [k for k, v in all_records.get(cat_name, {}).items() if isinstance(v, dict) and v.get("_creator") == st.session_state.get("current_user")]
        
    history_list.reverse()
    selected_record = st.sidebar.selectbox("一键读取已存档案", ["-- 新建档案 / 自动生成新数据 --"] + history_list, key=f"sel_{state_key}")
    
    data_to_render_local = None
    if selected_record != "-- 新建档案 / 自动生成新数据 --":
        st.sidebar.success(f"👁️ 正在查看：\n\n**{selected_record}**")
        if st.sidebar.button("🗑️ 删除此档案", type="secondary", use_container_width=True, key=f"del_{state_key}"):
            delete_record(cat_name, selected_record)
            st.rerun()
        data_to_render_local = all_records.get(cat_name, {}).get(selected_record)
        
    return selected_record, data_to_render_local

# ================= 渲染核心逻辑分离 =================
data_to_render = None

if not is_client_mode and st.session_state.get("new_link"):
    st.success(f"🎉 **{st.session_state.get('new_name', '')}** 的档案已成功入库！\n\n👇 **请立刻复制下方链接发送给客户：**")
    st.code(st.session_state.new_link, language="text")
    if st.button("✅ 我已复制，关闭提示", key="close_global_tip"):
        st.session_state.new_link = None
        st.session_state.new_name = None
        st.rerun()
    st.markdown("---")

# 【运势版】
if page_selection == "📊 全息能量档案":
    if not is_client_mode:
        st.title("🔮 【拨雾计划】专属全息能量档案")
        selected_record, data_to_render = render_history_sidebar("运势版", "fortune")
        
        if selected_record == "-- 新建档案 / 自动生成新数据 --":
            raw_json_input = st.sidebar.text_area("⚙️ 底层数据(可手动修改)", value=st.session_state.auto_json_result, height=200)
            if st.sidebar.button("🔄 渲染右侧报告", type="primary", use_container_width=True): pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败，JSON不完整。")
            else:
                st.markdown("<div class='empty-state'><h2>⏳ 引擎待机中...</h2><p>请在左侧上传排盘截图，启动全自动解析。</p></div>", unsafe_allow_html=True)
    else:
        data_to_render = all_records.get("运势版", {}).get(client_id)
        if not data_to_render: st.error("⚠️ 链接已失效或档案不存在。")

    if data_to_render and "总览" in data_to_render:
        data = data_to_render
        if show_teleprompter and not is_client_mode:
            st.markdown("<div class='teleprompter'><h4>㊙️ 内部销讲话术 (运势篇)</h4><p><b>💰 促单锚点：</b>引导客户关注折线图最低谷的那天，强调这是能量黑洞日，可顺势推销深度护航或风水布局方案。</p></div>", unsafe_allow_html=True)
        
        if is_client_mode: st.markdown(f"<h2 style='text-align:center;'>🔮 {client_id.split('(')[0].strip()} 的全息能量档案</h2><br>", unsafe_allow_html=True)
        
        col_info1, col_info2 = st.columns(2)
        with col_info1: st.info(f"**🧬 能量底色**：\n\n{data['总览']['性格底色']}")
        with col_info2: st.success(f"**🎯 周期破局策略**：\n\n{data['总览']['周期总结']}")
            
        st.markdown("### 📈 个人四维波动矩阵")
        df = pd.DataFrame(data["折线图"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["日期"], y=df["财富"], mode='lines+markers', name='💰 财富运势', line=dict(color='#FFD700', width=3, shape='spline')))
        fig.add_trace(go.Scatter(x=df["日期"], y=df["感情"], mode='lines+markers', name='❤️ 感情/情绪', line=dict(color='#FF69B4', width=3, shape='spline')))
        fig.add_trace(go.Scatter(x=df["日期"], y=df["事业"], mode='lines+markers', name='🚀 事业势能', line=dict(color='#00E5FF', width=3, shape='spline')))
        fig.add_trace(go.Scatter(x=df["日期"], y=df["健康"], mode='lines+markers', name='🛡️ 健康机能', line=dict(color='#00FF7F', width=2, dash='dot', shape='spline')))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_type='category', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), hovermode="x unified", height=450, margin=dict(l=0, r=0, t=40, b=0), dragmode=False)
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### 📅 战袍与能量干预包")
        display_mode = st.radio("👉 界面显示模式切换：", ["🗺️ 七日全景模式", "📅 单日沉浸模式"], horizontal=True, key="display_toggle")
        
        days_data = data.get("每日详情", [])
        if days_data:
            if "七日全景模式" in display_mode:
                cols = st.columns(3)
                for idx, daily in enumerate(days_data):
                    with cols[idx % 3]:
                        st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.03); padding: 18px; border-radius: 12px; margin-bottom: 20px; border-top: 4px solid #00E5FF;">
                            <h4 style="margin-top:0; color: #00E5FF; font-size: 18px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 10px;">🗓️ {daily.get('日期', '')}</h4>
                            <div style="font-size: 14px; line-height: 1.6; color: #D0D0D0;">
                                <div style="margin-bottom: 10px;"><b style="color: #00E5FF;">👕 战袍：</b>{daily.get('战袍', '')}</div>
                                <div style="margin-bottom: 10px;"><b style="color: #00FF7F;">🧭 吉位：</b>{daily.get('吉位', '')}</div>
                                <div style="margin-bottom: 10px;"><b style="color: #FFD700;">⚠️ 预警：</b>{daily.get('预警', '')}</div>
                                <div style="margin-bottom: 0px;"><b style="color: #FF4B4B;">🛑 禁忌：</b>{daily.get('禁忌', '')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                date_list = [item["日期"] for item in days_data]
                selected_date_single = st.selectbox("📌 请下拉选择日期：", date_list)
                daily_data = next((item for item in days_data if item["日期"] == selected_date_single), None)
                if daily_data:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.info(f"**👕 当日战袍**：\n\n{daily_data.get('战袍', '')}"); st.success(f"**🧭 能量吉位**：\n\n{daily_data.get('吉位', '')}")
                    with col_b:
                        st.warning(f"**⚠️ 高危预警**：\n\n{daily_data.get('预警', '')}"); st.error(f"**🛑 行为禁忌**：\n\n{daily_data.get('禁忌', '')}")
        
        if not is_client_mode:
            if selected_record == "-- 新建档案 / 自动生成新数据 --":
                st.markdown('<div class="save-module">### 💾 将此报告存入云端并生成交付链接', unsafe_allow_html=True)
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1: save_name = st.text_input("客户标识（如：小红书-李女士）：", key="save_name_fortune")
                with col_save2:
                    st.write(""); st.write("")
                    if st.button("💾 入库并生成链接", type="primary", use_container_width=True):
                        if save_name.strip():
                            record_key = save_record("运势版", save_name.strip(), data)
                            st.session_state.auto_json_result = "" 
                            
                            encoded_cat = urllib.parse.quote("运势版")
                            encoded_id = urllib.parse.quote(record_key)
                            st.session_state.new_link = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                            st.session_state.new_name = save_name.strip()
                            st.rerun() 
                        else: st.error("⚠️ 请先输入客户标识！")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给客户！")
                encoded_cat = urllib.parse.quote("运势版")
                encoded_id = urllib.parse.quote(selected_record)
                share_url = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")

# 【人格版】
elif page_selection == "👁️ 内核透视矩阵":
    if not is_client_mode:
        st.title("👁️ 【拨雾计划】目标内核深度透析矩阵")
        selected_record_npd, data_to_render = render_history_sidebar("人格版", "npd")

        if selected_record_npd == "-- 新建档案 / 自动生成新数据 --":
            raw_json_input = st.sidebar.text_area("⚙️ 底层数据(可手动修改)", value=st.session_state.auto_json_result, height=200)
            if st.sidebar.button("🔄 渲染右侧报告", type="primary", use_container_width=True): pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败。")
            else: st.markdown("<div class='empty-state'><h2>👁️ 矩阵待机中...</h2><p>请在左侧上传排盘截图，启动全自动解析。</p></div>", unsafe_allow_html=True)
    else:
        data_to_render = all_records.get("人格版", {}).get(client_id)
        if not data_to_render: st.error("⚠️ 链接已失效。")

    if data_to_render and "雷达图" in data_to_render:
        data = data_to_render
        if show_teleprompter and not is_client_mode:
            st.markdown("<div class='teleprompter'><h4>㊙️ 内部销讲话术</h4><p><b>🗣️ 专家金句：</b>“所有让你痛苦的关系，都是因为能量场被他压制了。看雷达图最尖锐的那个角，就是他刺伤你最深的地方。”</p></div>", unsafe_allow_html=True)

        if is_client_mode: st.markdown(f"<h2 style='text-align:center;'>👁️ {client_id.split('(')[0].strip()} 的内核透视矩阵</h2><br>", unsafe_allow_html=True)

        st.markdown("### 🕸️ 潜意识六维雷达图 (暗黑三角检测)")
        categories = list(data["雷达图"].keys()); values = list(data["雷达图"].values())
        values.append(values[0]); categories.append(categories[0])
        fig = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(255, 75, 75, 0.4)', line=dict(color='#FF4B4B', width=2)))
        fig.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)', 
                radialaxis=dict(visible=True, range=[0, 100], color='rgba(255,255,255,0.5)', gridcolor='rgba(255,255,255,0.1)'), 
                angularaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=11))
            ), 
            showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
            height=400, dragmode=False, margin=dict(l=85, r=85, t=30, b=30)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### 📜 临床级命理交叉诊断书")
        st.error(f"**🚨 暗影特质与病理预警**：\n\n{data['深度解析'].get('暗影特质与预警', data['深度解析'].get('NPD病理预警', ''))}")
        col1, col2 = st.columns(2)
        with col1: st.info(f"**🪞 内核画像 (高光与底色)**：\n\n{data['深度解析'].get('内核画像与高光', data['深度解析'].get('内核画像', ''))}")
        with col2: st.warning(f"**🎭 亲密关系与社交反差**：\n\n{data['深度解析'].get('亲密关系反差', data['深度解析'].get('社交面具反差', ''))}")
        st.success(f"**🛡️ 相处与破局指南 (专属建议)**：\n\n{data['深度解析'].get('相处与破局指南', data['深度解析'].get('破局与防御指南', ''))}")
        
        if not is_client_mode:
            if selected_record_npd == "-- 新建档案 / 自动生成新数据 --":
                st.markdown('<div class="save-module">### 💾 将此报告存入云端并生成交付链接', unsafe_allow_html=True)
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1: save_name = st.text_input("客户标识：", key="save_name_npd")
                with col_save2:
                    st.write(""); st.write("")
                    if st.button("💾 入库并生成链接", type="primary", use_container_width=True):
                        if save_name.strip(): 
                            record_key = save_record("人格版", save_name.strip(), data)
                            st.session_state.auto_json_result = "" 
                            
                            encoded_cat = urllib.parse.quote("人格版")
                            encoded_id = urllib.parse.quote(record_key)
                            st.session_state.new_link = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                            st.session_state.new_name = save_name.strip()
                            st.rerun() 
                        else: st.error("⚠️ 请先输入客户标识！")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给客户！")
                encoded_cat = urllib.parse.quote("人格版")
                encoded_id = urllib.parse.quote(selected_record_npd)
                share_url = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")

# 【合盘版】
elif page_selection == "💞 双人宿命羁绊 (合盘版)":
    if not is_client_mode:
        st.title("💞 【拨雾计划】双人宿命羁绊透析矩阵")
        selected_record_syn, data_to_render = render_history_sidebar("合盘版", "syn")

        if selected_record_syn == "-- 新建档案 / 自动生成新数据 --":
            raw_json_input = st.sidebar.text_area("⚙️ 底层数据(可手动修改)", value=st.session_state.auto_json_result, height=200)
            if st.sidebar.button("🔄 渲染右侧报告", type="primary", use_container_width=True): pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败。")
            else: st.markdown("<div class='empty-state'><h2>💞 引擎待机中...</h2><p>请在左侧上传双人排盘截图(拼成一张图)，启动全自动解析。</p></div>", unsafe_allow_html=True)
    else:
        data_to_render = all_records.get("合盘版", {}).get(client_id)
        if not data_to_render: st.error("⚠️ 链接已失效。")

    if data_to_render and "双人雷达图" in data_to_render:
        data = data_to_render
        if show_teleprompter and not is_client_mode:
            st.markdown("<div class='teleprompter'><h4>㊙️ 内部销讲话术</h4><p><b>💰 促单锚点：</b>引导客户看下方的防出轨和财富纠葛版块，推销常年情感顾问或改运咨询。</p></div>", unsafe_allow_html=True)

        if is_client_mode: st.markdown(f"<h2 style='text-align:center;'>💞 {client_id.split('(')[0].strip()} 的双人宿命羁绊</h2><br>", unsafe_allow_html=True)

        col_score, col_desc = st.columns([1, 2])
        with col_score:
            score = data['合盘总评'].get('契合度分数', 50)
            fig_gauge = go.Figure(go.Indicator(mode = "gauge+number", value = score, title = {'text': "❤️ 宿命契合度", 'font': {'color': 'white'}}, gauge = {'axis': {'range': [None, 100], 'tickcolor': "white"}, 'bar': {'color': "#FF69B4"}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "gray", 'steps': [{'range': [0, 40], 'color': "rgba(255, 75, 75, 0.3)"}, {'range': [40, 80], 'color': "rgba(255, 215, 0, 0.3)"}, {'range': [80, 100], 'color': "rgba(0, 229, 255, 0.3)"}]}))
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=300, margin=dict(l=20, r=20, t=50, b=20), dragmode=False)
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        with col_desc:
            st.write(""); st.write("")
            st.info(f"**📖 宿命羁绊定调**：\n\n{data['合盘总评'].get('宿命羁绊定调', '')}")
            col_tag1, col_tag2 = st.columns(2)
            with col_tag1: st.markdown(f"<div style='background-color:rgba(255,105,180,0.1); padding:10px; border-radius:8px; border-left:3px solid #FF69B4;'><b>🔮 关系定性：</b>{data['合盘总评'].get('关系定性', '')}</div>", unsafe_allow_html=True)
            with col_tag2: st.markdown(f"<div style='background-color:rgba(0,229,255,0.1); padding:10px; border-radius:8px; border-left:3px solid #00E5FF;'><b>⚖️ 权力格局：</b>{data['合盘总评'].get('权力格局', '')}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🚨 核心风险与隐刺排查 (高敏指标)")
        warn_col1, warn_col2 = st.columns(2)
        with warn_col1: st.error(f"**💔 第三方介入 (防出轨) 侦测**：\n\n{data.get('核心风险预警', {}).get('第三方介入风险', '')}")
        with warn_col2: st.warning(f"**💰 财富纠葛 (旺夫/破财) 评估**：\n\n{data.get('核心风险预警', {}).get('财务纠葛', '')}")

        st.markdown("---")
        st.markdown("### ⚔️ 能量博弈重叠矩阵 (双人雷达)")
        cat_closed = data["双人雷达图"]["维度"] + [data["双人雷达图"]["维度"][0]]
        val_A = data["双人雷达图"]["A方"] + [data["双人雷达图"]["A方"][0]]
        val_B = data["双人雷达图"]["B方"] + [data["双人雷达图"]["B方"][0]]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=val_A, theta=cat_closed, fill='toself', name='A方(如女方)', fillcolor='rgba(0, 229, 255, 0.4)', line=dict(color='#00E5FF', width=2)))
        fig_radar.add_trace(go.Scatterpolar(r=val_B, theta=cat_closed, fill='toself', name='B方(如男方)', fillcolor='rgba(255, 105, 180, 0.4)', line=dict(color='#FF69B4', width=2)))
        fig_radar.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)', 
                radialaxis=dict(visible=True, range=[0, 100], color='rgba(255,255,255,0.5)', gridcolor='rgba(255,255,255,0.1)'), 
                angularaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=11))
            ), 
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5), 
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
            height=420, dragmode=False, margin=dict(l=85, r=85, t=30, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### 📜 交叉博弈深度解析")
        col1, col2 = st.columns(2)
        with col1: st.success(f"**🧲 核心吸引力**：\n\n{data['深度交叉解析'].get('核心吸引力', '')}")
        with col2: st.error(f"**💣 雷区引爆点**：\n\n{data['深度交叉解析'].get('雷区引爆点', '')}")
        st.warning(f"**🛡️ 终极相处建议**：\n\n{data['深度交叉解析'].get('终极相处建议', '')}")
        
        if not is_client_mode:
            if selected_record_syn == "-- 新建档案 / 自动生成新数据 --":
                st.markdown('<div class="save-module">### 💾 将此报告存入云端并生成交付链接', unsafe_allow_html=True)
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1: save_name = st.text_input("合盘标识：", key="save_name_syn")
                with col_save2:
                    st.write(""); st.write("")
                    if st.button("💾 入库并生成链接", type="primary", use_container_width=True):
                        if save_name.strip(): 
                            record_key = save_record("合盘版", save_name.strip(), data)
                            st.session_state.auto_json_result = ""
                            
                            encoded_cat = urllib.parse.quote("合盘版")
                            encoded_id = urllib.parse.quote(record_key)
                            st.session_state.new_link = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                            st.session_state.new_name = save_name.strip()
                            st.rerun() 
                        else: st.error("⚠️ 请先输入合盘标识！")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给客户！")
                encoded_cat = urllib.parse.quote("合盘版")
                encoded_id = urllib.parse.quote(selected_record_syn)
                share_url = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")

# 【财富版】
elif page_selection == "💰 流年财富透视矩阵 (搞钱专属)":
    if not is_client_mode:
        st.title("💰 【拨雾计划】流年财富透视矩阵")
        selected_record_wealth, data_to_render = render_history_sidebar("财富版", "wealth")

        if selected_record_wealth == "-- 新建档案 / 自动生成新数据 --":
            raw_json_input = st.sidebar.text_area("⚙️ 底层数据(可手动修改)", value=st.session_state.auto_json_result, height=200)
            if st.sidebar.button("🔄 渲染右侧报告", type="primary", use_container_width=True): pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败，请检查 JSON 格式。")
            else: st.markdown("<div class='empty-state'><h2>💰 搞钱引擎待机中...</h2><p>请在左侧上传排盘截图，启动全自动解析。</p></div>", unsafe_allow_html=True)
    else:
        data_to_render = all_records.get("财富版", {}).get(client_id)
        if not data_to_render: st.error("⚠️ 链接已失效。")

    if data_to_render and "搞钱六维雷达图" in data_to_render:
        data = data_to_render
        if show_teleprompter and not is_client_mode:
            st.markdown("<div class='teleprompter'><h4>㊙️ 内部销讲话术</h4><p><b>💰 促单锚点：</b>重点放大客户‘破财黑洞’的恐惧感，或者‘爆发节点’的贪婪感。顺势抛出高客单价的风水局或全年私教服务。</p></div>", unsafe_allow_html=True)

        if is_client_mode: st.markdown(f"<h2 style='text-align:center; color: #FFD700;'>💰 {client_id.split('(')[0].strip()} 的财富透视矩阵</h2><br>", unsafe_allow_html=True)

        st.markdown("### 🕸️ 搞钱六维雷达图 (财富基因检测)")
        categories = list(data["搞钱六维雷达图"]["维度"])
        values = list(data["搞钱六维雷达图"]["分值"])
        values.append(values[0]); categories.append(categories[0])
        fig = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', fillcolor='rgba(255, 215, 0, 0.4)', line=dict(color='#FFD700', width=2)))
        fig.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)', 
                radialaxis=dict(visible=True, range=[0, 100], color='rgba(255,255,255,0.5)', gridcolor='rgba(255,255,255,0.1)'), 
                angularaxis=dict(color='white', gridcolor='rgba(255,255,255,0.1)', tickfont=dict(size=11))
            ), 
            showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
            height=400, dragmode=False, margin=dict(l=85, r=85, t=30, b=30)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        st.markdown("### 👑 财富阶层与天命主场")
        st.info(f"**💰 财富格局定调**：\n\n{data['财富总览'].get('财富格局定调', '')}")
        st.success(f"**🎯 搞钱天命主场**：\n\n{data['财富总览'].get('搞钱天命主场', '')}")

        st.markdown("---")
        st.markdown("### 📈 流年财运精准狙击")
        col_dyn1, col_dyn2 = st.columns(2)
        with col_dyn1: st.success(f"**🚀 爆发节点 (猛烈出击)**：\n\n{data['流年财运动态'].get('爆发节点', '')}")
        with col_dyn2: st.error(f"**💣 破财黑洞 (空仓蛰伏)**：\n\n{data['流年财运动态'].get('破财黑洞预警', '')}")

        st.markdown("---")
        st.markdown("### 🛡️ 护城河与风水干预")
        st.warning(f"**🤝 合作与避坑指南**：\n\n{data['深度搞钱建议'].get('合作与避坑指南', '')}")
        st.info(f"**🔮 能量风水加持**：\n\n{data['深度搞钱建议'].get('能量风水加持', '')}")
        
        if not is_client_mode:
            if selected_record_wealth == "-- 新建档案 / 自动生成新数据 --":
                st.markdown('<div class="save-module">### 💾 将此报告存入云端并生成交付链接', unsafe_allow_html=True)
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1: save_name = st.text_input("客户标识（如：创投群-王总）：", key="save_name_wealth")
                with col_save2:
                    st.write(""); st.write("")
                    if st.button("💾 入库并生成链接", type="primary", use_container_width=True):
                        if save_name.strip(): 
                            record_key = save_record("财富版", save_name.strip(), data)
                            st.session_state.auto_json_result = ""
                            
                            encoded_cat = urllib.parse.quote("财富版")
                            encoded_id = urllib.parse.quote(record_key)
                            st.session_state.new_link = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                            st.session_state.new_name = save_name.strip()
                            st.rerun() 
                        else: st.error("⚠️ 请先输入客户标识！")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给老板！")
                encoded_cat = urllib.parse.quote("财富版")
                encoded_id = urllib.parse.quote(selected_record_wealth)
                share_url = f"https://bowuapp-test.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")

# ================= 底部留资与转化模块 (仅C端可见) =================
if is_client_mode and data_to_render:
    st.markdown("<br>", unsafe_allow_html=True)
    
    wechat_ids = ["Xiaoyizhenren367", "A-Wxrrbb"] 
    wechat_id = random.choice(wechat_ids) 
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent; font-family: "sans serif", -apple-system, BlinkMacSystemFont, sans-serif; }}
            .cta-container {{ text-align: center; padding: 40px 20px; background: linear-gradient(145deg, rgba(0,229,255,0.05) 0%, rgba(255,105,180,0.05) 100%); border-radius: 15px; border: 1px solid rgba(255,255,255,0.05); }}
            .btn {{ cursor: pointer; display: inline-block; background-color: rgba(0, 229, 255, 0.1); border: 1px solid #00E5FF; color: #00E5FF; padding: 12px 30px; border-radius: 30px; font-weight: bold; letter-spacing: 1px; font-size: 15px; transition: all 0.3s ease; outline: none; box-shadow: 0 4px 15px rgba(0, 229, 255, 0.15); }}
            .btn:active {{ transform: scale(0.95); box-shadow: 0 2px 5px rgba(0, 229, 255, 0.15); }}
        </style>
    </head>
    <body>
        <div class="cta-container">
            <h3 style="color: #FAFAFA; margin-top: 0; margin-bottom: 10px; font-weight: 400; letter-spacing: 2px;">需要针对性的深度破局？</h3>
            <p style="color: #888; font-size: 14px; margin-bottom: 25px; line-height: 1.6;">您的数字档案仅展现了当前维度的部分信息。<br>如需更深度的命理推演或现实风水干预，请联系专属主理人。</p>
            
            <button class="btn" id="copyBtn" onclick="copyText()">
                ➕ 一键复制主理人微信
            </button>
            
            <p style="color:#444; font-size:12px; margin-top: 30px; margin-bottom: 0; letter-spacing: 1px;">© 拨雾计划 BOWU.PRO 版权所有</p>
        </div>

        <script>
            function copyText() {{
                var textArea = document.createElement("textarea");
                textArea.value = "{wechat_id}";
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                var btn = document.getElementById('copyBtn');
                btn.innerHTML = "✅ 微信号已复制！快去微信添加";
                btn.style.backgroundColor = "rgba(0, 255, 127, 0.15)";
                btn.style.borderColor = "#00FF7F";
                btn.style.color = "#00FF7F";
                btn.style.boxShadow = "0 4px 15px rgba(0, 255, 127, 0.2)";
                
                setTimeout(function() {{
                    btn.innerHTML = "➕ 一键复制主理人微信";
                    btn.style.backgroundColor = "rgba(0, 229, 255, 0.1)";
                    btn.style.borderColor = "#00E5FF";
                    btn.style.color = "#00E5FF";
                    btn.style.boxShadow = "0 4px 15px rgba(0, 229, 255, 0.15)";
                }}, 3000);
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=350)
