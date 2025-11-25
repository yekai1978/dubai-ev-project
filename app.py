import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ==========================================
# 1. 配置与常量层 (Configuration & Constants)
# ==========================================
PAGE_CONFIG = {
    "layout": "wide",
    "page_title": "迪拜新能源超充投资模型 V10.4 Ultimate",
    "page_icon": "🇦🇪",
    "initial_sidebar_state": "expanded"
}

ADMIN_PASSWORD = "DbeVc"
FONT_FILENAME = 'NotoSansSC-Regular.ttf'

# 默认年度推演参数 (爬坡模型)
DEFAULT_PARAMS = {
    "daily_kwh": [50, 100, 150, 200, 250, 300, 350, 400, 450, 500],
    "staff": [2] * 10,
    "salary": [75000] * 10
}

# 自定义 CSS 样式 (适配侧边栏按钮)
CSS_STYLES = """
    <style>
    /* 头部横幅样式 */
    .main-header-container {
        background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 2rem 1rem; /* 稍微减小高度 */
        border-radius: 0 0 20px 20px;
        color: white; text-align: center;
        margin-top: -4rem; margin-bottom: 1rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .main-title { font-size: 2.2rem; font-weight: 800; margin: 0; letter-spacing: 1px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .sub-title { font-size: 1rem; opacity: 0.9; margin-top: 0.5rem; font-weight: 400; }

    /* 指标卡片优化 */
    [data-testid="stMetric"] {
        background-color: #ffffff; border-radius: 12px; padding: 20px;
        border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); border-color: #2c5364; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #2c5364 !important; font-weight: 800 !important; }

    /* 侧边栏样式 */
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
    [data-testid="stSidebar"] h1 { font-size: 1.5rem; color: #2c5364; }
    [data-testid="stSidebar"] h2 { font-size: 1.2rem; color: #203a43; margin-top: 1rem;}
    
    /* --- 重点优化：侧边栏提交按钮 --- */
    /* 让按钮在侧边栏底部更显眼 */
    [data-testid="stFormSubmitButton"] {
        margin-top: 1rem;
        padding-bottom: 1rem;
    }
    [data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: 700;
        background: linear-gradient(90deg, #2c5364 0%, #203a43 100%);
        border: none;
        box-shadow: 0 4px 10px rgba(44, 83, 100, 0.3);
        transition: all 0.2s ease;
        color: white !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        box-shadow: 0 6px 15px rgba(44, 83, 100, 0.5);
        transform: translateY(-1px);
        background: linear-gradient(90deg, #203a43 0%, #1e3c72 100%);
    }
    [data-testid="stFormSubmitButton"] > button:active { transform: scale(0.99); }
    /* --------------------------- */

    /* 移动端适配 */
    @media (max-width: 640px) {
        .main-title { font-size: 1.8rem; }
        [data-testid="stNumberInput"] input { width: 100%; }
    }
    </style>
"""

# ==========================================
# 2. 资源加载与安全层 (Resources & Security)
# ==========================================
@st.cache_resource
def load_custom_font():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, FONT_FILENAME)
    if os.path.exists(font_path): return fm.FontProperties(fname=font_path)
    else: return fm.FontProperties(family='sans-serif')

def check_password():
    if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
    if st.session_state["authenticated"]: return
    st.markdown("# 🔒 访问受限 (Access Restricted)")
    st.markdown("此模型包含敏感商业数据，请输入授权密码继续。")
    st.markdown("---")
    with st.form("login_form"):
        password_input = st.text_input("访问密码", type="password", placeholder="Enter Password...", label_visibility="collapsed")
        submit_button = st.form_submit_button("🔓 验证登录 (Verify)", type="primary", use_container_width=True)
        if submit_button:
            if password_input == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.toast("验证成功。", icon="✅")
                st.rerun()
            else: st.error("❌ 密码错误。")
    st.stop()

# ==========================================
# 3. 工具函数层 (Utility Functions)
# ==========================================
def dataframe_to_png(df, font_prop):
    df_display = df.copy()
    for col in df_display.columns:
        if pd.api.types.is_numeric_dtype(df_display[col]) and col != "年份":
             df_display[col] = df_display[col].apply(
                 lambda x: f"{x:,.0f}" if abs(x) > 100 else (f"{x:.1f}" if abs(x) > 1 else f"{x:.2f}")
             )
    fig, ax = plt.subplots(figsize=(14, len(df)*0.7 + 2))
    ax.axis('tight'); ax.axis('off')
    table = ax.table(cellText=df_display.values, colLabels=df_display.columns, loc='center', cellLoc='center')
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontproperties=font_prop); cell.set_edgecolor('#e0e0e0')
        if key[0] == 0:
            cell.set_facecolor('#2c5364'); cell.get_text().set_color('white'); cell.get_text().set_weight('bold'); cell.set_height(0.08)
        else:
            cell.set_height(0.06)
            if key[0] % 2 == 0: cell.set_facecolor('#f8f9fa')
    table.auto_set_font_size(False); table.set_fontsize(11); table.scale(1.1, 1.1)
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, transparent=True); buf.seek(0); plt.close(fig)
    return buf

# ==========================================
# 4. 核心逻辑层 (Core Logic) - 纯计算
# ==========================================
def calculate_capex_details(inputs):
    capex_charger = (inputs['price_pile_unit'] * inputs['qty_piles'])
    capex_trans = (inputs['price_trans_unit'] * inputs['qty_trans'])
    capex_power_infra = inputs['cost_dewa_conn'] + inputs['cost_hv_cable'] + inputs['cost_lv_cable']
    capex_civil = inputs['cost_civil_work'] + inputs['cost_canopy'] + inputs['cost_design']
    capex_others = inputs['cost_weak_current_total'] + inputs['other_cost_1'] + inputs['other_cost_2']
    capex_infra_total = capex_trans + capex_power_infra + capex_civil + capex_others
    total_capex = capex_charger + capex_infra_total
    return {"total_capex": total_capex, "capex_charger": capex_charger, "capex_infra": capex_infra_total}

def calculate_financial_model(edited_df, capex_data, inputs):
    results = []
    total_capex = capex_data["total_capex"]
    results.append({"年份": "Y0", "营收": 0, "成本(OPEX)": 0, "折旧(抵税)": 0, "息税前利(EBIT)": 0, "税金": 0, "净利润": 0, "自由现金流(FCF)": -total_capex, "累计现金流": -total_capex})
    cumulative_cash = -total_capex
    payback_year = None
    total_guns = inputs['qty_piles'] * inputs['guns_per_pile']
    dep_charger_annual = capex_data["capex_charger"] / inputs['dep_years_charger'] if inputs['dep_years_charger'] > 0 else 0
    dep_infra_annual = capex_data["capex_infra"] / inputs['dep_years_infra'] if inputs['dep_years_infra'] > 0 else 0

    for index, row in edited_df.iterrows():
        year_idx = index; year_num = year_idx + 1
        daily_kwh = row["单枪日均充电量 (kWh)"]; staff_count = row["运营人数 (人)"]; salary_avg = row["人均年薪 (AED)"]
        
        current_price_sale = inputs['price_sale'] * ((1 + inputs['price_sale_growth']) ** year_idx)
        current_price_cost = inputs['price_cost'] * ((1 + inputs['price_cost_growth']) ** year_idx)
        annual_sales_kwh = daily_kwh * total_guns * 365
        revenue = annual_sales_kwh * current_price_sale
        
        annual_buy_kwh = annual_sales_kwh / inputs['power_efficiency']
        cost_power = annual_buy_kwh * current_price_cost
        inflation_factor = (1 + inputs['inflation_rate']) ** year_idx
        current_labor = (staff_count * salary_avg) * inflation_factor
        fixed_opex_base = inputs['base_rent'] + inputs['base_it_saas'] + inputs['base_marketing'] + inputs['base_maintenance']
        current_fixed = fixed_opex_base * inflation_factor
        total_opex = cost_power + current_labor + current_fixed
        
        ebitda = revenue - total_opex
        current_dep_charger = dep_charger_annual if year_num <= inputs['dep_years_charger'] else 0
        current_dep_infra = dep_infra_annual if year_num <= inputs['dep_years_infra'] else 0
        current_total_depreciation = current_dep_charger + current_dep_infra
        ebit = ebitda - current_total_depreciation
        cost_finance = total_capex * inputs['interest_rate']
        ebt = ebit - cost_finance
        tax_amount = (ebt - inputs['tax_threshold']) * inputs['tax_rate'] if ebt > inputs['tax_threshold'] else 0
        net_profit = ebt - tax_amount
        free_cash_flow = net_profit + current_total_depreciation
        cumulative_cash += free_cash_flow
        
        if payback_year is None and cumulative_cash >= 0:
            prev_cash = results[-1]["累计现金流"]
            payback_year = (year_idx) + (abs(prev_cash) / free_cash_flow) if free_cash_flow > 0 else year_idx + 1

        results.append({"年份": f"Y{year_num}", "营收": revenue, "成本(OPEX)": total_opex, "折旧(抵税)": current_total_depreciation, "息税前利(EBIT)": ebit, "税金": tax_amount, "净利润": net_profit, "自由现金流(FCF)": free_cash_flow, "累计现金流": cumulative_cash})
    
    return pd.DataFrame(results), payback_year

# ==========================================
# 5. 界面渲染层 (UI Rendering) - 纯展示
# ==========================================
def render_header():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    st.markdown("""
        <div class="main-header-container">
            <div class="main-title">🇦🇪 迪拜新能源超充站 · 投资测算模型</div>
            <div class="sub-title">V10.4 Ultimate | 侧边栏集成控制台 | 专业级UI体验</div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar_and_get_inputs():
    """渲染整合后的侧边栏控制台，并返回所有输入和提交状态"""
    with st.sidebar:
        st.header("🎛️ 控制台 (Control Panel)")
        
        # --- 配置导入 (表单外) ---
        with st.expander("📂 导入/恢复配置", expanded=False):
            uploaded_config = st.file_uploader("上传CSV", type=["csv"], label_visibility="collapsed")
            if uploaded_config is not None:
                try:
                    df_uploaded = pd.read_csv(uploaded_config)
                    required_columns = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
                    if all(col in df_uploaded.columns for col in required_columns):
                        st.session_state['df_config_cache'] = df_uploaded
                        st.toast("✅ 配置已加载。", icon="📂")
                    else: st.error("❌ 格式错误。")
                except Exception as e: st.error(f"❌ 读取失败：{e}")
        st.divider()
        
        # --- 主输入表单 (包含所有参数) ---
        with st.form("main_calculator_form"):
            st.subheader("1. 项目规模与周期 (Project Setup)")
            inputs = {}
            c1, c2 = st.columns(2)
            inputs['qty_piles'] = c1.number_input("拟投主机(台)", 2, 1, 100)
            inputs['qty_trans'] = c2.number_input("拟投变压器(台)", 1, 1, 20)
            
            c3, c4 = st.columns(2)
            inputs['interest_rate'] = c3.number_input("资金成本(%)", 5.0, 0.5, 0.0, 30.0) / 100
            inputs['years_duration'] = c4.number_input("测算年限(年)", 10, 1, 5, 20)
            
            c5, c6 = st.columns(2)
            inputs['price_sale'] = c5.number_input("销售电价(AED)", 1.20, 0.05, 0.1, 5.0)
            inputs['price_cost'] = c6.number_input("进货电价(AED)", 0.44, 0.05, 0.1, 5.0)

            st.markdown("---")
            st.subheader("⚙️ 后台参数微调 (Backend Config)")
            
            with st.expander("🏗️ CAPEX 基建设备参数", expanded=False):
                ec1, ec2 = st.columns(2)
                inputs['pile_power_kw'] = ec1.number_input("主机功率(kW)", 480, 20, 0, 2000)
                inputs['guns_per_pile'] = ec2.number_input("单机枪数(把)", 6, 1, 1, 30)
                inputs['price_pile_unit'] = st.number_input("主机单价(AED)", 200000, 5000, 0)
                tc1, tc2 = st.columns(2)
                trans_type = tc1.selectbox("变电站规格", ["1000 kVA", "1500 kVA"])
                inputs['trans_val'] = 1000 if "1000" in trans_type else 1500
                inputs['price_trans_unit'] = tc2.number_input("变电站单价", (200000 if inputs['trans_val']==1000 else 250000), 5000, 0)
                inputs['cost_dewa_conn'] = st.number_input("DEWA接入费", 200000, 10000, 0)
                inputs['cost_civil_work'] = st.number_input("土建施工费", 150000, 10000, 0)
                inputs['cost_hv_cable'] = st.number_input("高压电缆", 20000, 1000, 0)
                inputs['cost_lv_cable'] = st.number_input("低压电缆", 80000, 5000, 0)
                inputs['cost_canopy'] = st.number_input("遮阳棚品牌", 80000, 5000, 0)
                inputs['cost_design'] = st.number_input("设计顾问费", 40000, 5000, 0)
                inputs['cost_weak_current_total'] = st.number_input("弱电系统总包", 70000, 5000, 0)
                inputs['other_cost_1'] = st.number_input("前期开办费", 30000, 5000, 0)
                inputs['other_cost_2'] = st.number_input("不可预见金", 20000, 5000, 0)

            with st.expander("🛠️ OPEX 固定运营参数", expanded=False):
                inputs['base_rent'] = st.number_input("车位租金(AED/年)", 96000, 5000, 0)
                inputs['base_it_saas'] = st.number_input("IT/SaaS(AED/年)", 50000, 1000, 0)
                inputs['base_marketing'] = st.number_input("广告营销(AED/年)", 50000, 1000, 0)
                inputs['base_maintenance'] = st.number_input("维保外包(AED/年)", 30000, 1000, 0)

            with st.expander("📉 财务核心假设", expanded=True):
                fc1, fc2 = st.columns(2)
                inputs['power_efficiency'] = fc1.number_input("⚡ 电能效率(%)", 95.0, 0.5, 50.0, 100.0) / 100
                inputs['inflation_rate'] = fc2.number_input("📈 通胀率(%)", 3.0, 0.5, 0.0, 50.0) / 100
                pc1, pc2 = st.columns(2)
                inputs['price_sale_growth'] = pc1.number_input("💹 销售涨幅(%)", 0.0, 0.5, -10.0, 20.0) / 100
                inputs['price_cost_growth'] = pc2.number_input("💹 成本涨幅(%)", 0.0, 0.5, -10.0, 20.0) / 100
                tc1, tc2 = st.columns(2)
                inputs['tax_rate'] = tc1.number_input("🏛️ 税率(%)", 9.0, 1.0, 0.0, 50.0) / 100
                inputs['tax_threshold'] = tc2.number_input("免税额度", 375000, 10000, 0)
                dc1, dc2 = st.columns(2)
                inputs['dep_years_charger'] = dc1.number_input("🔋 设备折旧(年)", 5, 1, 2, 15)
                inputs['dep_years_infra'] = dc2.number_input("🏗️ 基建折旧(年)", 15, 1, 5, 40)

            st.write("") # Spacer
            # --- 重点优化：简化的提交按钮，位于侧边栏最底部 ---
            submitted = st.form_submit_button("🚀 运行测算 (Run Analysis)", type="primary", use_container_width=True)
            
    return inputs, submitted

def render_main_content(all_inputs, form_submitted):
    """渲染主界面内容"""
    # 容量校验 (实时显示)
    total_power = all_inputs['qty_piles'] * all_inputs['pile_power_kw']
    total_trans = all_inputs['qty_trans'] * all_inputs['trans_val']
    if total_power > total_trans:
        st.warning(f"⚠️ **容量提示**: 总功率 {total_power}kW > 变压器 {total_trans}kVA")
    else:
        st.success(f"✅ **配置确认**: {all_inputs['qty_piles']*all_inputs['guns_per_pile']}枪 | 总功率 {total_power}kW | 变压器 {total_trans}kVA")

    # 计算并显示 CAPEX 明细
    capex_data = calculate_capex_details(all_inputs)
    with st.expander("💰 **查看 Year 0 初始投资 (CAPEX) 明细**", expanded=False):
        st.info(f"**总投入：{capex_data['total_capex']:,.0f} AED**")
        c1, c2 = st.columns(2)
        c1.metric("🔋 充电设备类投资", f"{capex_data['capex_charger']:,.0f} AED")
        c2.metric("🏗️ 基建与电力配套投资", f"{capex_data['capex_infra']:,.0f} AED")

    # 渲染动态表格 (主界面核心)
    st.header("2. 年度运营推演核心表 (Dynamic Table)")
    st.info("👉 请在左侧设置参数，并在下方表格修改年度假设，最后点击侧边栏底部的 **“🚀 运行测算”** 按钮。")
    
    years_duration = all_inputs['years_duration']
    df_input = None
    if st.session_state.get('df_config_cache') is not None:
        df_uploaded = st.session_state['df_config_cache']
        required_cols = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
        if all(col in df_uploaded.columns for col in required_cols):
            if len(df_uploaded) < years_duration:
                last_row = df_uploaded.iloc[-1]
                df_extra = pd.DataFrame([last_row] * (years_duration - len(df_uploaded)))
                df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
            else: df_input = df_uploaded.head(years_duration)
        else: st.session_state.pop('df_config_cache', None)

    if df_input is None:
        long_daily_kwh = DEFAULT_PARAMS['daily_kwh'] + [DEFAULT_PARAMS['daily_kwh'][-1]] * years_duration
        long_staff = DEFAULT_PARAMS['staff'] + [DEFAULT_PARAMS['staff'][-1]] * years_duration
        long_salary = DEFAULT_PARAMS['salary'] + [DEFAULT_PARAMS['salary'][-1]] * years_duration
        df_input = pd.DataFrame({"单枪日均充电量 (kWh)": long_daily_kwh[:years_duration],"运营人数 (人)": long_staff[:years_duration],"人均年薪 (AED)": long_salary[:years_duration]})
    
    df_input["年份"] = [f"Y{i+1}" for i in range(years_duration)]
    df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]

    edited_df = st.data_editor(
        df_input,
        column_config={
            "年份": st.column_config.TextColumn(disabled=True, width="small"),
            "单枪日均充电量 (kWh)": st.column_config.NumberColumn(label="✏️ 单枪日均充电量 (kWh)", min_value=0, max_value=2000, step=10, required=True, format="%d kWh"),
            "运营人数 (人)": st.column_config.NumberColumn(label="✏️ 运营人数 (人)", min_value=0, step=1, format="%d 人"),
            "人均年薪 (AED)": st.column_config.NumberColumn(label="✏️ 人均年薪 (AED)", format="%d AED")
        },
        hide_index=True, use_container_width=True, height=int(38 * (min(years_duration, 12) + 2))
    )
    return edited_df, capex_data

def render_financial_report(df_res, total_capex, payback_year, years_duration):
    st.divider()
    st.header("📊 财务评估结果 (Financial Report)")
    total_net_profit = df_res["净利润"].sum()
    total_fcf_ops = df_res["净利润"].sum() + df_res["折旧(抵税)"].sum() 
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f}", help="建设期总投入")
    c2.metric("💸 运营期总净利", f"{total_net_profit:,.0f}", help="测算期内税后净利润总和")
    c3.metric("🌊 运营期自由现金流", f"{total_fcf_ops:,.0f}", help="测算期内经营活动产生的现金流 (净利润+折旧)")
    if payback_year and payback_year <= years_duration + 1: c4.metric("⏱️ 动态回本期", f"{payback_year:.1f} 年", delta="已回本", delta_color="normal")
    else: c4.metric("⏱️ 动态回本期", "未回本", delta="周期外", delta_color="inverse")
    st.write("")

    tab_chart, tab_table = st.tabs(["📈 累计现金流曲线 (J-Curve)", "📄 详细现金流表 (Cash Flow)"])
    with tab_chart: st.area_chart(df_res.set_index("年份")["累计现金流"], color="#2c5364", use_container_width=True)
    with tab_table:
        cols_to_show = ["营收", "成本(OPEX)", "折旧(抵税)", "息税前利(EBIT)", "税金", "净利润", "自由现金流(FCF)", "累计现金流"]
        st.dataframe(df_res.style.format("{:,.0f}", subset=cols_to_show), use_container_width=True)

def render_download_section(df_res, edited_df, font_prop):
    st.divider()
    with st.container(border=True):
        st.write("📥 **数据存取中心 (Data Center)**")
        c1, c2 = st.columns(2)
        with c1:
            st.caption("导出结果")
            csv_report = df_res.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📄 下载财务报告 (.csv)", csv_report, 'dubai_financial_report_v10.4.csv', 'text/csv', use_container_width=True)
            png_buffer = dataframe_to_png(df_res, font_prop)
            st.download_button("🖼️ 下载表格图片 (.png)", png_buffer, 'dubai_financial_report_v10.4.png', 'image/png', use_container_width=True)
        with c2:
            st.caption("保存配置")
            csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 保存当前运营配置 (.csv)", csv_config, 'operation_config_v10.4.csv', 'text/csv', use_container_width=True)

# ==========================================
# 6. 主控制流 (Main Execution)
# ==========================================
def main():
    st.set_page_config(**PAGE_CONFIG)
    zh_font = load_custom_font()
    check_password()
    render_header()

    # 1. 渲染侧边栏并获取所有输入和提交状态
    all_inputs, form_submitted = render_sidebar_and_get_inputs()

    # 2. 渲染主界面 (CAPEX信息 和 动态表格)
    edited_df, capex_data = render_main_content(all_inputs, form_submitted)

    # 3. 计算触发逻辑
    if 'calc_trigger' not in st.session_state: st.session_state['calc_trigger'] = False
    if form_submitted: st.session_state['calc_trigger'] = True

    if st.session_state['calc_trigger']:
        # 执行核心计算
        df_res, payback_year = calculate_financial_model(edited_df, capex_data, all_inputs)
        # 渲染结果和下载区
        render_financial_report(df_res, capex_data['total_capex'], payback_year, all_inputs['years_duration'])
        render_download_section(df_res, edited_df, zh_font)
    else:
        st.divider()
        st.info("👋 欢迎使用！请在左侧控制台调整参数，完成后点击 **“🚀 运行测算”**。")

if __name__ == "__main__":
    main()