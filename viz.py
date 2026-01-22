import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Config
st.set_page_config(page_title="Personal Activity Tracker", layout="wide", initial_sidebar_state="collapsed")
alt.data_transformers.disable_max_rows()

@st.cache_data
def load_data():
    df = pd.read_csv('dataset.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['travel'] = df['travel_day'].astype(str).str.lower() == 'true'
    df['step_count'] = pd.to_numeric(df['step_count'], errors='coerce')
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce')
    return df

df = load_data()

# Utility functions for derived metrics
def calculate_streak(df_sorted, target):
    """Calculate current streak of hitting target"""
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
    """Calculate percentage of days hitting target"""
    valid_days = df_filtered[df_filtered['step_count'].notna()]
    if len(valid_days) == 0:
        return 0
    hit_target = len(valid_days[valid_days['step_count'] >= target])
    return (hit_target / len(valid_days)) * 100

# Immediate tab navigation (no dropdown)
tab1, tab2, tab3 = st.tabs(["📊 Activity", "✈️ Travel", "📝 About"])

# ============================================================================
# TAB 1: FITNESS TRACKER - Daily habit monitoring and goal tracking
# ============================================================================
with tab1:
    st.title("📊 Personal Activity Tracker")
    st.markdown("""
    **Building healthy habits, one step at a time.** Track your daily progress, 
    and stay motivated to hit your goals consistently.

    **(Note that in the absence of enough data, some metrics may not be computable.
    Also, the tracker ideally should default to today, but since data is not up to date,
    you can select the end date manually.)**
    """)
    
    st.markdown("---")
    
    # Quick settings
    col_set1, col_set2, col_set3 = st.columns([2, 2, 1])
    with col_set1:
        lookback_days = st.selectbox("View Period", [7, 14, 30, 60, 90], index=2, key='lookback')
    with col_set2:
        end_date = st.date_input("End Date", df['date'].max().date(), key='end_date_tracker')
    with col_set3:
        daily_target = st.number_input("Daily Goal", value=10000, min_value=1000, step=1000, key='target_tracker')
    
    # Filter data for selected period
    start_date = pd.Timestamp(end_date) - timedelta(days=lookback_days)
    recent_df = df[
        (df['date'] >= start_date) & 
        (df['date'] <= pd.Timestamp(end_date))
    ].copy()
    
    # Calculate key metrics
    current_streak = calculate_streak(recent_df, daily_target)
    consistency_rate = calculate_consistency(recent_df, daily_target)
    avg_steps = recent_df['step_count'].mean() if not recent_df.empty else 0
    total_steps = recent_df['step_count'].sum() if not recent_df.empty else 0
    days_hit_target = len(recent_df[recent_df['step_count'] >= daily_target])
    total_days = len(recent_df[recent_df['step_count'].notna()])
    
    # Progress percentage
    progress_pct = (avg_steps / daily_target * 100) if daily_target > 0 else 0
    
    st.markdown("---")
    st.markdown("### 🎯 Am I Meeting My Daily Step Goal?")
    
    # Display major metrics
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    with col_m1:
        delta_color = "normal" if progress_pct >= 70 else "inverse"
        st.metric(
            "Average Daily Steps", 
            f"{avg_steps:,.0f}", 
            delta=f"{progress_pct:.0f}% of goal"
        )
    
    with col_m2:
        st.metric(
            "🔥 Current Streak", 
            f"{current_streak} days",
            delta="Consecutive goal days"
        )
    
    with col_m3:
        st.metric(
            "Consistency Rate", 
            f"{consistency_rate:.0f}%",
            delta=f"{days_hit_target}/{total_days} days"
        )
    
    with col_m4:
        st.metric(
            "Total Steps", 
            f"{total_steps:,.0f}",
            delta=f"Last {lookback_days} days"
        )
    
    with col_m5:
        # Calculate best day
        if not recent_df.empty:
            best_day = recent_df.loc[recent_df['step_count'].idxmax()]
            st.metric(
                "Best Day", 
                f"{best_day['step_count']:,.0f}",
                delta=best_day['date'].strftime('%b %d')
            )
        else:
            st.metric("Best Day", "N/A")
    
    # Motivational insight
    st.markdown("---")
    if consistency_rate >= 80:
        st.success(f"🌟 **Excellent!** You're hitting your goal {consistency_rate:.0f}% of the time. Keep up the amazing work!")
    elif consistency_rate >= 60:
        st.info(f"💪 **Good progress!** You're at {consistency_rate:.0f}% consistency. A few more active days and you'll be in the excellent range!")
    elif consistency_rate >= 40:
        st.warning(f"📈 **Getting there!** At {consistency_rate:.0f}% consistency. Try to add 1-2 more active days this week!")
    else:
        st.error(f"🎯 **Let's build momentum!** Currently at {consistency_rate:.0f}%. Small improvements each day add up!")
    
    st.markdown("---")
    
    # Daily trend chart with moving average
    st.subheader("📈 Daily Activity Trends")
    st.caption(f"Your steps over the last {lookback_days} days | Green bars = Goal achieved, Red bars = Below goal | Blue line = 7-day average trend")
    
    if not recent_df.empty:
        # Create color based on goal achievement
        recent_df['goal_met'] = recent_df['step_count'] >= daily_target
        
        # Calculate 7-day moving average
        recent_df = recent_df.sort_values('date')
        recent_df['moving_avg'] = recent_df['step_count'].rolling(window=7, min_periods=1).mean()
        
        # Bar chart for daily steps
        trend_chart = alt.Chart(recent_df).mark_bar().encode(
            x=alt.X('date:T', title='Date', axis=alt.Axis(format='%b %d')),
            y=alt.Y('step_count:Q', title='Daily Steps'),
            color=alt.condition(
                alt.datum.goal_met,
                alt.value('#10B981'),  # Green - goal met
                alt.value('#EF4444')   # Red - below goal
            ),
            tooltip=[
                alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
                alt.Tooltip('step_count:Q', title='Steps', format=','),
                alt.Tooltip('moving_avg:Q', title='7-Day Avg', format=',.0f'),
                alt.Tooltip('city:N', title='City'),
                alt.Tooltip('weather:N', title='Weather')
            ]
        ).properties(
            height=300
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
        st.altair_chart(combined_trend, use_container_width=True)
        
        # Trend interpretation
        if len(recent_df) >= 14:
            first_week_avg = recent_df.head(7)['step_count'].mean()
            last_week_avg = recent_df.tail(7)['step_count'].mean()
            trend_change = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
            
            if trend_change > 10:
                st.success(f"📈 **Trending up!** Your activity increased by {trend_change:.1f}% compared to the start of this period.")
            elif trend_change < -10:
                st.warning(f"📉 **Trending down**: Activity decreased by {abs(trend_change):.1f}%. Consider what changed!")
            else:
                st.info(f"➡️ **Steady**: Your activity is stable (±{abs(trend_change):.1f}%).")
    else:
        st.warning("No data available for the selected period.")
    
    st.markdown("---")
    
    # Step Distribution Histogram
    st.subheader("📊 Step Distribution")
    st.caption("How often do you hit different step ranges? This shows your typical performance.")

    if not recent_df.empty:
        # Create step bins
        bins = [0, 5000, 10000, 15000, 20000, 25000, 30000, float('inf')]
        labels = ['0-5k', '5k-10k', '10k-15k', '15k-20k', '20k-25k', '25k-30k', '30k+']
        
        hist_data = recent_df[recent_df['step_count'].notna()].copy()
        hist_data['step_range'] = pd.cut(hist_data['step_count'], bins=bins, labels=labels, right=False)
        
        range_counts = hist_data['step_range'].value_counts().reindex(labels, fill_value=0).reset_index()
        range_counts.columns = ['step_range', 'count']
        range_counts['percentage'] = (range_counts['count'] / range_counts['count'].sum() * 100).round(1)
        
        # Create colors based on goal
        range_counts['color'] = range_counts['step_range'].apply(
            lambda x: '#10B981' if '10k-' in x or '15k-' in x or '20k-' in x or '25k-' in x or '30k+' in x
            else '#F59E0B' if '5k-10k' in x
            else '#EF4444'
        )
        
        # Calculate key metrics
        below_goal = range_counts[range_counts['step_range'].isin(['0-5k', '5k-10k'])]['count'].sum()
        at_goal = range_counts[~range_counts['step_range'].isin(['0-5k', '5k-10k'])]['count'].sum()
        total_days_hist = range_counts['count'].sum()
        goal_pct = (at_goal / total_days_hist * 100) if total_days_hist > 0 else 0
        
        # Top metrics row
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            most_common = range_counts.loc[range_counts['count'].idxmax()]
            st.metric("Most Common Range", most_common['step_range'], 
                    f"{most_common['percentage']:.0f}% of days")
        
        with col_m2:
            st.metric("Days at/above Goal", f"{at_goal}/{total_days_hist}", 
                    f"{goal_pct:.0f}%")
        
        with col_m3:
            high_performance = range_counts[range_counts['step_range'].isin(['20k-25k', '25k-30k', '30k+'])]['count'].sum()
            st.metric("Exceptional Days", f"{high_performance}", 
                    "20k+ steps")
        
        st.markdown("---")
        
        # Full-width histogram
        hist_chart = alt.Chart(range_counts).mark_bar().encode(
            x=alt.X('step_range:N', title='Step Range', sort=labels),
            y=alt.Y('count:Q', title='Number of Days'),
            color=alt.Color('color:N', scale=None, legend=None),
            tooltip=[
                alt.Tooltip('step_range:N', title='Range'),
                alt.Tooltip('count:Q', title='Days'),
                alt.Tooltip('percentage:Q', title='Percentage', format='.1f')
            ]
        ).properties(height=300)
        
        st.altair_chart(hist_chart, use_container_width=True)
        
        # Bottom insights in yellow box
        low_performance = range_counts[range_counts['step_range'] == '0-5k']['count'].sum()
        lp_pct = (low_performance / total_days_hist * 100) if total_days_hist > 0 else 0
        hp_pct = (high_performance / total_days_hist * 100) if total_days_hist > 0 else 0
        
        # Build insights list
        insights = []
        
        # Insight 1: Most common range
        insights.append(f"**Most typical performance:** Your most common step range is **{most_common['step_range']}**, occurring on {most_common['percentage']:.0f}% of days.")
        
        # Insight 2: Goal achievement or high performance
        if high_performance > 0:
            insights.append(f"**Exceptional days:** You've had **{high_performance} days with 20k+ steps** ({hp_pct:.1f}% of all days), showing strong commitment on your best days!")
        else:
            insights.append(f"**Goal achievement:** You've hit your 10k step goal on **{at_goal} out of {total_days_hist} days** ({goal_pct:.1f}% success rate).")
        
        # Insight 3: Low activity or consistency
        if low_performance > 0:
            insights.append(f"**Low-activity days:** There were **{low_performance} days with fewer than 5k steps** ({lp_pct:.1f}%), which is normal for rest days or busier schedules.")
        else:
            insights.append(f"**Excellent consistency:** You haven't had any days under 5k steps - keep up the great work!")
        
        # Display in warning box (yellow)
        st.warning("\n\n".join([f"• {insight}" for insight in insights]))

    else:
        st.warning("No data available for distribution analysis.")
    
    st.markdown("---")
    
    # Streak Timeline
    st.subheader("🔥 Streak History")
    st.caption("Visualizing all your goal streaks over time.")

    if not recent_df.empty:
        # Calculate all streaks
        streak_df = recent_df.sort_values('date').copy()
        streak_df['hit_goal'] = streak_df['step_count'] >= daily_target
        
        # Identify streak periods
        streak_df['streak_group'] = (streak_df['hit_goal'] != streak_df['hit_goal'].shift()).cumsum()
        
        # Filter only successful streaks
        streaks = streak_df[streak_df['hit_goal']].groupby('streak_group').agg({
            'date': ['min', 'max', 'count']
        }).reset_index()
        streaks.columns = ['streak_group', 'start_date', 'end_date', 'length']
        streaks = streaks[streaks['length'] > 0].sort_values('start_date')
        
        if len(streaks) > 0:
            # Top metrics row
            # st.markdown("#### 🏆 Streak Stats")
            col_m1, col_m2, col_m3 = st.columns(3)
            
            longest_streak = streaks.loc[streaks['length'].idxmax()]
            total_streaks = len(streaks)
            avg_streak_length = streaks['length'].mean()
            
            with col_m1:
                st.metric("Longest Streak", f"{longest_streak['length']} days", 
                        delta=longest_streak['start_date'].strftime('%b %Y'))
            
            with col_m2:
                st.metric("Total Streaks", f"{total_streaks}")
            
            with col_m3:
                st.metric("Avg Streak", f"{avg_streak_length:.1f} days")
            
            st.markdown("---")
            
            # Timeline visualization (full width)
            fig_streak = go.Figure()
            
            # Add horizontal bars for each streak
            for idx, row in streaks.iterrows():
                color = '#10B981' if row['length'] >= 7 else '#F59E0B' if row['length'] >= 3 else '#3B82F6'
                
                fig_streak.add_trace(go.Scatter(
                    x=[row['start_date'], row['end_date']],
                    y=[idx, idx],
                    mode='lines+markers',
                    line=dict(color=color, width=8),
                    marker=dict(size=10, color=color),
                    hovertemplate=f"<b>Streak #{idx+1}</b><br>" +
                                f"Length: {row['length']} days<br>" +
                                f"Start: {row['start_date'].strftime('%b %d, %Y')}<br>" +
                                f"End: {row['end_date'].strftime('%b %d, %Y')}<extra></extra>",
                    showlegend=False
                ))
            
            fig_streak.update_layout(
                height=max(200, len(streaks) * 30),
                xaxis_title='Date',
                yaxis_title='',
                yaxis=dict(showticklabels=False),
                hovermode='closest',
                plot_bgcolor='rgba(250,250,250,0.5)',
                margin=dict(l=20, r=20, t=20, b=40)
            )
            
            st.plotly_chart(fig_streak, use_container_width=True)
            
            # Bottom info row
            col_leg1, col_leg2 = st.columns([1, 1])
            
            with col_leg1:
                st.markdown("**Streak Legend:**")
                st.markdown("🟢 Green: 7+ days (excellent)  \n🟡 Yellow: 3-6 days (good)  \n🔵 Blue: 1-2 days (starting)")
            
            with col_leg2:
                # Current streak status
                current = streaks.iloc[-1]
                if current['end_date'] == recent_df['date'].max():
                    st.success(f"🔥 **Active streak: {current['length']} days!**")
                else:
                    st.info(f"💪 **Start a new streak today!**")
        
        else:
            st.info("No streaks found in this period. Start your first streak today!")

    else:
        st.warning("No data available for streak analysis.")
    
    # st.markdown("---")
    
    # # Monthly Calendar Heatmap
    # st.subheader("📅 Activity Calendar")
    # st.caption("Build consistent habits by tracking daily performance | Red = Low, Yellow = Moderate, Green = Goal achieved")
    
    # heatmap_data = recent_df[recent_df['step_count'].notna()].copy()
    
    # if not heatmap_data.empty:
    #     # Create heatmap data structure
    #     heatmap_data['day'] = heatmap_data['date'].dt.day
    #     heatmap_data['dow'] = heatmap_data['date'].dt.day_name()
        
    #     # Create health-focused colors
    #     day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    #     heatmap_data['dow'] = pd.Categorical(heatmap_data['dow'], categories=day_order, ordered=True)
    #     heatmap_data = heatmap_data.sort_values('dow')
        
    #     # Create custom color scale for health
    #     fig_heat = go.Figure()
        
    #     colors = []
    #     for steps in heatmap_data['step_count']:
    #         if steps < 5000:
    #             colors.append('#EF4444')  # Red - poor
    #         elif steps < daily_target:
    #             colors.append('#F59E0B')  # Yellow/orange - moderate
    #         else:
    #             colors.append('#10B981')  # Green - good
        
        # fig_heat.add_trace(go.Scatter(
        #     x=heatmap_data['day'],
        #     y=heatmap_data['dow'],
        #     mode='markers',
        #     marker=dict(
        #         size=heatmap_data['step_count'] / 800,
        #         color=colors,
        #         line=dict(width=1, color='white'),
        #         sizemode='diameter',
        #         sizemin=8
        #     ),
        #     text=heatmap_data['step_count'].apply(lambda x: f'{x:,.0f} steps'),
        #     hovertemplate='<b>%{y}</b><br>Day %{x}<br>%{text}<extra></extra>',
        #     showlegend=False
        # ))
        
        # fig_heat.update_layout(
        #     height=300,
        #     plot_bgcolor='rgba(250,250,250,0.5)',
        #     xaxis=dict(
        #         title='Day of Month',
        #         tickmode='linear',
        #         tick0=1,
        #         dtick=1,
        #         gridcolor='rgba(200,200,200,0.3)'
        #     ),
        #     yaxis=dict(
        #         title='',
        #         categoryorder='array',
        #         categoryarray=day_order,
        #         gridcolor='rgba(200,200,200,0.3)'
        #     ),
        #     margin=dict(l=80, r=20, t=20, b=40)
        # )
        
        # st.plotly_chart(fig_heat, use_container_width=True)
        
        # Weekly breakdown
    #     st.markdown("---")
    #     st.subheader("📊 Weekly Breakdown")
        
    #     heatmap_data['weekday'] = heatmap_data['date'].dt.day_name()
    #     weekday_avg = heatmap_data.groupby('weekday')['step_count'].mean().reindex(day_order).reset_index()
    #     weekday_avg.columns = ['weekday', 'avg_steps']
        
    #     weekday_chart = alt.Chart(weekday_avg).mark_bar().encode(
    #         x=alt.X('weekday:N', title='Day of Week', sort=day_order),
    #         y=alt.Y('avg_steps:Q', title='Average Steps'),
    #         color=alt.condition(
    #             alt.datum.avg_steps >= daily_target,
    #             alt.value('#10B981'),
    #             alt.value('#F59E0B')
    #         ),
    #         tooltip=[
    #             alt.Tooltip('weekday:N', title='Day'),
    #             alt.Tooltip('avg_steps:Q', title='Avg Steps', format=',')
    #         ]
    #     ).properties(height=250)
        
    #     st.altair_chart(weekday_chart, use_container_width=True)
        
    #     # Insights
    #     best_weekday = weekday_avg.loc[weekday_avg['avg_steps'].idxmax(), 'weekday']
    #     worst_weekday = weekday_avg.loc[weekday_avg['avg_steps'].idxmin(), 'weekday']
        
    #     col_w1, col_w2 = st.columns(2)
    #     with col_w1:
    #         st.metric("Most Active Day", best_weekday, f"{weekday_avg.loc[weekday_avg['weekday'] == best_weekday, 'avg_steps'].values[0]:,.0f} avg")
    #     with col_w2:
    #         st.metric("Least Active Day", worst_weekday, f"{weekday_avg.loc[weekday_avg['weekday'] == worst_weekday, 'avg_steps'].values[0]:,.0f} avg")
    
    # else:
    #     st.warning("No data available for calendar view.")

    st.markdown("---")
    st.caption("Track your steps now. Stay active, stay healthy!")

# ============================================================================
# TAB 2: TRAVEL INSIGHTS - Long-term pattern analysis
# ============================================================================
with tab2:
    st.title("✈️ Travel Impact Tracker")
    st.markdown("""
    **Discovering how the world shapes your movement.** Explore patterns across different countries, 
    understand how travel boosts activity, and see which destinations kept me most active.
    """)
    
    st.markdown("---")
    
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
            "Reference Goal", 
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
    
    # Key insights
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    
    with col_i1:
        st.metric(
            "Travel Boost",
            f"{travel_boost:+.0f}%",
            delta="vs home days"
        )
    
    with col_i2:
        countries_visited = filtered_df['country'].nunique()
        st.metric(
            "Countries Explored",
            f"{countries_visited}",
            delta=f"{filtered_df['city'].nunique()} cities"
        )
    
    with col_i3:
        travel_days = len(filtered_df[filtered_df['travel']])
        total_days = len(filtered_df[filtered_df['step_count'].notna()])
        st.metric(
            "Travel Days",
            f"{travel_days}",
            delta=f"{(travel_days/total_days*100):.0f}% of period"
        )
    
    with col_i4:
        if pd.notna(travel_avg):
            st.metric(
                "Avg Steps Traveling",
                f"{travel_avg:,.0f}",
                delta=f"vs {home_avg:,.0f} at home"
            )
        else:
            st.metric("Avg Steps Traveling", "N/A")
    
    # Key insight banner
    st.markdown("---")
    if travel_boost > 30:
        st.success(f"🚀 **Major travel effect!** You walk {travel_boost:.0f}% more when traveling. Exploration really gets you moving!")
    elif travel_boost > 10:
        st.info(f"✈️ **Moderate travel boost**: {travel_boost:.0f}% increase in activity. Travel days keep you active!")
    elif travel_boost > 0:
        st.info(f"🌍 **Slight travel boost**: {travel_boost:.0f}% more active when traveling.")
    else:
        st.warning(f"🏠 **Home comfort**: You're actually {abs(travel_boost):.0f}% more active at home than when traveling.")
    
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
            title='Average Daily Steps by Country',
            range_color=[country_stats['avg_steps'].min(), country_stats['avg_steps'].max()]
        )
        
        fig_map.update_layout(
            height=500,
            title_font_size=16,
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor='#CCCCCC',
                projection_type='natural earth',
                bgcolor='rgba(243,243,243,0.3)',
                showland=True,
                landcolor='rgb(250, 250, 250)',
                showcountries=True,
                countrycolor='rgb(200, 200, 200)',
                # Zoom in on Europe/France region
                center=dict(lat=48.8566, lon=2.3522),  # Paris coordinates
                projection_scale=0.5,  # Zoom level (higher = more zoomed in)
                lataxis_range=[35, 65],  # Latitude range covering Europe
                lonaxis_range=[-15, 30]  # Longitude range covering Europe
            ),
            coloraxis_colorbar=dict(
                title="Avg Steps",
                thicknessmode="pixels",
                thickness=15,
                lenmode="pixels",
                len=300,
                yanchor="middle",
                y=0.5,
                tickformat=',d'
            ),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig_map, use_container_width=True)

        # Top performing destinations
        st.markdown("---")
        st.subheader("🏆 Top Destinations by Activity")
        
        col_dest1, col_dest2 = st.columns(2)
        
        with col_dest1:
            st.markdown("#### Top Countries")
            top_countries = country_stats.nlargest(5, 'avg_steps')
            
            country_chart = alt.Chart(top_countries).mark_bar().encode(
                y=alt.Y('country:N', title=None, sort='-x'),
                x=alt.X('avg_steps:Q', title='Average Daily Steps'),
                color=alt.Color('avg_steps:Q', scale=alt.Scale(scheme='reds'), legend=None),
                tooltip=[
                    alt.Tooltip('country:N', title='Country'),
                    alt.Tooltip('avg_steps:Q', title='Avg Steps', format=','),
                    alt.Tooltip('days_count:Q', title='Days')
                ]
            ).properties(height=250)
            
            st.altair_chart(country_chart, use_container_width=True)
        
        with col_dest2:
            st.markdown("#### Top Cities")
            city_stats = map_data.groupby('city')['step_count'].agg(['mean', 'count']).reset_index()
            city_stats.columns = ['city', 'avg_steps', 'days_count']
            city_stats = city_stats.sort_values('avg_steps', ascending=False).head(5)
            
            city_chart = alt.Chart(city_stats).mark_bar().encode(
                y=alt.Y('city:N', title=None, sort='-x'),
                x=alt.X('avg_steps:Q', title='Average Daily Steps'),
                color=alt.Color('avg_steps:Q', scale=alt.Scale(scheme='oranges'), legend=None),
                tooltip=[
                    alt.Tooltip('city:N', title='City'),
                    alt.Tooltip('avg_steps:Q', title='Avg Steps', format=','),
                    alt.Tooltip('days_count:Q', title='Days')
                ]
            ).properties(height=250)
            
            st.altair_chart(city_chart, use_container_width=True)
    
    else:
        st.warning("No data available for the selected period.")
    
    st.markdown("---")
    
    # Travel vs Home Comparison
    st.subheader("🏠 Travel Days vs Home Days")
    st.caption("Direct comparison of activity levels by location type")

    # Bar chart comparison
    travel_comparison_data = filtered_df[filtered_df['step_count'].notna()].copy()
    travel_comparison_data['location_type'] = travel_comparison_data['travel'].map({True: 'Travel', False: 'Home'})

    if not travel_comparison_data.empty:
        travel_stats = travel_comparison_data[travel_comparison_data['travel']]['step_count']
        home_stats = travel_comparison_data[~travel_comparison_data['travel']]['step_count']
        
        # Calculate key metrics
        travel_mean = travel_stats.mean()
        home_mean = home_stats.mean()
        boost_pct = ((travel_mean - home_mean) / home_mean * 100) if home_mean > 0 else 0
        
        travel_days_count = len(travel_stats)
        home_days_count = len(home_stats)
        
        travel_goal_rate = (len(travel_stats[travel_stats >= analysis_target]) / travel_days_count * 100) if travel_days_count > 0 else 0
        home_goal_rate = (len(home_stats[home_stats >= analysis_target]) / home_days_count * 100) if home_days_count > 0 else 0
        
        # Top metrics row
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric(
                "Travel Boost",
                f"{boost_pct:+.1f}%",
                delta=f"{travel_mean - home_mean:+,.0f} steps"
            )
        
        with col_m2:
            st.metric(
                "Travel Days",
                f"{travel_days_count}",
                delta=f"{travel_goal_rate:.0f}% hit goal"
            )
        
        with col_m3:
            st.metric(
                "Home Days",
                f"{home_days_count}",
                delta=f"{home_goal_rate:.0f}% hit goal"
            )
        
        st.markdown("---")
        
        # Full-width bar chart
        avg_by_type = travel_comparison_data.groupby('location_type')['step_count'].mean().reset_index()
        avg_by_type.columns = ['location_type', 'avg_steps']
        
        bar_chart = alt.Chart(avg_by_type).mark_bar(size=80).encode(
            x=alt.X('location_type:N', title='', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('avg_steps:Q', title='Average Daily Steps'),
            color=alt.Color(
                'location_type:N',
                scale=alt.Scale(domain=['Travel', 'Home'], range=['#FF6B35', '#4ECDC4']),
                legend=None
            ),
            tooltip=[
                alt.Tooltip('location_type:N', title='Type'),
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
        st.altair_chart(combined_bar, use_container_width=True)
        
        # Bottom insights in colored box
        insights = []
        
        insights.append(f"**Travel days:** You average **{travel_mean:,.0f} steps** when traveling, hitting your goal on {travel_goal_rate:.0f}% of travel days ({travel_days_count} total days).")
        
        insights.append(f"**Home days:** You average **{home_mean:,.0f} steps** at home, hitting your goal on {home_goal_rate:.0f}% of home days ({home_days_count} total days).")
        
        if boost_pct > 20:
            insights.append(f"**Impact:** 🚀 Travel significantly boosts your activity by {boost_pct:.1f}%! Exploration really gets you moving.")
        elif boost_pct > 0:
            insights.append(f"**Impact:** ✈️ Travel helps you stay more active, with a {boost_pct:.1f}% increase in daily steps.")
        else:
            insights.append(f"**Impact:** 🏠 Interestingly, you're {abs(boost_pct):.1f}% more active at home than when traveling.")
        
        # Display in info box
        if boost_pct > 20:
            st.success("\n\n".join([f"• {insight}" for insight in insights]))
        elif boost_pct > 0:
            st.info("\n\n".join([f"• {insight}" for insight in insights]))
        else:
            st.warning("\n\n".join([f"• {insight}" for insight in insights]))
    
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
        
        st.plotly_chart(violin_plot, use_container_width=True)
        
        # Weather insights
        weather_stats = weather_data.groupby('weather')['step_count'].agg(['mean', 'count']).reset_index()
        weather_stats = weather_stats.sort_values('mean', ascending=False)
        
        col_w1, col_w2, col_w3 = st.columns(3)
        
        if len(weather_stats) > 0:
            with col_w1:
                best_weather = weather_stats.iloc[0]
                st.metric(
                    "Best Weather for Activity",
                    best_weather['weather'],
                    f"{best_weather['mean']:,.0f} avg steps"
                )
            
            with col_w2:
                if len(weather_stats) > 1:
                    worst_weather = weather_stats.iloc[-1]
                    st.metric(
                        "Least Active Weather",
                        worst_weather['weather'],
                        f"{worst_weather['mean']:,.0f} avg steps"
                    )
            
            with col_w3:
                weather_impact = ((weather_stats.iloc[0]['mean'] - weather_stats.iloc[-1]['mean']) / weather_stats.iloc[-1]['mean'] * 100) if len(weather_stats) > 1 else 0
                st.metric(
                    "Weather Impact",
                    f"{weather_impact:+.0f}%",
                    "Best vs worst"
                )
    else:
        st.warning("No weather data available.")

    st.markdown("---")
    st.caption("Track your steps now. Stay active, stay healthy!")

# ============================================================================
# TAB 3: ABOUT - Design explanation and documentation
# ============================================================================
with tab3:
    st.title("📝 About This Dashboard")
    
    st.markdown("""
    ### **Project Overview**
    
    This dashboard is a comprehensive analysis tool for my personal fitness data, designed to answer two fundamental questions:
    1. **Am I maintaining healthy daily habits?** (Short-term tracking)
    2. **How does my lifestyle (based on travel patterns) and environment (i.e. weather) affect my activity?** (Long-term patterns)
    
    The visualization transforms raw step data into actionable insights through thoughtful design decisions across 
    data processing, structure, visual encoding, and interaction.
                
    The main audience is myself, aiming to gain insights into my fitness habits and how travel influences my activity levels.
    However, it can be extended to anyone interested in personal activity tracking and travel impact analysis.
    
    ---
    
    ### **1. Data**
    
    #### **Source & Collection**
    - **Origin**: Personal fitness tracker data exported from Google Fit
    - **Format**: CSV file with 13 columns and 500+ daily records
    - **Time Period**: June 2023 - January 2025
    - **Geographic Coverage**: 20+ countries across multiple continents
    
    #### **Schema**
    The dataset includes three types of variables:
    - **Temporal**: `date` (daily granularity)
    - **Quantitative**: `step_count`, `move_minutes_count`, `distance`, `calories`, `average_speed`, `max_speed`, `min_speed`
    - **Categorical**: `city`, `country`, `country_code`, `weather`, `travel_day`
    
    #### **Data Processing**
    - Date parsing to enable temporal analysis
    - Boolean conversion for `travel_day` flag (string "True" → boolean)
    - Numeric coercion with error handling for step counts and distances
    - Derived metrics calculation (streaks, consistency rates, moving averages)
    
    #### **Data Quality**
    - Missing values handled gracefully (excluded from calculations but preserved in dataset)
    
    ---
    
    ### **2. Structure & Organization**
    
    #### **Navigation Architecture**
    The dashboard uses a **tab-based structure** for three reasons:
    1. All sections visible at once without scrolling or menus
    2. Clear distinction between daily tracking vs. analytical exploration
    3. Users can focus on one analysis mode at a time
    
    #### **Tab Design**
    - **📊 Activity Tab**: Short-term tracking (7-90 days) focused on habit building and goal achievement
    - **✈️ Travel Tab**: Long-term analysis (months to years) examining contextual factors
    - **📝 About Tab**: Design documentation and metadata
    
    #### **Information Hierarchy**
    Each tab follows a consistent vertical flow:
    1. **Controls** → User inputs (date ranges, goals)
    2. **Key Metrics** → Summary statistics in metric cards
    3. **Primary Visualization** → Main chart answering the core question
    4. **Supporting Analysis** → Additional breakdowns and insights
    5. **Interpretation** → Colored insight boxes with contextual guidance
    
    ---
    
    ### **3. Visual Representations**
    
    Each visualization was chosen to match the specific analytical task:
    
    #### **Activity Tab Visualizations**
    
    **Bar Chart with Moving Average Line**
    - **Purpose**: Show daily step trends and goal achievement
    - **Encoding**: 
      - Position (x-axis) = Date
      - Length (y-axis) = Step count
      - Color = Goal achievement (green/red binary encoding)
      - Line overlay = 7-day moving average (smooths noise)
    - **Rationale**: Bar charts excel at discrete daily comparisons, while the trend line provides context for overall trajectory
    
    **Histogram with Range Binning**
    - **Purpose**: Reveal typical performance distribution
    - **Encoding**:
      - Categorical bins (0-5k, 5k-10k, etc.)
      - Height = Frequency of days in each range
      - Color gradient (red → yellow → green) maps to health assessment
    - **Rationale**: Histogram reveals distributions and helps identify "normal" vs. exceptional days
    
    **Streak Timeline (Gantt-style)**
    - **Purpose**: Visualize goal achievement streaks over time
    - **Encoding**:
      - Horizontal lines = Streak duration
      - Position = Temporal placement
      - Color = Streak length category (blue/yellow/green for short/medium/long)
    - **Rationale**: Timeline view shows temporal patterns and motivates streak continuation
    
    #### **Travel Tab Visualizations**
    
    **Choropleth Map**
    - **Purpose**: Provide geographic overview of activity by country
    - **Encoding**:
      - Color intensity = Average daily steps (red gradient)
      - Geographic boundaries = Country shapes
      - Zoom focused on Europe (my primary location)
    - **Rationale**: Geographic visualization reveals spatial patterns invisible in tables or charts
    
    **Grouped Bar Chart (Travel vs. Home)**
    - **Purpose**: Direct comparison of activity levels by context
    - **Encoding**:
      - Position = Location type (categorical)
      - Length = Average steps
      - Color = Category distinction (orange for travel, teal for home)
      - Reference line = Goal threshold
    - **Rationale**: Bars provide easier comparison between data
    
    **Violin Plot (Weather Impact)**
    - **Purpose**: Show full distribution of activity across weather conditions
    - **Encoding**:
      - Width = Probability density at each step count
      - Box plot overlay = Median and quartiles
      - Individual points = Outliers
    - **Rationale**: Violin plots reveal distribution shape that box plots miss
    
    **Horizontal Bar Rankings**
    - **Purpose**: Identify top-performing destinations
    - **Encoding**:
      - Length = Average steps
      - Sorted descending = Best to worst
      - Color gradient = Reinforces magnitude
    - **Rationale**: Bars provide easier comparison between data
    
    ---
    
    ### **4. Page Layout**
    
    #### **Layout Principles**
    - **Wide layout mode**: Maximizes horizontal space for chart width
    - **Full-width charts**: Main visualizations span entire width for detail visibility
    - Need to check for responsiveness on smaller screens (tablets)
    
    #### **Information Ordering**
    - **Metrics first**: Key statistics visible without scrolling
    - **Progressive detail**: More complex visualizations appear after summary
    - **Contextual insights**: Colored boxes provide interpretation without overwhelming the data
    
    ---
    
    ### **5. Color Use**
    
    #### **Color Semantics**
    
    **Health-Focused Palette (Activity Tab)**
    - 🔴 **Red**: Poor performance (<5k steps) - signals concern
    - 🟡 **Yellow**: Moderate activity (5k-10k) - neutral/warning
    - 🟢 **Green**: Goal achieved (10k+) - signals positivity
    - 🔵 **Blue**: Trend lines and neutral metrics
    
    **Travel Context Palette (Travel Tab)**
    - 🟠 **Orange**: Travel days - warm, adventurous
    - 🔵 **Teal**: Home days - cool, stable
    - 🔴 **Red gradient**: Map intensity (darker = more active)
    
    #### **Accessibility**
    - Avoided red-green only distinctions
    - High contrast ratios for text readability
    
    ---
    
    ### **6. Interaction**
    
    #### **Filter Controls**
    - **Date range selectors**: Adjust analysis window dynamically
    - **Goal input**: Personalize target threshold (accounts for changing fitness levels)
    - **Lookback period**: Quick presets (7/14/30/60/90 days) for common use cases
    
    #### **Interactive Charts**
    - **Tooltips**: Hover reveals precise values, dates, and contextual data (city, weather)
    - **Panning/zooming**: Charts allow exploration of dense data
    - **Real-time updates**: Changing filters recalculates all metrics and visualizations in real-time
    
    #### **Design Rationale**
    - Minimal interaction required (dashboard is primarily consumptive)
    - Filters placed at top of each tab for easy access
    - Default values set to meaningful ranges (30 days, 10k goal)
    
    ---
    
    ### **7. Metadata & Context**
    
    #### **Embedded Guidance**
    - **Captions**: Every chart includes explanatory text describing what to look for
    - **Titles**: Descriptive headings frame each section's purpose
    - **Insight boxes**: Automated interpretations guide understanding (e.g., "Trending up!")
    
    #### **Statistical Context**
    - Reference lines (goal thresholds) provide comparison anchors
    - Percentage calculations normalize across different time periods
    - Moving averages smooth daily noise to reveal trends
    ---
    
    ### **Technologies Used**
    - **Streamlit**: Web framework enabling rapid prototyping and deployment
    - **Plotly**: Interactive geographic and statistical visualizations
    - **Altair**: Statistical graphics
    - **Pandas**: Data manipulation 
    
    ---
    
    ### **Limitations & Future Work**
    
    **Current Limitations**:
    - Single activity type (steps only, no running/cycling distinction)
    - Weather data limited to simple categories
    - No predictive modeling or forecasting
    
    **Planned Enhancements**:
    - Multi-activity support (distinguish walking vs. running vs. cycling)
    - Predictive models ("Will I hit my weekly goal?")
    - Correlation analysis (weather × location × activity interactions)
    - Export functionality (PDF reports, CSV downloads)
    - AI-powered goal recommendations based on historical performance
    """)

    st.markdown("---")
    st.caption("Dashboard created for Visual Analytics Class - CentraleSupelec BDMA ")