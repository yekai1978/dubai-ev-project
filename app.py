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
    "page_title": "迪拜新能源超充投资模型 V10.3 Ultimate",
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

# 自定义 CSS 样式 (优化按钮与整体质感)
CSS_STYLES = """
    <style>
    /* 头部横幅样式 */
    .main-header-container {
        background: linear-gradient(90deg, #0f2027 0%, #203a43 50%, #2c5364 100%); /* 更深邃的迪拜夜景配色 */
        padding: 2.5rem 1rem;
        border-radius: 0 0 20px 20px;
        color: white; text-align: center;
        margin-top: -4rem; margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .main-title { font-size: 2.4rem; font-weight: 800; margin: 0; letter-spacing: 1px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .sub-title { font-size: 1.1rem; opacity: 0.9; margin-top: 0.8rem; font-weight: 400; }

    /* 指标卡片优化 */
    [data-testid="stMetric"] {
        background-color: #ffffff; border-radius: 12px; padding: 20px;
        border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); border-color: #2c5364; }
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #2c5364 !important; font-weight: 800 !important; }

    /* 侧边栏样式 */
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e9ecef; }
    
    /* --- 重点优化：表单提交按钮 --- */
    [data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border-radius: 10px;
        height: 3.5rem;
        font-size: 1.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #2c5364 0%, #203a43 100%); /* 使用主题深色渐变 */
        border: none;
        box-shadow: 0 4px 12px rgba(44, 83, 100, 0.4);
        transition: all 0.3s ease;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        box-shadow: 0 8px 20px rgba(44, 83, 100, 0.6);
        transform: scale(1.02);
    }
    [data-testid="stFormSubmitButton"] > button:active { transform: scale(0.98); }
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
    """加载自定义中文字体"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, FONT_FILENAME)
    if os.path.exists(font_path):
        return fm.FontProperties(fname=font_path)
    else:
        # print(f"Warning: Font '{FONT_FILENAME}' not found.")
        return fm.FontProperties(family='sans-serif')

def check_password():
    """安全验证门禁"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
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
                st.toast("验证成功，欢迎使用。", icon="✅")
                st.rerun()
            else:
                st.error("❌ 密码错误，请重试。")
    st.stop()

# ==========================================
# 3. 工具函数层 (Utility Functions)
# ==========================================
def dataframe_to_png(df, font_prop):
    """将 DataFrame 渲染为精美 PNG 图像"""
    df_display = df.copy()
    # 智能数值格式化
    for col in df_display.columns:
        if pd.api.types.is_numeric_dtype(df_display[col]) and col != "年份":
             df_display[col] = df_display[col].apply(
                 lambda x: f"{x:,.0f}" if abs(x) > 100 else (f"{x:.1f}" if abs(x) > 1 else f"{x:.2f}")
             )

    fig, ax = plt.subplots(figsize=(14, len(df)*0.7 + 2)) # 调整画布大小
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=df_display.values, colLabels=df_display.columns, loc='center', cellLoc='center')
    
    # 应用字体与样式
    for key, cell in table.get_celld().items():
        cell.set_text_props(fontproperties=font_prop)
        cell.set_edgecolor('#e0e0e0')
        if key[0] == 0: # 表头
            cell.set_facecolor('#2c5364')
            cell.get_text().set_color('white')
            cell.get_text().set_weight('bold')
            cell.set_height(0.08)
        else: # 数据行
            cell.set_height(0.06)
            if key[0] % 2 == 0: # 隔行变色
                cell.set_facecolor('#f8f9fa')

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.1, 1.1)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf

# ==========================================
# 4. 核心逻辑层 (Core Logic) - 纯计算
# ==========================================
def calculate_capex_details(inputs):
    """计算 CAPEX 明细，返回字典以便分类折旧"""
    # 1. 充电设备类
    capex_charger = (inputs['price_pile_unit'] * inputs['qty_piles'])
    
    # 2. 变电站及基建类 (包含变压器、电力接入、土建、弱电、杂项)
    capex_trans = (inputs['price_trans_unit'] * inputs['qty_trans'])
    capex_power_infra = inputs['cost_dewa_conn'] + inputs['cost_hv_cable'] + inputs['cost_lv_cable']
    capex_civil = inputs['cost_civil_work'] + inputs['cost_canopy'] + inputs['cost_design']
    capex_others = inputs['cost_weak_current_total'] + inputs['other_cost_1'] + inputs['other_cost_2']
    
    capex_infra_total = capex_trans + capex_power_infra + capex_civil + capex_others
    
    total_capex = capex_charger + capex_infra_total
    
    return {
        "total_capex": total_capex,
        "capex_charger": capex_charger,
        "capex_infra": capex_infra_total
    }

def calculate_financial_model(edited_df, capex_data, inputs):
    """执行年度财务推演计算（含动态电价与分类折旧抵税）"""
    results = []
    total_capex = capex_data["total_capex"]
    
    # Year 0 初始化
    results.append({
        "年份": "Y0", "营收": 0, "成本(OPEX)": 0, "折旧(抵税)": 0, "息税前利(EBIT)": 0,
        "税金": 0, "净利润": 0, "自由现金流(FCF)": -total_capex, "累计现金流": -total_capex
    })
    cumulative_cash = -total_capex
    payback_year = None
    total_guns = inputs['qty_piles'] * inputs['guns_per_pile']
    
    # --- 核心升级：计算分类年折旧额 (直线法) ---
    dep_charger_annual = capex_data["capex_charger"] / inputs['dep_years_charger'] if inputs['dep_years_charger'] > 0 else 0
    # 基建类资产通常折旧年限更长
    dep_infra_annual = capex_data["capex_infra"] / inputs['dep_years_infra'] if inputs['dep_years_infra'] > 0 else 0
    total_annual_depreciation = dep_charger_annual + dep_infra_annual
    # ---------------------------------------

    # 年度迭代
    for index, row in edited_df.iterrows():
        year_idx = index # 0-indexed (Y1=0)
        year_num = year_idx + 1
        
        # 1. 获取年度输入变量
        daily_kwh = row["单枪日均充电量 (kWh)"]
        staff_count = row["运营人数 (人)"]
        salary_avg = row["人均年薪 (AED)"]
        
        # 2. 计算动态电价 (考虑年增长率)
        current_price_sale = inputs['price_sale'] * ((1 + inputs['price_sale_growth']) ** year_idx)
        current_price_cost = inputs['price_cost'] * ((1 + inputs['price_cost_growth']) ** year_idx)

        # 3. 收入计算
        annual_sales_kwh = daily_kwh * total_guns * 365
        revenue = annual_sales_kwh * current_price_sale
        
        # 4. 支出计算 (OPEX)
        annual_buy_kwh = annual_sales_kwh / inputs['power_efficiency']
        cost_power = annual_buy_kwh * current_price_cost
        
        inflation_factor = (1 + inputs['inflation_rate']) ** year_idx
        current_labor = (staff_count * salary_avg) * inflation_factor
        fixed_opex_base = inputs['base_rent'] + inputs['base_it_saas'] + inputs['base_marketing'] + inputs['base_maintenance']
        current_fixed = fixed_opex_base * inflation_factor
        
        total_opex = cost_power + current_labor + current_fixed
        
        # 5. 利润计算 (含折旧抵税逻辑)
        ebitda = revenue - total_opex # 息税折旧前利润
        
        # 计算当年实际折旧额 (考虑折旧期满)
        current_dep_charger = dep_charger_annual if year_num <= inputs['dep_years_charger'] else 0
        current_dep_infra = dep_infra_annual if year_num <= inputs['dep_years_infra'] else 0
        current_total_depreciation = current_dep_charger + current_dep_infra
        
        ebit = ebitda - current_total_depreciation # 息税前利润
        
        cost_finance = total_capex * inputs['interest_rate'] # 资金成本(利息)
        ebt = ebit - cost_finance # 税前利润
        
        # 税务计算
        tax_amount = 0
        if ebt > inputs['tax_threshold']:
            tax_amount = (ebt - inputs['tax_threshold']) * inputs['tax_rate']
        
        net_profit = ebt - tax_amount # 净利润
        
        # 6. 现金流计算 (FCF近似 = 净利润 + 折旧加回)
        free_cash_flow = net_profit + current_total_depreciation
        
        cumulative_cash += free_cash_flow
        
        # 7. 回本期计算
        if payback_year is None and cumulative_cash >= 0:
            prev_cash = results[-1]["累计现金流"]
            if free_cash_flow > 0:
                 payback_year = (year_idx) + (abs(prev_cash) / free_cash_flow)
            else:
                 payback_year = year_idx + 1

        results.append({
            "年份": f"Y{year_num}",
            "营收": revenue, "成本(OPEX)": total_opex, "折旧(抵税)": current_total_depreciation,
            "息税前利(EBIT)": ebit, "税金": tax_amount, "净利润": net_profit,
            "自由现金流(FCF)": free_cash_flow, "累计现金流": cumulative_cash
        })
    
    return pd.DataFrame(results), payback_year

# ==========================================
# 5. 界面渲染层 (UI Rendering) - 纯展示
# ==========================================
def render_header():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    st.markdown("""
        <div class="main-header-container">
            <div class="main-title">🇦🇪 迪拜新能源超充站 · 投资测算模型</div>
            <div class="sub-title">V10.3 Ultimate | 精细化折旧抵税 | 动态电价 | 专业级UI交互</div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar_content():
    """渲染侧边栏：配置导入与后台参数"""
    with st.sidebar:
        st.header("🎛️ 控制面板 (Control Panel)")
        
        with st.expander("📂 **导入历史配置**", expanded=False):
            uploaded_config = st.file_uploader("上传配置CSV", type=["csv"], label_visibility="collapsed")
            if uploaded_config is not None:
                try:
                    df_uploaded = pd.read_csv(uploaded_config)
                    required_columns = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
                    if all(col in df_uploaded.columns for col in required_columns):
                        st.session_state['df_config_cache'] = df_uploaded
                        st.toast("✅ 配置已加载，请在主界面表单确认。", icon="📂")
                    else:
                        st.error("❌ 格式错误，缺少必要列。")
                except Exception as e: st.error(f"❌ 读取失败：{e}")
        
        st.divider()
        st.subheader("⚙️ 后台基准配置")
        inputs = {}
        
        with st.expander("🏗️ **CAPEX 基建设备参数**", expanded=False):
            st.caption("核心设备与基建单价设定")
            c1, c2 = st.columns(2)
            inputs['pile_power_kw'] = c1.number_input("主机功率(kW)", 480, 20)
            inputs['guns_per_pile'] = c2.number_input("单机枪数(把)", 6, 1)
            inputs['price_pile_unit'] = st.number_input("主机单价(AED)", 200000, 5000)
            
            t1, t2 = st.columns(2)
            trans_type = t1.selectbox("变电站规格", ["1000 kVA", "1500 kVA"])
            inputs['trans_val'] = 1000 if "1000" in trans_type else 1500
            inputs['price_trans_unit'] = t2.number_input("变电站单价(AED)", (200000 if inputs['trans_val']==1000 else 250000), 5000)
            
            st.markdown("---")
            e1, e2 = st.columns(2)
            inputs['cost_dewa_conn'] = e1.number_input("DEWA接入费", 200000, 10000)
            inputs['cost_civil_work'] = e2.number_input("土建施工费", 150000, 10000)
            inputs['cost_hv_cable'] = e1.number_input("高压电缆", 20000, 1000)
            inputs['cost_lv_cable'] = e2.number_input("低压电缆", 80000, 5000)
            inputs['cost_canopy'] = st.number_input("遮阳棚品牌", 80000, 5000)
            inputs['cost_design'] = st.number_input("设计顾问费", 40000, 5000)
            
            st.markdown("---")
            inputs['cost_weak_current_total'] = st.number_input("弱电系统总包", 70000, 5000, help="含监控、地锁、网络")
            inputs['other_cost_1'] = st.number_input("前期开办费", 30000, 5000)
            inputs['other_cost_2'] = st.number_input("不可预见金", 20000, 5000)

        with st.expander("🛠️ **OPEX 固定运营参数**", expanded=False):
            inputs['base_rent'] = st.number_input("车位租金(AED/年)", 96000, 5000)
            inputs['base_it_saas'] = st.number_input("IT/SaaS(AED/年)", 50000, 1000)
            inputs['base_marketing'] = st.number_input("广告营销(AED/年)", 50000, 1000)
            inputs['base_maintenance'] = st.number_input("维保外包(AED/年)", 30000, 1000)

        with st.expander("📉 **财务核心假设 (重点)**", expanded=True):
            f1, f2 = st.columns(2)
            inputs['power_efficiency'] = f1.number_input("⚡ 电能效率(%)", 95.0, 0.5, 50.0, 100.0) / 100
            inputs['inflation_rate'] = f2.number_input("📈 通胀率(%)", 3.0, 0.5) / 100
            
            st.markdown("---")
            st.caption("动态电价增长假设")
            p1, p2 = st.columns(2)
            inputs['price_sale_growth'] = p1.number_input("💹 销售涨幅(%)", 0.0, 0.5, help="年环比增长") / 100
            inputs['price_cost_growth'] = p2.number_input("💹 成本涨幅(%)", 0.0, 0.5, help="年环比增长") / 100
            
            st.markdown("---")
            st.caption("税务与折旧策略")
            t1, t2 = st.columns(2)
            inputs['tax_rate'] = t1.number_input("🏛️ 税率(%)", 9.0, 1.0) / 100
            inputs['tax_threshold'] = t2.number_input("免税额度", 375000, 10000)
            
            # --- 核心升级：拆分折旧年限 ---
            d1, d2 = st.columns(2)
            inputs['dep_years_charger'] = d1.number_input("🔋 充电设备折旧(年)", value=5, min_value=3, max_value=15, help="核心充电桩资产")
            inputs['dep_years_infra'] = d2.number_input("🏗️ 基建变电折旧(年)", value=15, min_value=10, max_value=30, help="变电站、土建等长期资产")
            # ---------------------------
            
        st.markdown("---")
        st.caption("Dubai EV Theme V10.3")
    return inputs

def render_project_inputs_form(backend_inputs):
    """渲染主界面表单"""
    st.header("1. 项目规模与周期设定 (Project Setup)")
    inputs = backend_inputs.copy()
    
    with st.form("project_inputs_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### A. 设备数量")
            inputs['qty_piles'] = st.number_input("拟投超充主机 (台)", 2, 1, 100)
            inputs['qty_trans'] = st.number_input("拟投变压器 (台)", 1, 1, 20)
        with c2:
            st.markdown("##### B. 资金与电价 (Y1基准)")
            inputs['interest_rate'] = st.number_input("资金成本费率 (%)", 5.0, 0.5) / 100
            inputs['price_sale'] = st.number_input("销售电价 (AED/kWh)", 1.20, 0.05)
            inputs['price_cost'] = st.number_input("进货电价 (AED/kWh)", 0.44, 0.05)
        with c3:
            st.markdown("##### C. 周期设定")
            inputs['years_duration'] = st.number_input("运营测算年限 (年)", value=10, min_value=5, max_value=20)
        
        st.write("") # spacer
        # --- 重点优化：现代感提交按钮，置于底部 ---
        submitted = st.form_submit_button("🚀 确认配置并运行测算模型 (Run Financial Model)", type="primary", use_container_width=True)

    # 容量校验 (表单外实时显示)
    total_power = inputs['qty_piles'] * inputs['pile_power_kw']
    total_trans = inputs['qty_trans'] * inputs['trans_val']
    if total_power > total_trans:
        st.warning(f"⚠️ **容量提示**: 总功率 {total_power}kW > 变压器 {total_trans}kVA，请留意。")
    else:
        st.success(f"✅ **配置确认**: {inputs['qty_piles']*inputs['guns_per_pile']}枪 | 总功率 {total_power}kW | 变压器 {total_trans}kVA")
        
    return inputs, submitted

def render_dynamic_table(years_duration):
    st.header("2. 年度运营推演核心表 (Dynamic Table)")
    # --- 重点优化：醒目的可编辑提示 ---
    st.info("👉 **操作提示**：请直接点击下方表格中带有 **✏️** 图标的列头，修改每年的关键假设数据。")
    
    # 数据准备 (自适应逻辑)
    df_input = None
    if st.session_state.get('df_config_cache') is not None:
        df_uploaded = st.session_state['df_config_cache']
        required_cols = ["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]
        if all(col in df_uploaded.columns for col in required_cols):
            if len(df_uploaded) < years_duration:
                last_row = df_uploaded.iloc[-1]
                df_extra = pd.DataFrame([last_row] * (years_duration - len(df_uploaded)))
                df_input = pd.concat([df_uploaded, df_extra], ignore_index=True)
            else:
                df_input = df_uploaded.head(years_duration)
        else:
             st.session_state.pop('df_config_cache', None) # 清除无效缓存

    if df_input is None:
        # 使用默认爬坡数据生成
        long_daily_kwh = DEFAULT_PARAMS['daily_kwh'] + [DEFAULT_PARAMS['daily_kwh'][-1]] * years_duration
        long_staff = DEFAULT_PARAMS['staff'] + [DEFAULT_PARAMS['staff'][-1]] * years_duration
        long_salary = DEFAULT_PARAMS['salary'] + [DEFAULT_PARAMS['salary'][-1]] * years_duration
        df_input = pd.DataFrame({
            "单枪日均充电量 (kWh)": long_daily_kwh[:years_duration],
            "运营人数 (人)": long_staff[:years_duration],
            "人均年薪 (AED)": long_salary[:years_duration]
        })
    
    df_input["年份"] = [f"Y{i+1}" for i in range(years_duration)]
    df_input = df_input[["年份", "单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]]

    # --- 重点优化：在表头增加编辑图标提示 ---
    edited_df = st.data_editor(
        df_input,
        column_config={
            "年份": st.column_config.TextColumn(disabled=True, width="small"),
            "单枪日均充电量 (kWh)": st.column_config.NumberColumn(label="✏️ 单枪日均充电量 (kWh)", min_value=0, max_value=1500, step=10, required=True, format="%d kWh"),
            "运营人数 (人)": st.column_config.NumberColumn(label="✏️ 运营人数 (人)", min_value=0, step=1, format="%d 人"),
            "人均年薪 (AED)": st.column_config.NumberColumn(label="✏️ 人均年薪 (AED)", format="%d AED")
        },
        hide_index=True, use_container_width=True, height=int(38 * (min(years_duration, 12) + 2))
    )
    return edited_df

def render_financial_report(df_res, total_capex, payback_year, years_duration):
    st.header("📊 财务评估结果 (Financial Report)")
    
    # 计算关键总计
    total_net_profit = df_res["净利润"].sum()
    # FCFE近似 = 净利润总和 + 折旧总和 (运营期产生的现金)
    total_fcf_ops = df_res["净利润"].sum() + df_res["折旧(抵税)"].sum() 
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 初始总投资 (CAPEX)", f"{total_capex:,.0f}", help="建设期总投入")
    c2.metric("💸 运营期总净利", f"{total_net_profit:,.0f}", help="测算期内税后净利润总和")
    c3.metric("🌊 运营期自由现金流", f"{total_fcf_ops:,.0f}", help="测算期内经营活动产生的现金流 (净利润+折旧)")
    
    if payback_year and payback_year <= years_duration + 1:
        c4.metric("⏱️ 动态回本期", f"{payback_year:.1f} 年", delta="已回本", delta_color="normal")
    else:
        c4.metric("⏱️ 动态回本期", "未回本", delta="周期外", delta_color="inverse")
    st.write("")

    tab_chart, tab_table = st.tabs(["📈 累计现金流曲线 (J-Curve)", "📄 详细现金流表 (Cash Flow)"])
    with tab_chart:
        st.area_chart(df_res.set_index("年份")["累计现金流"], color="#2c5364", use_container_width=True)
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
            st.download_button("📄 下载财务报告 (.csv)", csv_report, 'dubai_financial_report_v10.3.csv', 'text/csv', use_container_width=True)
            png_buffer = dataframe_to_png(df_res, font_prop)
            st.download_button("🖼️ 下载表格图片 (.png)", png_buffer, 'dubai_financial_report_v10.3.png', 'image/png', use_container_width=True)
        with c2:
            st.caption("保存配置")
            csv_config = edited_df[["单枪日均充电量 (kWh)", "运营人数 (人)", "人均年薪 (AED)"]].to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 保存当前运营配置 (.csv)", csv_config, 'operation_config_v10.3.csv', 'text/csv', use_container_width=True)

# ==========================================
# 6. 主控制流 (Main Execution)
# ==========================================
def main():
    st.set_page_config(**PAGE_CONFIG)
    zh_font = load_custom_font()
    check_password()

    render_header()
    backend_inputs = render_sidebar_content() # 获取侧边栏配置

    # 主界面流程
    all_inputs, form_submitted = render_project_inputs_form(backend_inputs)
    
    # 计算并显示 CAPEX 明细
    capex_data = calculate_capex_details(all_inputs)
    st.info(f"💰 **Year 0 总投入：{capex_data['total_capex']:,.0f} AED** (设备类: {capex_data['capex_charger']:,.0f} | 基建类: {capex_data['capex_infra']:,.0f})")

    # 渲染动态表格
    edited_df = render_dynamic_table(all_inputs['years_duration'])

    # 计算触发逻辑
    if 'calc_trigger' not in st.session_state: st.session_state['calc_trigger'] = False
    if form_submitted: st.session_state['calc_trigger'] = True

    if st.session_state['calc_trigger']:
        # 执行核心计算 (含精细化折旧)
        df_res, payback_year = calculate_financial_model(edited_df, capex_data, all_inputs)
        render_financial_report(df_res, capex_data['total_capex'], payback_year, all_inputs['years_duration'])
        render_download_section(df_res, edited_df, zh_font)
    else:
        st.divider()
        st.info("👉 请设定参数并编辑表格，最后点击下方 **“🚀 确认配置并运行测算模型”** 按钮查看结果。")

if __name__ == "__main__":
    main()