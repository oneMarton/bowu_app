import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import os
import requests
from datetime import datetime
import streamlit.components.v1 as components
import urllib.parse # 新增：用于给链接套上防截断保护膜

# --- 双擎数据库配置 (本地+云端) ---
DATA_FILE = "bowu_records.json"
CLOUD_CFG_FILE = "cloud_config.json"

def get_cloud_cfg():
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
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data
        except Exception: pass
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "合盘版" not in data: data["合盘版"] = {}
                return data
        except Exception: return {"运势版": {}, "人格版": {}, "合盘版": {}}
    return {"运势版": {}, "人格版": {}, "合盘版": {}}

def save_record(category, name, data):
    records = load_records()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record_key = f"{name} ({timestamp})"
    
    if category not in records: records[category] = {}
    records[category][record_key] = data
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        
    cfg = get_cloud_cfg()
    if cfg.get("api_key") and cfg.get("bin_id"):
        try:
            headers = {"X-Master-Key": cfg["api_key"], "Content-Type": "application/json"}
            requests.put(f"https://api.jsonbin.io/v3/b/{cfg['bin_id']}", json=records, headers=headers, timeout=5)
        except Exception: pass
        
    return record_key

def delete_record(category, record_key):
    records = load_records()
    if category in records and record_key in records[category]:
        del records[category][record_key]
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        cfg = get_cloud_cfg()
        if cfg.get("api_key") and cfg.get("bin_id"):
            try:
                headers = {"X-Master-Key": cfg["api_key"], "Content-Type": "application/json"}
                requests.put(f"https://api.jsonbin.io/v3/b/{cfg['bin_id']}", json=records, headers=headers, timeout=5)
            except Exception: pass
        return True
    return False

def parse_clean_json(raw_str):
    start_idx = raw_str.find('{')
    end_idx = raw_str.rfind('}')
    if start_idx != -1 and end_idx != -1:
        clean_str = raw_str[start_idx:end_idx+1]
        return json.loads(clean_str)
    return json.loads(raw_str)

# 1. 全局页面配置 (修复：强制每次刷新都默认展开侧边栏)
st.set_page_config(page_title="拨雾计划 - 商业矩阵终端", layout="wide", page_icon="🔮", initial_sidebar_state="expanded")

# ====== 暴力抹除官方云的所有痕迹 (全白标化 V2 终极版) ======
st.markdown("""
    <style>
    /* 隐藏右上角默认菜单 */
    #MainMenu { display: none !important; }
    /* 隐藏底部 Created by Streamlit 页脚 */
    footer { display: none !important; }
    /* 终极暴力隐藏右下角的 Manage App 和 Streamlit Logo 浮窗 (覆盖所有新老版本标签) */
    .viewerBadge_container { display: none !important; }
    .viewerBadge_link { display: none !important; }
    .viewerBadge_text { display: none !important; }
    [data-testid="stViewerBadge"] { display: none !important; }
    [data-testid="manage-app-button"] { display: none !important; }
    /* 隐藏顶部可能出现的 Toolbar */
    [data-testid="stToolbar"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# ====== 客户端模式拦截器 ======
query_params = st.query_params
client_cat = query_params.get("cat")
client_id = query_params.get("id")
is_client_mode = bool(client_cat and client_id)

all_records = load_records()

if is_client_mode:
    # 彻底隐藏后台工具，打造极致 C 端体验 (免密阅读)
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header { visibility: hidden !important; }
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
    
    page_map = {"运势版": "📊 全息能量档案", "人格版": "👁️ 内核透视矩阵", "合盘版": "💞 双人宿命羁绊 (合盘版)"}
    page_selection = page_map.get(client_cat, "📊 全息能量档案")
    show_teleprompter = False # 强制关闭销讲
    st.markdown("<h4 style='text-align:center; color:#888; letter-spacing: 5px; font-weight: 300; margin-bottom: 30px;'>— 拨雾计划 专属数字档案 —</h4>", unsafe_allow_html=True)

else:
    # --- 正常主理人模式 ---
    
    # ====== V16 核心升级：主理人后台密码锁 ======
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        # 拦截状态：显示密码输入框
        st.markdown("""
            <style>
            .block-container { max-width: 500px; padding-top: 100px; }
            [data-testid="stSidebar"] { display: none !important; }
            /* 修复：移除了 header 隐藏代码，防止误杀侧边栏召唤箭头 */
            </style>
        """, unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; margin-bottom: 30px; color: #00E5FF; letter-spacing: 2px;'>🔒 拨雾计划引擎终端</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color: #888; margin-bottom: 30px;'>Admin Access Only / 主理人身份验证</p>", unsafe_allow_html=True)
        
        pwd = st.text_input("请输入访问密钥：", type="password", key="admin_pwd", placeholder="Please enter your access key...")
        
        # 【修改密码看这里】：把 "bowu888" 改成你想要的任何密码
        if st.button("🔑 验证登入", use_container_width=True, type="primary"):
            if pwd == "bowu888": 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 密钥错误，拒绝访问！触发防盗刷警报。")
                
        st.stop() # 密码不对，强行阻断下方所有后台代码的运行！

    # ====== 密码验证通过后，显示正常后台 ======
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
    page_selection = st.sidebar.radio("请选择要生成的交付报告：", ["📊 全息能量档案", "👁️ 内核透视矩阵", "💞 双人宿命羁绊 (合盘版)"])
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("☁️ 团队云端同步配置 (SaaS联机)"):
        cfg = get_cloud_cfg()
        st.caption("填入密钥后，你和团队成员的数据将实时同步！")
        c_api = st.text_input("API Key", value=cfg.get("api_key", ""), type="password")
        c_bin = st.text_input("Bin ID", value=cfg.get("bin_id", ""))
        if st.button("🔗 连接云端网络", use_container_width=True):
            if c_api.strip() and c_bin.strip():
                with open(CLOUD_CFG_FILE, 'w', encoding='utf-8') as f: json.dump({"api_key": c_api.strip(), "bin_id": c_bin.strip()}, f)
                st.success("✅ 云端配置已保存！"); st.rerun()
            else:
                if os.path.exists(CLOUD_CFG_FILE): os.remove(CLOUD_CFG_FILE)
                st.info("已断开云端。"); st.rerun()
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### 🛠️ 商业转化工具")
    show_teleprompter = st.sidebar.checkbox("👁️ 开启主理人销讲提词器", value=False)
    st.sidebar.markdown("---")


# ================= 渲染核心逻辑分离 =================
data_to_render = None

# 【运势版】
if page_selection == "📊 全息能量档案":
    if not is_client_mode:
        st.title("🔮 【拨雾计划】专属全息能量档案")
        st.markdown("---")
        st.sidebar.markdown("### 📂 客户历史档案库")
        fortune_history = list(all_records.get("运势版", {}).keys())
        fortune_history.reverse() 
        selected_record = st.sidebar.selectbox("一键读取已存档案", ["-- 新建档案 / 粘贴新数据 --"] + fortune_history, key="history_fortune")
        
        if selected_record != "-- 新建档案 / 粘贴新数据 --":
            st.sidebar.success(f"👁️ 正在查看历史记录：\n\n**{selected_record}**")
            if st.sidebar.button("🗑️ 删除此档案", type="secondary", use_container_width=True, key="del_fortune"):
                delete_record("运势版", selected_record); st.rerun()
            data_to_render = all_records["运势版"][selected_record]
        else:
            st.sidebar.warning("⚠️ 粘贴数据后请点击刷新按钮！")
            raw_json_input = st.sidebar.text_area("在此粘贴【运势】JSON 代码", value="", height=300)
            if st.sidebar.button("🔄 确认并生成运势报告", type="primary", use_container_width=True):
                pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败，JSON不完整。")
            else:
                st.markdown("<div class='empty-state'><h2>⏳ 引擎待机中...</h2><p>请在左侧控制台粘贴数据，或读取历史记录。</p></div>", unsafe_allow_html=True)
    else:
        # C端模式直接读取
        data_to_render = all_records.get("运势版", {}).get(client_id)
        if not data_to_render: st.error("⚠️ 链接已失效或档案不存在。")

    # 统一渲染核心数据
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
        # --- 修复滑动误触：增加 dragmode=False 和 fixedrange=True ---
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_type='category', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), hovermode="x unified", height=450, margin=dict(l=0, r=0, t=40, b=0), dragmode=False)
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        # config={'displayModeBar': False} 隐藏右上角工具栏
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
        
        # === 核心：入库与生成分享链接 ===
        if not is_client_mode:
            if selected_record == "-- 新建档案 / 粘贴新数据 --":
                st.markdown('<div class="save-module">### 💾 将此报告存入本地档案库', unsafe_allow_html=True)
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1: save_name = st.text_input("客户标识（如：小红书-李女士）：", key="save_name_fortune")
                with col_save2:
                    st.write(""); st.write("")
                    if st.button("💾 一键入库", type="primary", use_container_width=True):
                        if save_name.strip():
                            save_record("运势版", save_name.strip(), data); st.success("✅ 档案入库成功！页面即将刷新..."); st.rerun() 
                        else: st.error("⚠️ 请先输入客户标识！")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # 已存档案，直接生成 C端 URL
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给客户！")
                
                # 对链接核心参数进行 URL 安全编码防截断
                encoded_cat = urllib.parse.quote("运势版")
                encoded_id = urllib.parse.quote(selected_record)
                share_url = f"https://bowuplan.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")


# 【人格版】
elif page_selection == "👁️ 内核透视矩阵":
    if not is_client_mode:
        st.title("👁️ 【拨雾计划】目标内核深度透析矩阵")
        st.markdown("---")
        st.sidebar.markdown("### 📂 客户历史档案库")
        npd_history = list(all_records.get("人格版", {}).keys())
        npd_history.reverse()
        selected_record_npd = st.sidebar.selectbox("一键读取已存档案", ["-- 新建档案 / 粘贴新数据 --"] + npd_history)
        
        if selected_record_npd != "-- 新建档案 / 粘贴新数据 --":
            st.sidebar.success(f"👁️ 正在查看：**{selected_record_npd}**")
            if st.sidebar.button("🗑️ 删除此档案", type="secondary", use_container_width=True):
                delete_record("人格版", selected_record_npd); st.rerun()
            data_to_render = all_records["人格版"][selected_record_npd]
        else:
            raw_json_input = st.sidebar.text_area("在此粘贴【人格透析】JSON 代码", height=300)
            if st.sidebar.button("🔄 确认并生成报告", type="primary", use_container_width=True): pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败。")
            else: st.markdown("<div class='empty-state'><h2>👁️ 矩阵待机中...</h2></div>", unsafe_allow_html=True)
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
        # --- 修复滑动误触与手机端文字被切断 ---
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
            if selected_record_npd == "-- 新建档案 / 粘贴新数据 --":
                st.markdown('<div class="save-module">### 💾 存入档案库', unsafe_allow_html=True)
                save_name = st.text_input("客户标识：", key="save_name_npd")
                if st.button("💾 一键入库", type="primary"):
                    if save_name.strip(): save_record("人格版", save_name.strip(), data); st.rerun() 
            else:
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给客户！")
                
                # 对链接核心参数进行 URL 安全编码防截断
                encoded_cat = urllib.parse.quote("人格版")
                encoded_id = urllib.parse.quote(selected_record_npd)
                share_url = f"https://bowuplan.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")


# 【合盘版】
elif page_selection == "💞 双人宿命羁绊 (合盘版)":
    if not is_client_mode:
        st.title("💞 【拨雾计划】双人宿命羁绊透析矩阵")
        st.markdown("---")
        st.sidebar.markdown("### 📂 客户历史档案库")
        synastry_history = list(all_records.get("合盘版", {}).keys())
        synastry_history.reverse()
        selected_record_syn = st.sidebar.selectbox("一键读取已存档案", ["-- 新建档案 / 粘贴新数据 --"] + synastry_history)
        
        if selected_record_syn != "-- 新建档案 / 粘贴新数据 --":
            st.sidebar.success(f"👁️ 正在查看：**{selected_record_syn}**")
            if st.sidebar.button("🗑️ 删除此档案", type="secondary", use_container_width=True):
                delete_record("合盘版", selected_record_syn); st.rerun()
            data_to_render = all_records["合盘版"][selected_record_syn]
        else:
            raw_json_input = st.sidebar.text_area("在此粘贴【合盘】JSON 代码", height=300)
            if st.sidebar.button("🔄 确认并生成报告", type="primary", use_container_width=True): pass
            if raw_json_input.strip():
                try: data_to_render = parse_clean_json(raw_json_input)
                except: st.error("⚠️ 解析失败。")
            else: st.markdown("<div class='empty-state'><h2>💞 引擎待机中...</h2></div>", unsafe_allow_html=True)
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
            # --- 修复滑动误触 ---
            fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=300, margin=dict(l=20, r=20, t=50, b=20), dragmode=False)
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
        with col_desc:
            st.write(""); st.write("")
            st.info(f"**📖 宿命羁绊定调**：\n\n{data['合盘总评'].get('宿命羁绊定调', '')}")
            col_tag1, col_tag2 = st.columns(2)
            with col_tag1: st.markdown(f"<div style='background-color:rgba(255,105,180,0.1); padding:10px; border-radius:8px; border-left:3px solid #FF69B4;'><b>🔮 关系定性：</b>{data['合盘总评'].get('关系定性', '')}</div>", unsafe_allow_html=True)
            with col_tag2: st.markdown(f"<div style='background-color:rgba(0,229,255,0.1); padding:10px; border-radius:8px; border-left:3px solid #00E5FF;'><b>⚖️ 权力格局：</b>{data['合盘总评'].get('权力格局', '')}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🚨 核心风险与隐患排查 (高敏指标)")
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
        # --- 修复滑动误触与手机端文字被切断 ---
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
            if selected_record_syn == "-- 新建档案 / 粘贴新数据 --":
                st.markdown('<div class="save-module">### 💾 存入档案库', unsafe_allow_html=True)
                save_name = st.text_input("合盘标识：", key="save_name_syn")
                if st.button("💾 一键入库", type="primary"):
                    if save_name.strip(): save_record("合盘版", save_name.strip(), data); st.rerun() 
            else:
                st.markdown("---")
                st.markdown("### 🔗 专属交付链接 (自动隐藏后台并免密)")
                st.caption("👇 点击下方代码框右上角的【复制图标】，即可一键复制并发送给客户！")
                
                # 对链接核心参数进行 URL 安全编码防截断
                encoded_cat = urllib.parse.quote("合盘版")
                encoded_id = urllib.parse.quote(selected_record_syn)
                share_url = f"https://bowuplan.streamlit.app/?cat={encoded_cat}&id={encoded_id}"
                st.code(share_url, language="text")
