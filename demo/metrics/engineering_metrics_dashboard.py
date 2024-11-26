from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from demo.ui.style import (
    create_styled_metric,
    create_styled_line_chart,
    create_styled_tabs,
    create_pie_chart,
    display_pie_chart,
)
from demo.metrics.engineering_metrics import calculate_metrics_from_timescale

def engineering_metrics_dashboard():
    st.title("Engineering Metrics Dashboard")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.today() - timedelta(days=30),
            max_value=datetime.today(),
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.today(),
            min_value=start_date,
            max_value=datetime.today(),
        )

    # Get metrics data
    metrics = calculate_metrics_from_timescale(start_date, end_date)

    # Create tabs for different metric categories
    tabs = create_styled_tabs([
        "Time Metrics",
        "Code Metrics",
        "Quality Metrics",
        "Planning Metrics"
    ])

    # Tab 1: Time Metrics
    with tabs[0]:
        st.subheader("Development Time Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_styled_metric("Coding Time", metrics["coding_time"]["value"], "⌨️")
            create_styled_line_chart(metrics["coding_time"]["trend"], "Time", "Days")
            
        with col2:
            create_styled_metric("PR Pickup Time", metrics["pr_pickup_time"]["value"], "🔍")
            create_styled_line_chart(metrics["pr_pickup_time"]["trend"], "Time", "Hours")
            
        with col3:
            create_styled_metric("PR Review Time", metrics["pr_review_time"]["value"], "👀")
            create_styled_line_chart(metrics["pr_review_time"]["trend"], "Time", "Days")

        st.subheader("Deployment Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_styled_metric("Deploy Time", metrics["deploy_time"]["value"], "🚀")
            create_styled_line_chart(metrics["deploy_time"]["trend"], "Time", "Minutes")
            
        with col2:
            create_styled_metric("Cycle Time", metrics["cycle_time"]["value"], "⏱️")
            create_styled_line_chart(metrics["cycle_time"]["trend"], "Time", "Days")
            
        with col3:
            create_styled_metric("MTTR", metrics["mttr"]["value"], "🔧")
            create_styled_line_chart(metrics["mttr"]["trend"], "Time", "Hours")

    # Tab 2: Code Metrics
    with tabs[1]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_styled_metric("PR Size", metrics["pr_size"]["value"], "📏")
            create_styled_line_chart(metrics["pr_size"]["trend"], "Time", "Lines")
            
        with col2:
            create_styled_metric("Merge Frequency", metrics["merge_frequency"]["value"], "🔄")
            create_styled_line_chart(metrics["merge_frequency"]["trend"], "Time", "Per Day")
            
        with col3:
            create_styled_metric("Deployment Frequency", metrics["deployment_frequency"]["value"], "📦")
            create_styled_line_chart(metrics["deployment_frequency"]["trend"], "Time", "Per Day")

    # Tab 3: Quality Metrics
    with tabs[2]:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_styled_metric("Change Failure Rate", metrics["change_failure_rate"]["value"], "❌")
            create_styled_line_chart(metrics["change_failure_rate"]["trend"], "Time", "Percentage")
            
        with col2:
            create_styled_metric("Rework Rate", metrics["rework_rate"]["value"], "🔄")
            create_styled_line_chart(metrics["rework_rate"]["trend"], "Time", "Percentage")
            
        with col3:
            create_styled_metric("Refactor Rate", metrics["refactor_rate"]["value"], "🔨")
            create_styled_line_chart(metrics["refactor_rate"]["trend"], "Time", "Percentage")

    # Tab 4: Planning Metrics
    with tabs[3]:
        col1, col2 = st.columns(2)
        
        with col1:
            create_styled_metric("Planning Accuracy", metrics["planning_accuracy"]["value"], "📊")
            create_styled_line_chart(metrics["planning_accuracy"]["trend"], "Time", "Percentage")
            
        with col2:
            create_styled_metric("Capacity Accuracy", metrics["capacity_accuracy"]["value"], "⚖️")
            create_styled_line_chart(metrics["capacity_accuracy"]["trend"], "Time", "Percentage") 