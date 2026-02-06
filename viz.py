import streamlit as st
import altair as alt
import pandas as pd

from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
st.set_page_config(page_title="Personal Activity Tracker", layout="wide", initial_sidebar_state="collapsed")
alt.data_transformers.disable_max_rows()

alt.renderers.enable('svg')

st.markdown("""
<style>
/* General text scaling */
body {
    font-size: 18px !important;
}

/* Subheaders */
[data-testid="stHeading"] h2 {
    font-size: 28px !important;
    margin-bottom: 10px !important;
}

/* Captions */
[data-testid="stCaptionContainer"] {
    font-size: 16px !important;
    line-height: 1.5;
}

/* Column headers and labels */
.stSelectbox label,
.stDateInput label,
.stSlider label,
.stNumberInput label,
.stTextInput label {
    font-size: 16px !important;
    font-weight: 500 !important;
}

/* Tab text */
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    gap: 12px;
    background-color: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    width: 100%;
}

.stTabs [data-baseweb="tab-list"] button {
    font-size: 19px !important;
    font-weight: 600 !important;
    padding: 14px 32px !important;
    letter-spacing: 0.5px;
    flex: 1;
    min-width: 180px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Active tab styling */
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    background-color: #0066cc !important;
    color: white !important;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.3);
}

/* Inactive tab styling */
.stTabs [data-baseweb="tab-list"] button[aria-selected="false"] {
    color: #333 !important;
    background-color: white !important;
    border: 1px solid #ddd;
    border-radius: 6px;
    transition: all 0.2s ease;
}

.stTabs [data-baseweb="tab-list"] button[aria-selected="false"]:hover {
    background-color: #e8f0ff !important;
    border-color: #0066cc;
}

/* Tab content area */
.stTabs [data-baseweb="tab"] {
    padding: 16px 0;
}

/* Metric values */
.metric-value {
    font-size: 18px !important;
}

/* Tooltip text in charts */
.vega-tooltip {
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('dataset.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['travel'] = df['travel_day'].astype(str).str.lower() == 'true'
    df['step_count'] = pd.to_numeric(df['step_count'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
    
    df['day_of_week'] = df['date'].dt.day_name()
    df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6])  
    df['day_type'] = df['is_weekend'].map({True: 'Weekend', False: 'Weekday'})
    
    return df

df = load_data()

def calculate_streak(df_sorted, target):
    if df_sorted.empty:
        return 0
    streak = 0
    for _, row in df_sorted.sort_values('date', ascending=False).iterrows():
        if pd.notna(row['step_count']) and row['step_count'] >= target:
            streak += 1
        else:
            break
    return streak

def calculate_consistency(df_filtered, target):
    valid_days = df_filtered[df_filtered['step_count'].notna()]
    if len(valid_days) == 0:
        return 0
    hit_target = len(valid_days[valid_days['step_count'] >= target])
    return (hit_target / len(valid_days)) * 100

def analyze_success_patterns(df_filtered, target):
    success_days = df_filtered[df_filtered['step_count'] >= target].copy()
    all_days = df_filtered[df_filtered['step_count'].notna()].copy()
    
    if len(success_days) == 0 or len(all_days) == 0:
        return {}
    
    patterns = {}
    
    # Weekend success rate
    weekend_success = len(success_days[success_days['is_weekend']]) / len(all_days[all_days['is_weekend']]) * 100 if len(all_days[all_days['is_weekend']]) > 0 else 0
    weekday_success = len(success_days[~success_days['is_weekend']]) / len(all_days[~all_days['is_weekend']]) * 100 if len(all_days[~all_days['is_weekend']]) > 0 else 0
    
    patterns['weekend_success_rate'] = weekend_success
    patterns['weekday_success_rate'] = weekday_success
    patterns['best_day_type'] = 'Weekends' if weekend_success > weekday_success else 'Weekdays'
    
    # Travel success rate
    travel_success = len(success_days[success_days['travel']]) / len(all_days[all_days['travel']]) * 100 if len(all_days[all_days['travel']]) > 0 else 0
    home_success = len(success_days[~success_days['travel']]) / len(all_days[~all_days['travel']]) * 100 if len(all_days[~all_days['travel']]) > 0 else 0
    
    patterns['travel_success_rate'] = travel_success
    patterns['home_success_rate'] = home_success
    
    # Best day of week
    dow_success = success_days.groupby('day_of_week').size() / all_days.groupby('day_of_week').size() * 100
    if not dow_success.empty:
        patterns['best_day_of_week'] = dow_success.idxmax()
        patterns['best_day_rate'] = dow_success.max()
    
    # Weather success
    if 'weather' in success_days.columns and success_days['weather'].notna().any():
        weather_success = success_days.groupby('weather').size() / all_days.groupby('weather').size() * 100
        if not weather_success.empty:
            patterns['best_weather'] = weather_success.idxmax()
            patterns['best_weather_rate'] = weather_success.max()
    
    return patterns

st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="margin-bottom: 5px;">🏃 Personal Activity Tracker</h1>
    <p style="font-size: 16px; color: #666;">Building healthy habits, one step at a time. Track your daily progress, and stay motivated to hit your goals consistently.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Activity", "✈️ Travel", "📝 About"])

# ============================================================================
# TAB 1: ACTIVITY ANALYSIS: Step trends, goal tracking, and consistency insights
# ============================================================================
with tab1:    
    col_set1, col_set2, col_set3 = st.columns([2, 2, 1])
    with col_set1:
        lookback_days = st.selectbox("View Period", [7, 14, 30, 60, 90], index=2, key='lookback')
    with col_set2:
        end_date = st.date_input("End Date", df['date'].max().date(), key='end_date_tracker')
    with col_set3:
        daily_target = st.number_input("Daily Step Goal", value=10000, min_value=1000, step=1000, key='target_tracker')
    
    start_date = pd.Timestamp(end_date) - timedelta(days=lookback_days-1)
    
    date_range = pd.date_range(start=start_date, end=pd.Timestamp(end_date), freq='D')
    
    recent_df = df[
        (df['date'] >= start_date) & 
        (df['date'] <= pd.Timestamp(end_date))
    ].copy()
    
    full_period_df = pd.DataFrame({'date': date_range})
    full_period_df = full_period_df.merge(recent_df, on='date', how='left')
    full_period_df['step_count'] = full_period_df['step_count'].fillna(0)
    if 'travel' in full_period_df.columns:
        full_period_df['travel'] = full_period_df['travel'].fillna(False).astype(bool)
    for col in ['day_of_week', 'is_weekend', 'day_type', 'weather', 'city']:
        full_period_df[col] = full_period_df[col].bfill().ffill()
    
    recent_df_original = recent_df.copy()
    recent_df = full_period_df
    
    current_streak = calculate_streak(recent_df_original, daily_target)
    consistency_rate = calculate_consistency(recent_df, daily_target)
    avg_steps = recent_df['step_count'].mean() if not recent_df.empty else 0
    total_steps = recent_df['step_count'].sum() if not recent_df.empty else 0
    days_hit_target = len(recent_df[recent_df['step_count'] >= daily_target])
    total_days = lookback_days
    
    success_patterns = analyze_success_patterns(recent_df_original, daily_target)
    
    progress_pct = (avg_steps / daily_target * 100) if daily_target > 0 else 0
    
    st.markdown("---")
    st.markdown("### 🎯 Am I Meeting My Step Goals?")
    st.caption(f"Data period: {lookback_days} days | From {start_date.date()} to {pd.Timestamp(end_date).date()}")
    
    col_m1, col_m2, col_m3 = st.columns(3, gap="large")
    
    with col_m1:
        if avg_steps >= daily_target:
            avg_color = "#10B981"  # Green
            bg_color = "#D1FAE5"
            status_text = "Goal achieved"
            status_color = "#10B981"
        else:
            avg_color = "#EF4444"  # Red
            bg_color = "#FEE2E2"
            status_text = f"{daily_target - avg_steps:,.0f} steps to goal"
            status_color = "#EF4444"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 36px 32px 32px 32px; border-radius: 16px; border-left: 10px solid {avg_color}; box-shadow: 0 6px 24px rgba(0,0,0,0.13); margin-bottom: 8px;">
            <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>Average Daily Steps</strong></p>
            <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: {avg_color};">{avg_steps:,.0f}</p>
            <p style="margin: 6px 0 0 0; color: {status_color}; font-size: 12px;">{status_text}</p>
            <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;"><strong>{days_hit_target}</strong> of <strong>{total_days}</strong> days hit goal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_m2:
        streak_color = "#3B82F6" if current_streak >= 7 else "#8B5CF6" if current_streak >= 3 else "#6B7280"
        st.markdown(f"""
        <div style="background-color: #EFF6FF; padding: 36px 32px 32px 32px; border-radius: 16px; border-left: 10px solid {streak_color}; box-shadow: 0 6px 24px rgba(0,0,0,0.13); margin-bottom: 8px;">
            <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>🔥 Current Streak</strong></p>
            <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: {streak_color};">{current_streak}</p>
            <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;">Consecutive days</p>
            <p style="margin: 6px 0 0 0; color: #9CA3AF; font-size: 12px;">{'🎯 Keep it going!' if current_streak > 0 else '🚀 Start today!'}</p>
        </div>
        """, unsafe_allow_html=True)

    # Trend indicator 
    with col_m3:
        today = pd.Timestamp(end_date)
        
        trend_days = lookback_days
        
        course_start = today - timedelta(days=trend_days-1)  # Current period start
        previous_course_start = course_start - timedelta(days=trend_days)  # Previous period start
        
        # Helper to get filled data
        def get_filled_period(start, end):
            dates = pd.date_range(start=start, end=end, freq='D')
            temp_df = pd.DataFrame({'date': dates})
            temp_df = temp_df.merge(df, on='date', how='left')
            return temp_df['step_count'].fillna(0)
            
        current_period_data = get_filled_period(course_start, today)
        previous_period_data = get_filled_period(previous_course_start, course_start - timedelta(days=1))
        
        if len(current_period_data) > 0 and len(previous_period_data) > 0:
            current_avg = current_period_data.mean()
            previous_avg = previous_period_data.mean()
            trend_change = ((current_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
            
            if trend_change > 0:
                trend_emoji = "📈"
                trend_text = f"+{trend_change:.0f}%"
                trend_color = "#10B981"
                trend_bg = "#D1FAE5"
            elif trend_change <= 0:
                trend_emoji = "📉"
                trend_text = f"{trend_change:.0f}%"
                trend_color = "#EF4444"
                trend_bg = "#FEE2E2"
            else:
                trend_emoji = "➡️"
                trend_text = "Stable"
                trend_color = "#8B5CF6"
                trend_bg = "#F3E8FF"
            
            trend_label = f"{trend_days}-Day Trend" if trend_days != 7 else "Weekly Trend"
            trend_sublabel = f"vs previous {trend_days} days" if trend_days != 7 else "vs last week"
            
            st.markdown(f"""
            <div style="background-color: {trend_bg}; padding: 28px; border-radius: 12px; border-left: 6px solid {trend_color}; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>{trend_emoji} {trend_label}</strong></p>
                <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: {trend_color};">{trend_text}</p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;">{trend_sublabel}</p>
                <p style="margin: 6px 0 0 0; color: #9CA3AF; font-size: 12px;">{'Momentum building!' if trend_change > 0 else 'Keep pushing!' if trend_change <= 0 else 'Consistent pace'}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            trend_label = f"{trend_days}-Day Avg" if trend_days != 7 else "This Week Avg"
            st.markdown(f"""
            <div style="background-color: #F0F9FF; padding: 28px; border-radius: 12px; border-left: 6px solid #0EA5E9; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>📊 {trend_label}</strong></p>
                <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: #0EA5E9;">{current_period_data.mean() if len(current_period_data) > 0 else 0:,.0f}</p>
                <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;">Steps per day</p>
                <p style="margin: 6px 0 0 0; color: #9CA3AF; font-size: 12px;">Current period</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if consistency_rate >= 80:
        final_msg = f"🌟 **Excellent!** You're hitting your goal {consistency_rate:.0f}% of the time."
        msg_type = "success"
    elif consistency_rate >= 60:
        final_msg = f"💪 **Good progress!** You're hitting your goal {consistency_rate:.0f}% of the time."
        msg_type = "info"
    elif consistency_rate >= 40:
        final_msg = f"📈 **Getting there!** You're hitting your goal {consistency_rate:.0f}% of the time. Try to add 1-2 more active days this week."
        msg_type = "warning"
    else:
        final_msg = f"🎯 **Focus on the target!** You're hitting your goal {consistency_rate:.0f}% of the time. Make more improvements and they will add up!"
        msg_type = "error"
        
    if msg_type == "success":
        st.success(final_msg)
    elif msg_type == "info":
        st.info(final_msg)
    elif msg_type == "warning":
        st.warning(final_msg)
    else:
        st.error(final_msg)
    
    st.markdown("---")
    
    st.subheader("📈 Daily Activity Trends")
    st.caption(f"Your steps over the last {lookback_days} days | Green bars = Goal achieved, Red bars = Below goal | **Weekends = Thick Black Borders, Travel Days = Thick Blue Borders** | Blue line = 7-day average trend")
    
    if not recent_df.empty:

        if 'is_weekend' not in recent_df.columns or recent_df['is_weekend'].dtype != bool:
            recent_df['is_weekend'] = recent_df['date'].dt.dayofweek.isin([5, 6])

        # Create color based on goal achievement
        recent_df['goal_met'] = recent_df['step_count'] >= daily_target

        # Calculate 7-day moving average
        recent_df = recent_df.sort_values('date')
        recent_df['moving_avg'] = recent_df['step_count'].rolling(window=7, min_periods=1).mean()

        # Borders for Bars
        def border_logic(row):
            if row['travel']:
                return 4, "#0452D0", 'solid' 
            elif row['is_weekend']:
                return 3, "#000000", 'solid'
            else:
                return 2.5, "#B0B0B0", 'solid'

        border_info = recent_df.apply(border_logic, axis=1)
        recent_df['stroke_width'] = [b[0] for b in border_info]
        recent_df['stroke_color'] = [b[1] for b in border_info]
        recent_df['stroke_dash_str'] = [b[2] for b in border_info]

        trend_chart = alt.Chart(recent_df).mark_bar(
            width=35  
        ).encode(
            x=alt.X('date:T', title='Date', 
                    axis=alt.Axis(
                        format='%b %d',
                        labelAngle=45,
                        labelAlign='left',
                        labelPadding=10,
                        tickCount=min(len(recent_df), 15)
                    )),
            y=alt.Y('step_count:Q', title='Daily Steps'),
            color=alt.condition(
                alt.datum.goal_met,
                alt.value('#10B981'),
                alt.value('#EF4444')
            ),
            strokeWidth=alt.StrokeWidth('stroke_width:Q', scale=alt.Scale(range=[1.5, 5]), legend=None), 
            stroke=alt.Stroke('stroke_color:N',
                       scale=alt.Scale(domain=['#B0B0B0', '#000000', '#0452D0'], range=['#B0B0B0', '#000000', '#0452D0']),
                       legend=None),
            strokeDash=alt.StrokeDash('stroke_dash_str:N', 
                             scale=alt.Scale(domain=['solid', 'dashed'], 
                                           range=[[], [3,3]]), legend=None),
            tooltip=[
                alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
                alt.Tooltip('day_of_week:N', title='Day'),
                alt.Tooltip('day_type:N', title='Type'),
                alt.Tooltip('step_count:Q', title='Steps', format=','),
                alt.Tooltip('moving_avg:Q', title='7-Day Avg', format=',.0f'),
                alt.Tooltip('travel:N', title='Traveling'),
                alt.Tooltip('city:N', title='City'),
                alt.Tooltip('weather:N', title='Weather')
            ]
        ).properties(
            height=350,
            width=1200
        )
        
        # Moving average line
        moving_avg_line = alt.Chart(recent_df).mark_line(
            color='#3B82F6',
            strokeWidth=3,
            point=True
        ).encode(
            x='date:T',
            y='moving_avg:Q',
            tooltip=[
                alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
                alt.Tooltip('moving_avg:Q', title='7-Day Avg', format=',.0f')
            ]
        )
        
        # Add target line
        target_line = alt.Chart(pd.DataFrame({'y': [daily_target]})).mark_rule(
            strokeDash=[5, 5],
            color='#6366F1',
            size=2
        ).encode(
            y='y:Q'
        )
        
        # Add text annotation for target
        target_text = alt.Chart(pd.DataFrame({'y': [daily_target], 'text': [f'Goal: {daily_target:,}']})).mark_text(
            align='right',
            dx=-5,
            dy=-5,
            color='#6366F1',
            fontSize=12,
            fontWeight='bold'
        ).encode(
            x=alt.value(700),
            y='y:Q',
            text='text:N'
        )
        
        combined_trend = (trend_chart + moving_avg_line + target_line + target_text).interactive()
        st.altair_chart(combined_trend, width='stretch')
        
        if len(recent_df) >= 14:
            first_week_avg = recent_df.head(7)['step_count'].mean()
            last_week_avg = recent_df.tail(7)['step_count'].mean()
            trend_change = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
            
            # Add weekend vs weekday analysis
            weekend_avg = recent_df[recent_df['is_weekend']]['step_count'].mean()
            weekday_avg = recent_df[~recent_df['is_weekend']]['step_count'].mean()
            
            interpretation = ""
            if trend_change > 0:
                interpretation = f"📈 **Trending up!** Your activity increased by {trend_change:.1f}% compared to the start of this period."
            elif trend_change < 0:
                interpretation = f"📉 **Trending down**: Activity decreased by {abs(trend_change):.1f}%. Consider what changed!"
            else:
                interpretation = f"➡️ **Steady**: Your activity is stable."
            
            # Add weekend context
            if pd.notna(weekend_avg) and pd.notna(weekday_avg):
                weekend_diff = ((weekend_avg - weekday_avg) / weekday_avg * 100) if weekday_avg > 0 else 0
                if abs(weekend_diff) > 15:
                    if weekend_diff > 0:
                        interpretation += f"\n\n🏖️ **Weekends matter!** You walk {weekend_diff:.0f}% more on weekends ({weekend_avg:,.0f} vs {weekday_avg:,.0f} steps). Weekend trips drive your activity!"
                    else:
                        interpretation += f"\n\n💼 **Weekdays matter!** You walk {abs(weekend_diff):.0f}% more on weekdays ({weekday_avg:,.0f} vs {weekend_avg:,.0f} steps). Your daily routine keeps you active!"
            
            if trend_change > 10 or (pd.notna(weekend_avg) and pd.notna(weekday_avg) and abs(weekend_diff) > 15):
                st.success(interpretation)
            elif trend_change < -10:
                st.warning(interpretation)
            else:
                st.info(interpretation)
    else:
        st.warning("No data available for the selected period.")
    
    st.markdown("---")
    
    # st.subheader("📅 Weekend vs Weekday Performance")
    # st.caption("Understanding how your routine differs between work and rest days")
    
    # if not recent_df.empty:
    #     day_type_data = recent_df[recent_df['step_count'].notna()].copy()
        
    #     if not day_type_data.empty:
    #         # Calculate stats by day type
    #         day_type_stats = day_type_data.groupby('day_type').agg({
    #             'step_count': ['mean', 'count', lambda x: (x >= daily_target).sum()]
    #         }).reset_index()
    #         day_type_stats.columns = ['day_type', 'avg_steps', 'total_days', 'goal_days']
    #         day_type_stats['success_rate'] = (day_type_stats['goal_days'] / day_type_stats['total_days'] * 100).round(1)
            
    #         # Metrics row
    #         col_d1, col_d2, col_d3 = st.columns(3)
            
    #         weekend_stats = day_type_stats[day_type_stats['day_type'] == 'Weekend']
    #         weekday_stats = day_type_stats[day_type_stats['day_type'] == 'Weekday']
            
    #         if not weekend_stats.empty and not weekday_stats.empty:
    #             diff_pct = ((weekend_stats['avg_steps'].values[0] - weekday_stats['avg_steps'].values[0]) / 
    #                        weekday_stats['avg_steps'].values[0] * 100)
                
    #             with col_d1:
    #                 st.metric(
    #                     "Weekend Average",
    #                     f"{weekend_stats['avg_steps'].values[0]:,.0f}",
    #                     delta=f"{weekend_stats['success_rate'].values[0]:.0f}% goal success"
    #                 )
                
    #             with col_d2:
    #                 st.metric(
    #                     "Weekday Average",
    #                     f"{weekday_stats['avg_steps'].values[0]:,.0f}",
    #                     delta=f"{weekday_stats['success_rate'].values[0]:.0f}% goal success"
    #                 )
                
    #             with col_d3:
    #                 st.metric(
    #                     "Weekend Effect",
    #                     f"{diff_pct:+.1f}%",
    #                     delta="More active" if diff_pct > 0 else "Less active"
    #                 )
            
    #         st.markdown("---")
            
    #         # Side-by-side comparison chart
    #         comparison_chart = alt.Chart(day_type_stats).mark_bar(size=80).encode(
    #             x=alt.X('day_type:N', title='', axis=alt.Axis(labelAngle=0)),
    #             y=alt.Y('avg_steps:Q', title='Average Daily Steps'),
    #             color=alt.Color(
    #                 'day_type:N',
    #                 scale=alt.Scale(domain=['Weekday', 'Weekend'], range=['#3B82F6', '#F59E0B']),
    #                 legend=None
    #             ),
    #             tooltip=[
    #                 alt.Tooltip('day_type:N', title='Type'),
    #                 alt.Tooltip('avg_steps:Q', title='Avg Steps', format=','),
    #                 alt.Tooltip('total_days:Q', title='Days'),
    #                 alt.Tooltip('success_rate:Q', title='Goal Success', format='.1f')
    #             ]
    #         ).properties(height=300)
            
    #         # Add goal line
    #         goal_line = alt.Chart(pd.DataFrame({'y': [daily_target]})).mark_rule(
    #             strokeDash=[5, 5],
    #             color='#6366F1',
    #             size=2
    #         ).encode(y='y:Q')
            
    #         st.altair_chart((comparison_chart + goal_line), use_container_width=True)
            
    #         # Context insights
    #         if not weekend_stats.empty and not weekday_stats.empty:
    #             if diff_pct > 15:
    #                 st.success(f"🎉 **Weekend warrior!** You're significantly more active on weekends (+{diff_pct:.0f}%). Plan weekend adventures to maximize your activity!")
    #             elif diff_pct < -15:
    #                 st.info(f"💼 **Weekday routine works!** You're more active on weekdays (+{abs(diff_pct):.0f}%). Your work routine drives consistent movement.")
    #             else:
    #                 st.info(f"⚖️ **Balanced:** Your weekend and weekday activity levels are similar (±{abs(diff_pct):.0f}%). You maintain consistency throughout the week!")
    
    # st.markdown("---")
    
    st.subheader("🔥 Streak History")
    st.caption("Visualizing all your goal streaks over time. **See what types of days drove your activity!**")

    if not recent_df.empty:
        # Calculate all streaks within the current view period
        # Only use data within the selected lookback period
        view_start = recent_df['date'].min()
        view_end = recent_df['date'].max()
        streak_df = recent_df[(recent_df['date'] >= view_start) & (recent_df['date'] <= view_end)].sort_values('date').copy()
        streak_df['hit_goal'] = streak_df['step_count'] >= daily_target

        # Identify streak periods
        streak_df['streak_group'] = (streak_df['hit_goal'] != streak_df['hit_goal'].shift()).cumsum()

        # Filter only successful streaks and add context
        streaks_detailed = streak_df[streak_df['hit_goal']].groupby('streak_group').agg({
            'date': ['min', 'max', 'count'],
            'is_weekend': 'sum',
            'travel': 'sum'
        }).reset_index()

        streaks_detailed.columns = ['streak_group', 'start_date', 'end_date', 'length', 'weekend_days', 'travel_days']
        streaks_detailed = streaks_detailed[streaks_detailed['length'] > 0].sort_values('start_date')

        # Add context labels
        streaks_detailed['context'] = streaks_detailed.apply(
            lambda row: 'Travel' if row['travel_days'] > row['length'] / 2 
            else 'Weekend' if row['weekend_days'] > row['length'] / 2 
            else 'Mixed', axis=1
        )

        # Format dates to show only date
        streaks_detailed['start_date'] = streaks_detailed['start_date'].dt.date
        streaks_detailed['end_date'] = streaks_detailed['end_date'].dt.date
        
        if len(streaks_detailed) > 0:
            # Top metrics row
            col_m1, col_m2, col_m3 = st.columns(3)
            
            longest_streak = streaks_detailed.loc[streaks_detailed['length'].idxmax()]
            total_streaks = len(streaks_detailed)
            avg_streak_length = streaks_detailed['length'].mean()
            
            # Count context types
            travel_streaks = len(streaks_detailed[streaks_detailed['context'] == 'Travel'])
            weekend_streaks = len(streaks_detailed[streaks_detailed['context'] == 'Weekend'])
            
            with col_m1:
                st.metric("Longest Streak", f"{longest_streak['length']} days")
            
            with col_m2:
                st.metric("Avg Streak", f"{avg_streak_length:.1f} days")
            
            with col_m3:
                dominant_context = "Travel" if travel_streaks > weekend_streaks else "Weekend" if weekend_streaks > travel_streaks else "Mixed"
                st.metric("Streak Driver", dominant_context)
            
            st.markdown("---")
            
            # Timeline visualization with context
            fig_streak = go.Figure()
            
            # Add horizontal bars for each streak with context colors
            for idx, row in streaks_detailed.iterrows():
                # Color by length AND context
                if row['length'] >= 7:
                    color = '#10B981'  # Green for long streaks
                elif row['length'] >= 3:
                    color = '#F59E0B'  # Yellow for medium
                else:
                    color = '#3B82F6'  # Blue for short
                
                # Add pattern indicator for context
                context_label = row['context']
                hover_text = (f"<b>Streak #{idx+1}</b><br>" +
                            f"Length: {row['length']} days<br>" +
                            f"Context: {context_label}<br>" +
                            f"Weekends: {int(row['weekend_days'])}/{row['length']}<br>" +
                            f"Travel: {int(row['travel_days'])}/{row['length']}<br>" +
                            f"Start: {row['start_date']}<br>" +
                            f"End: {row['end_date']}")
                
                fig_streak.add_trace(go.Scatter(
                    x=[row['start_date'], row['end_date']],
                    y=[idx, idx],
                    mode='lines+markers',
                    line=dict(color=color, width=40),  # Even thicker line
                    marker=dict(size=14, color=color),
                    hovertemplate=hover_text + "<extra></extra>",
                    showlegend=False,
                    name=f"Streak {idx+1}"
                ))
            
            fig_streak.update_layout(
                height=max(200, len(streaks_detailed) * 30),
                xaxis_title='Date',
                yaxis_title='',
                yaxis=dict(showticklabels=False),
                hovermode='closest',
                plot_bgcolor='rgba(250,250,250,0.5)',
                margin=dict(l=20, r=20, t=20, b=40)
            )
            
            st.plotly_chart(fig_streak, width='stretch')
            
            # Bottom info with context
            col_leg1, col_leg2 = st.columns([1, 1])
            
            with col_leg1:
                st.markdown("**Streak Legend:**")
                st.markdown("🟢 Green: 7+ days (excellent)  \n🟡 Yellow: 3-6 days (good)  \n🔵 Blue: 1-2 days (starting)")
            
            with col_leg2:
                # Directly show the current streak value from the card above
                if current_streak > 0:
                    st.success(f"🔥 **Active streak: {current_streak} days!**")
                else:
                    st.info(f"💪 **Start a new streak today!**")
            
            # Streak context insights
            st.markdown("---")
            context_insights = []
            
            if travel_streaks > 0:
                context_insights.append(f"✈️ **{travel_streaks} of your streaks** were travel-driven. Exploration fuels your activity!")
            if weekend_streaks > 0:
                context_insights.append(f"🏖️ **{weekend_streaks} of your streaks** were weekend-heavy. Rest days keep you active!")
            
            # Best streak context
            if longest_streak['context'] == 'Travel':
                context_insights.append(f"🌍 Your **longest streak ({longest_streak['length']} days)** happened while traveling!")
            elif longest_streak['context'] == 'Weekend':
                context_insights.append(f"🎉 Your **longest streak ({longest_streak['length']} days)** was weekend-driven!")
            
            if context_insights:
                st.info("\n\n".join([f"{insight}" for insight in context_insights]))
        
        else:
            st.info("No streaks found in this period. Start your first streak today!")

    else:
        st.warning("No data available for streak analysis.")
    
    st.markdown("---")
    st.caption("Track your steps now. Stay active, stay healthy!")

# ============================================================================
# TAB 2: TRAVEL INSIGHTS - Long-term pattern analysis
# ============================================================================
with tab2:
    # Filters for analysis
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        date_range = st.date_input(
            "Analysis Period", 
            [df['date'].min().date(), df['date'].max().date()],
            key='date_range_travel'
        )
    with col_f2:
        analysis_target = st.number_input(
            "Daily Step Goal", 
            value=10000, 
            min_value=1000, 
            step=1000,
            key='target_travel'
        )
    
    filtered_df = df[
        (df['date'].dt.date >= date_range[0]) & 
        (df['date'].dt.date <= date_range[1])
    ]
    
    # Calculate travel metrics
    travel_avg = filtered_df[filtered_df['travel']]['step_count'].mean()
    home_avg = filtered_df[~filtered_df['travel']]['step_count'].mean()
    travel_boost = ((travel_avg - home_avg) / home_avg * 100) if home_avg > 0 and pd.notna(travel_avg) else 0
    
    st.markdown("---")
    st.markdown("### 🌍 How Does Travel Impact My Activity?")
    st.caption(f"Analysis period: {date_range[0]} to {date_range[1]}")
    
    # Key insights - Enhanced metrics as cards
    col_i1, col_i2, col_i3 = st.columns(3, gap="large")
    
    # Metric 1: Travel Success Rate
    with col_i1:
        travel_days_df = filtered_df[filtered_df['travel']]
        travel_goals = len(travel_days_df[travel_days_df['step_count'] >= analysis_target])
        travel_success_rate = (travel_goals / len(travel_days_df) * 100) if len(travel_days_df) > 0 else 0
        
        # Color-code success rate
        if travel_success_rate >= 80:
            card_color = "#10B981"
            bg_color = "#D1FAE5"
        elif travel_success_rate >= 50:
            card_color = "#F59E0B"
            bg_color = "#FEF3C7"
        else:
            card_color = "#EF4444"
            bg_color = "#FEE2E2"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 28px; border-radius: 12px; border-left: 6px solid {card_color}; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>Travel Success Rate</strong></p>
            <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: {card_color};">{travel_success_rate:.0f}%</p>
            <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;"><strong>{travel_goals}</strong> days hit goal</p>
            <p style="margin: 6px 0 0 0; color: #9CA3AF; font-size: 12px;">While traveling</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 2: Most Active Country
    with col_i2:
        top_country = filtered_df.groupby('country')['step_count'].mean().idxmax() if not filtered_df.empty else "N/A"
        top_country_steps = filtered_df.groupby('country')['step_count'].mean().max() if not filtered_df.empty else 0
        
        st.markdown(f"""
        <div style="background-color: #F0F9FF; padding: 28px; border-radius: 12px; border-left: 6px solid #0EA5E9; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>Most Active Country</strong></p>
            <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: #0EA5E9;">{top_country}</p>
            <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;">{top_country_steps:,.0f} avg steps</p>
            <p style="margin: 6px 0 0 0; color: #9CA3AF; font-size: 12px;">Peak activity</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metric 3: Travel Impact
    with col_i3:
        # Color-code travel impact
        if travel_boost > 10:
            impact_color = "#10B981"
            bg_color = "#D1FAE5"
        elif travel_boost > 0:
            impact_color = "#F59E0B"
            bg_color = "#FEF3C7"
        else:
            impact_color = "#EF4444"
            bg_color = "#FEE2E2"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 28px; border-radius: 12px; border-left: 6px solid {impact_color}; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <p style="margin: 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;"><strong>Travel Impact</strong></p>
            <p style="margin: 14px 0 0 0; font-size: 42px; font-weight: 800; color: {impact_color};">{travel_boost:+.0f}%</p>
            <p style="margin: 10px 0 0 0; color: #6B7280; font-size: 13px; line-height: 1.6;">vs home days</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Key insight banner
    st.markdown("---")
    if travel_boost > 30:
        st.success(f"🚀 **Huge travel gains!** You walk {travel_boost:.0f}% more when traveling. Travel really gets you moving!")
    elif travel_boost > 10:
        st.info(f"✈️ **Moderate travel effect**: {travel_boost:.0f}% increase in activity. Travel keeps you active!")
    elif travel_boost > 0:
        st.info(f"🌍 **Slight travel boost**: {travel_boost:.0f}% more active when traveling.")
    else:
        st.warning(f"🏠 **A true homebuddy**: You're actually {abs(travel_boost):.0f}% more active at home than when traveling.")
    
    st.markdown("---")
    
    # Geographic Map
    st.subheader("🗺️ Where Was I Most Active?")
    st.caption("Countries colored by average daily steps | Darker red = Higher activity")
    
    map_data = filtered_df[filtered_df['step_count'].notna()].copy()
    
    if not map_data.empty:
        # Calculate average steps by country
        country_stats = map_data.groupby(['country', 'country_code']).agg({
            'step_count': ['mean', 'sum', 'count']
        }).reset_index()

        country_stats.columns = ['country', 'country_code', 'avg_steps', 'total_steps', 'days_count']
        country_stats['avg_steps'] = country_stats['avg_steps'].round(0)

        # Create choropleth map
        fig_map = px.choropleth(
            country_stats,
            locations='country_code',
            locationmode='ISO-3',
            color='avg_steps',
            hover_name='country',
            hover_data={
                'country_code': False,
                'avg_steps': ':,.0f',
                'total_steps': ':,.0f',
                'days_count': True
            },
            color_continuous_scale='Reds',
            labels={
                'avg_steps': 'Avg Daily Steps',
                'total_steps': 'Total Steps',
                'days_count': 'Days Recorded'
            },
            range_color=[country_stats['avg_steps'].min(), country_stats['avg_steps'].max()]
        )

        fig_map.update_layout(
            height=650,
            title='',
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor='#CCCCCC',
                projection_type='natural earth',
                bgcolor='rgb(240, 240, 240)',
                showland=True,
                landcolor='rgb(250, 250, 250)',
                showcountries=True,
                countrycolor='rgb(200, 200, 200)',
                center=dict(lat=48.8566, lon=2.3522),
                projection_scale=0.5,
                lataxis_range=[35, 65],
                lonaxis_range=[-15, 30]
            ),
            coloraxis_colorbar=dict(
                title="Avg Daily Steps",
                thicknessmode="pixels",
                thickness=20,
                lenmode="pixels",
                len=350,
                yanchor="middle",
                y=0.5,
                tickformat=',d'
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='white',
            plot_bgcolor='white'
        )

        # Side-by-side layout for map and bar chart
        col_map, col_bar = st.columns([3, 1], gap="large")

        with col_map:
            st.plotly_chart(fig_map, width='stretch')

        with col_bar:
            st.markdown("#### Top Countries")
            top_countries = country_stats.nlargest(5, 'avg_steps')
            country_chart = alt.Chart(top_countries).mark_bar(size=16).encode(
                y=alt.Y('country:N', title=None, sort='-x'),
                x=alt.X('avg_steps:Q', title='Average Daily Steps'),
                color=alt.Color('avg_steps:Q', scale=alt.Scale(scheme='reds'), legend=None),
                tooltip=[
                    alt.Tooltip('country:N', title='Country'),
                    alt.Tooltip('avg_steps:Q', title='Avg Steps', format=','),
                    alt.Tooltip('days_count:Q', title='Days')
                ]
            ).properties(height=250)
            st.altair_chart(country_chart, width='stretch')
            st.markdown("#### Top Cities")
            city_stats = map_data.groupby('city')['step_count'].agg(['mean', 'count']).reset_index()
            city_stats.columns = ['city', 'avg_steps', 'days_count']
            city_stats = city_stats.sort_values('avg_steps', ascending=False).head(5)
            city_chart = alt.Chart(city_stats).mark_bar(size=16).encode(
                y=alt.Y('city:N', title=None, sort='-x'),
                x=alt.X('avg_steps:Q', title='Average Daily Steps'),
                color=alt.Color('avg_steps:Q', scale=alt.Scale(scheme='oranges'), legend=None),
                tooltip=[
                    alt.Tooltip('city:N', title='City'),
                    alt.Tooltip('avg_steps:Q', title='Avg Steps', format=','),
                    alt.Tooltip('days_count:Q', title='Days')
                ]
            ).properties(height=250)
            st.altair_chart(city_chart, width='stretch')
    
    else:
        st.warning("No data available for the selected period.")
    
    st.markdown("---")
    
    # Travel vs Home Comparison
    st.subheader("🏠 Travel Days vs Home Days")
    st.caption("Direct comparison of activity levels by location type and day of week")

    travel_comparison_data = filtered_df[filtered_df['step_count'].notna()].copy()

    if not travel_comparison_data.empty:
        # Separate data by travel and home
        travel_data = travel_comparison_data[travel_comparison_data['travel']]['step_count']
        home_data = travel_comparison_data[~travel_comparison_data['travel']]
        
        # Further separate home data into weekends and weekdays
        home_weekend_data = home_data[home_data['is_weekend']]['step_count']
        home_weekday_data = home_data[~home_data['is_weekend']]['step_count']
        
        # Calculate key metrics
        travel_mean = travel_data.mean()
        home_weekend_mean = home_weekend_data.mean()
        home_weekday_mean = home_weekday_data.mean()
        home_mean = home_data['step_count'].mean()
        
        travel_days_count = len(travel_data)
        home_weekend_count = len(home_weekend_data)
        home_weekday_count = len(home_weekday_data)
        home_days_count = len(home_data)
        
        travel_goal_rate = (len(travel_data[travel_data >= analysis_target]) / travel_days_count * 100) if travel_days_count > 0 else 0
        home_weekend_goal_rate = (len(home_weekend_data[home_weekend_data >= analysis_target]) / home_weekend_count * 100) if home_weekend_count > 0 else 0
        home_weekday_goal_rate = (len(home_weekday_data[home_weekday_data >= analysis_target]) / home_weekday_count * 100) if home_weekday_count > 0 else 0
        home_goal_rate = (len(home_data[home_data['step_count'] >= analysis_target]) / home_days_count * 100) if home_days_count > 0 else 0
        
        # # Top metrics row - 4 columns
        # col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        # with col_m1:
        #     st.metric(
        #         "Travel Days",
        #         f"{travel_days_count}",
        #         delta=f"{travel_goal_rate:.0f}% hit goal"
        #     )
        
        # with col_m2:
        #     st.metric(
        #         "Home - Weekdays",
        #         f"{home_weekday_count}",
        #         delta=f"{home_weekday_goal_rate:.0f}% hit goal"
        #     )
        
        # with col_m3:
        #     st.metric(
        #         "Home - Weekends",
        #         f"{home_weekend_count}",
        #         delta=f"{home_weekend_goal_rate:.0f}% hit goal"
        #     )
        
        # with col_m4:
        #     boost_vs_weekday = ((travel_mean - home_weekday_mean) / home_weekday_mean * 100) if home_weekday_mean > 0 else 0
        #     st.metric(
        #         "Travel Boost",
        #         f"{boost_vs_weekday:+.1f}%",
        #         delta="vs home weekdays"
        #     )
        
        st.markdown("---")
        
        # Create comparison data with all categories
        comparison_data = pd.DataFrame({
            'category': ['Travel', 'Home - Weekdays', 'Home - Weekends'],
            'avg_steps': [travel_mean, home_weekday_mean, home_weekend_mean],
            'color': ['#FF6B35', '#3B82F6', '#F59E0B']
        })
        
        bar_chart = alt.Chart(comparison_data).mark_bar(size=100).encode(
            x=alt.X('category:N', title='', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('avg_steps:Q', title='Average Daily Steps'),
            color=alt.Color(
                'category:N',
                scale=alt.Scale(domain=['Travel', 'Home - Weekdays', 'Home - Weekends'], 
                              range=['#FF6B35', '#3B82F6', '#F59E0B']),
                legend=None
            ),
            tooltip=[
                alt.Tooltip('category:N', title='Type'),
                alt.Tooltip('avg_steps:Q', title='Avg Steps', format=',')
            ]
        ).properties(height=350)
        
        # Add target line
        target_line = alt.Chart(pd.DataFrame({'y': [analysis_target]})).mark_rule(
            strokeDash=[5, 5],
            color='red',
            size=2
        ).encode(y='y:Q')
        
        combined_bar = (bar_chart + target_line)
        st.altair_chart(combined_bar, width='stretch')
        
        # Bottom insights in colored box
        insights = []

        boost_vs_weekday = ((travel_mean - home_weekday_mean) / home_weekday_mean * 100) if home_weekday_mean > 0 else 0
        boost_vs_weekend = ((travel_mean - home_weekend_mean) / home_weekend_mean * 100) if home_weekend_mean > 0 else 0

        # Travel vs home weekdays
        if boost_vs_weekday > 20:
            insights.append(f"🚀 Travel significantly boosts your activity by {boost_vs_weekday:.1f}% vs weekdays at home! Traveling really gets you moving.")
        elif boost_vs_weekday > 0:
            insights.append(f"✈️ Travel helps you stay more active, with a {boost_vs_weekday:.1f}% increase compared to weekdays at home.")
        else:
            insights.append(f"🏠 Interestingly, you're {abs(boost_vs_weekday):.1f}% more active during weekdays at home than when traveling.")

        # Travel vs home weekends
        if boost_vs_weekend > 20:
            insights.append(f"🌴 Travel also beats weekends at home by {boost_vs_weekend:.1f}%! Even your rest days can't keep up with your travel activity.")
        elif boost_vs_weekend > 0:
            insights.append(f"📅 Travel days are {boost_vs_weekend:.1f}% more active than weekends at home.")
        else:
            insights.append(f"🛋️ Home weekends are {abs(boost_vs_weekend):.1f}% more active than your travel days.")

        # Display in info box
        if boost_vs_weekday > 20 or boost_vs_weekend > 20:
            st.success("\n\n".join([f"{insight}" for insight in insights]))
        elif boost_vs_weekday > 0 or boost_vs_weekend > 0:
            st.info("\n\n".join([f"{insight}" for insight in insights]))
        else:
            st.warning("\n\n".join([f"{insight}" for insight in insights]))
    
    st.markdown("---")
    
    # Weather Impact
    st.subheader("🌦️ How Does Weather Affect My Activity?")
    st.caption("Distribution of steps across different weather conditions")
    
    weather_data = filtered_df[filtered_df['step_count'].notna() & filtered_df['weather'].notna()]
    
    if not weather_data.empty:
        violin_plot = px.violin(
            weather_data,
            x='weather',
            y='step_count',
            color='weather',
            box=True,
            points='outliers',
            labels={'step_count': 'Daily Steps', 'weather': 'Weather Condition'},
            color_discrete_sequence=['#FF6B35', '#4ECDC4', '#F7B731', '#5F27CD', '#00D2D3', '#FF9FF3']
        )
        
        violin_plot.update_layout(
            height=400,
            showlegend=False,
            xaxis_title='Weather Condition',
            yaxis_title='Daily Steps'
        )
        
        violin_plot.add_hline(
            y=analysis_target,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Goal: {analysis_target:,}",
            annotation_position="right"
        )
        
        st.plotly_chart(violin_plot, width='stretch')
        
        # Weather insights
        weather_stats = weather_data.groupby('weather')['step_count'].agg(['mean', 'count']).reset_index()
        weather_stats = weather_stats.sort_values('mean', ascending=False)
        
        col_w1, col_w2 = st.columns(2)
        
        if len(weather_stats) > 0:
            with col_w1:
                best_weather = weather_stats.iloc[0]
                st.metric(
                    "Best Weather for Activity",
                    best_weather['weather'],
                    f"{best_weather['mean']:,.0f} avg steps",
                    delta_color = 'off',
                    delta_arrow = 'off'
                )
            
            with col_w2:
                if len(weather_stats) > 1:
                    worst_weather = weather_stats.iloc[-1]
                    st.metric(
                        "Least Active Weather",
                        worst_weather['weather'],
                        f"{worst_weather['mean']:,.0f} avg steps",
                        delta_color = 'off',
                        delta_arrow = 'off'
                    )
    else:
        st.warning("No weather data available.")

    st.markdown("---")
    st.caption("Track your steps now. Stay active, stay healthy!")

# ============================================================================
# TAB 3: ABOUT - Design explanation and documentation
# ============================================================================
with tab3:
    st.markdown("""
    ### **About this Project**

    This dashboard is a comprehensive analysis tool for my personal fitness data, designed to answer two fundamental questions:
    1. **Am I maintaining healthy daily habits?** (Short-term tracking)
    2. **How does my lifestyle (based on travel patterns) and environment (such as weather) affect my activity?** (Long-term patterns)
    
    The visualization transforms raw step data into actionable insights through thoughtful design decisions across 
    data processing, structure, visual encoding, and interaction.
                
    The main audience is myself, aiming to gain insights into my steps and how the environment and personal factors influences my activity levels.
    However, it can be extended to anyone interested in personal activity tracking and travel impact analysis.
    
    ---
    
    ### **1. Data**
    
    #### **Source & Collection**
    - **Origin**: Personal fitness tracker data exported from Google Fit
    - **Format**: CSV file with 13 columns and 500+ daily records
    - **Time Period**: June 2023 - October 2025
    - **Geographic Coverage**: 20+ countries across multiple continents
    
    #### **Schema**
    The dataset includes three types of variables:
    - **Temporal**: `date` (daily granularity), plus derived: `day_of_week`, `is_weekend`, `day_type`
    - **Quantitative**: `step_count`, `move_minutes_count`, `distance`, `calories`, `average_speed`, `max_speed`, `min_speed`
    - **Categorical**: `city`, `country`, `country_code`, `weather`, `travel_day`
    
    #### **Data Processing**
    - Date parsing to enable temporal analysis
    - Boolean conversion for `travel_day` flag (string "True" is converted boolean)
    - Derived metrics calculation (streaks, consistency rates, moving averages, success patterns)
    
    #### **Data Quality**
    - For ease of computation, missing data handled as 0 steps for that day
    
    ---
    
    ### **2. Structure and Page Layout*
    
    #### **Navigation**
    The dashboard uses a **tab-based structure** for two main reasons:
    1. Clear distinction between daily step tracking vs. analysis of contextual factors
    2. Users can focus on one analysis mode at a time
    
    #### **Tab Design**
    - **Activity Tab**: Short-term tracking (7-90 days) focused on habit building and goal achievement
    - **Travel Tab**: Long-term analysis (months to years) examining contextual factors
    - **About Tab**: Design documentation and metadata
    
    #### **Layout**
    Each tab follows a consistent vertical flow for maximum clarity:
    1. **Filters:** User inputs (date ranges, goals)
    2. **Key Metrics:** Summary statistics in metric cards for quick overview of data, it is positioned at the top to provide immediate insights before diving into visualizations or if the user just wants a quick peek without exploring charts
    3. **Primary Visualization:** Main chart answering a core question
    4. **Supporting Analysis:** Additional breakdowns and insights for more details
    5. **Interpretation:** Colored insight boxes with motivation and context to guide understanding
    
    ---
    
    ### **3. Visual Representations**
    
    #### **Activity Tab**
    
    **Bar Chart with Moving Average Line**
    - **Purpose**: Show daily step trends and goal achievement
    - **Encoding**: 
      - Position (x-axis) = Date
      - Length (y-axis) = Step count
      - Color = Goal achievement (green/red for above/below goal)
      - Stroke width = Weekend indicator (thick border on weekend days) for more context without clutter
      - Line overlay = 7-day moving average to reveal trends beyond daily step count
    - Bar charts excel at discrete daily comparisons, stroke width adds weekend context without cluttering, and the line chart shows trends that bars alone can't reveal
    
    **Streak Timeline Gantt Chart**
    - **Purpose**: Visualize step goal achievement streaks and their driving factors
    - **Encoding**:
      - Horizontal lines = Streak duration
      - Position = Time (start and end dates of streaks)
      - Color = Streak length category (blue/yellow/green for short/medium/long)
      - Hover details include context breakdown (weekend %, travel %)
    - The Gantt chart timeline view shows temporal patterns effectively, and added context helps explain what enabled each streak
    
    #### **Travel Tab**
    
    **Choropleth Map**
    - **Purpose**: Provide geographic overview of activity by country
    - **Encoding**:
      - Color intensity = Average daily steps (red gradient)
      - Geographic boundaries = Country shapes
      - Zoom focused on Europe (my primary location now)
    - Geographic visualization reveals spatial patterns invisible in tables or charts
                
    **Horizontal Bar Rankings**
    - **Purpose**: Identify top-performing destinations and compare them more clearly
    - **Encoding**:
      - Length = Average steps
      - Sorted descending = Best to worst
      - Color gradient = Reinforces magnitude of differences
    - Bars provide easier comparison between data and shows the specific countries/cities that drive performance
    
    **Bar Chart (Travel vs. Home)**
    - **Purpose**: Direct comparison of activity levels by context
    - **Encoding**:
      - Position = Location and day type (categorical)
      - Length = Average steps
      - Color = Category distinction (orange for travel, blue for home weekdays, yellow for home weekends)
      - Reference line = Goal threshold
    - Bars provide easier comparison between data
    
    **Violin Plot for Weather Impact**
    - **Purpose**: Show full distribution of activity across weather conditions
    - **Encoding**:
      - Width = Probability density at each step count
      - Box plot overlay = Median and quartiles
      - Individual points = Outliers
    - Violin plots reveal distribution shape that box plots miss and allows better appreciation of activity under different weather conditions
    
    ---
    
    ### **4. Color**
    
    #### **Semantics**
    
    **Activity Tab**
    - 🔴 **Red**: Poor performance - signals concern
    - 🟡 **Yellow**: Moderate activity - neutral/warning
    - 🟢 **Green**: Goal achieved - signals positivity
    - 🔵 **Blue**: Neutral color for non-trend metrics
    - ⚫ **Dark borders**: Adds emphasis to weekends and travel days
    
    **Travel Tab**
    - 🟠 **Orange**: Travel days - warmest, more adventurous
    - 🟡 **Yellow**: Home weekends - warm, slightly adventurous 
    - 🔵 **Teal**: Home weekdays - cool, stable     
    - 🔴 **Red gradient**: Map intensity (darker = more active)
    
    #### **Accessibility**
    - Red-green might have issues for colorblindness, but they are spaced apart enough and reinforced with text labels to mitigate confusion
    
    ---
    
    ### **5. Interaction**
    
    #### **Filters**
    - **Date range selectors**: Adjust analysis window dynamically
    - **Goal input**: Personalize target threshold (accounts for changing fitness levels)
    - **Lookback period**: Quick presets (7/14/30/60/90 days) for common use cases
    
    #### **Interactive Charts**
    - **Tooltips**: Hover reveals precise values and contextual data (day of week, weekend status, travel status, city, weather)
    - **Panning/zooming**: Charts allow exploration of dense data
    - **Real-time updates**: Changing filters recalculates all metrics and visualizations in real-time
    
    #### **Insights**
    - **Pattern detection**: Identifies whether weekends or weekdays drive activity
    - **Trend interpretation**: Explains changes with personal context
    
    ---
    
    ### **6. Metadata**
    
    #### **Chart Guidance**
    - **Captions**: Every chart includes explanatory text describing what to look for
    - **Titles**: Descriptive headings frame each section's purpose
    - **Insight boxes**: Automated interpretations guide understanding based on context and motivate action
 
    #### **Statistics**
    - Reference lines (goal thresholds) provide comparison anchors
    - Percentage calculations normalize across different time periods
    - Moving averages smooth daily noise to reveal trends
    - Success rate calculations by day type, weather, travel status
    
    ---
    
    ### **Limitations & Future Work**
    
    **Current Limitations**:
    - Single activity type (steps only, no other activity included)
    - No predictive modeling or forecasting
    - Context limited to weekend/travel (could add holidays, seasons, even injuries or life events)
    - Limited to MY personal data only

    **Possible Enhancements**:
    - Multi-activity support (distinguish walking vs. running vs. cycling)
    - Predictive models ("Will I hit my weekly goal?") based on country to visit, weather API results or current performance
    - AI goal recommendations based on historical trends
    - Additional personal event annotations (vacations, injuries, life events)
    - Upload functionality for others to use the dashboard with their own data
    """)

    st.markdown("---")
    st.caption("Dashboard created for Visual Analytics Class - CentraleSupelec BDMA")