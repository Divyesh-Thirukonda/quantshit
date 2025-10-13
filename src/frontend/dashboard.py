"""
Streamlit dashboard for monitoring arbitrage system.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Any
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.config import get_settings
from src.core.logger import get_logger
from src.data.providers import DataAggregator
from src.platforms.kalshi import KalshiDataProvider
from src.strategies.base import StrategyManager
from src.strategies.cross_platform import CrossPlatformArbitrageStrategy
from src.strategies.correlation import CorrelationArbitrageStrategy
from src.execution.engine import OrderManager
from src.risk.manager import RiskManager

logger = get_logger(__name__)


class ArbitrageDashboard:
    """Main dashboard for arbitrage system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_aggregator = DataAggregator()
        self.strategy_manager = StrategyManager()
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        
        # Add Kalshi provider
        kalshi_provider = KalshiDataProvider()
        self.data_aggregator.add_provider(kalshi_provider)
        
        # Add strategies
        cross_platform_strategy = CrossPlatformArbitrageStrategy()
        correlation_strategy = CorrelationArbitrageStrategy()
        
        self.strategy_manager.add_strategy(cross_platform_strategy)
        self.strategy_manager.add_strategy(correlation_strategy)
    
    def run(self):
        """Run the Streamlit dashboard."""
        st.set_page_config(
            page_title="Arbitrage Trading System",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🎯 Arbitrage Trading System")
        st.markdown("Real-time monitoring and control for prediction market arbitrage")
        
        # Sidebar
        self._render_sidebar()
        
        # Main content
        self._render_main_content()
    
    def _render_sidebar(self):
        """Render sidebar with controls and status."""
        st.sidebar.header("System Control")
        
        # System status
        with st.sidebar.expander("📊 System Status", expanded=True):
            # This would connect to actual system in production
            st.metric("Data Providers", "1", delta="✅ Connected")
            st.metric("Active Strategies", "2", delta="🟢 Running")
            st.metric("Risk Level", "LOW", delta="✅ Normal")
        
        # Strategy controls
        with st.sidebar.expander("⚙️ Strategy Controls"):
            if st.button("🔄 Refresh Data"):
                st.rerun()
            
            if st.button("⏸️ Pause All Strategies"):
                st.info("All strategies paused")
            
            if st.button("▶️ Resume All Strategies"):
                st.info("All strategies resumed")
            
            if st.button("🛑 Emergency Stop"):
                st.error("Emergency stop activated!")
        
        # Settings
        with st.sidebar.expander("⚙️ Settings"):
            st.slider("Refresh Interval (s)", 5, 60, 10)
            st.selectbox("Risk Level", ["Conservative", "Moderate", "Aggressive"])
    
    def _render_main_content(self):
        """Render main dashboard content."""
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🎯 Opportunities", 
            "📈 Positions", 
            "⚠️ Risk", 
            "🔄 Backtesting"
        ])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_opportunities_tab()
        
        with tab3:
            self._render_positions_tab()
        
        with tab4:
            self._render_risk_tab()
        
        with tab5:
            self._render_backtesting_tab()
    
    def _render_overview_tab(self):
        """Render overview tab."""
        st.header("📊 System Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total P&L",
                value="$1,234.56",
                delta="$123.45 (10.1%)"
            )
        
        with col2:
            st.metric(
                label="🎯 Active Opportunities",
                value="5",
                delta="2 new"
            )
        
        with col3:
            st.metric(
                label="📈 Open Positions",
                value="12",
                delta="-1"
            )
        
        with col4:
            st.metric(
                label="⚡ Win Rate",
                value="73.5%",
                delta="5.2%"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💹 P&L Chart")
            # Sample data for demo
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            pnl = [100 + i*10 + (i%3)*20 for i in range(30)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=pnl,
                mode='lines',
                name='Cumulative P&L',
                line=dict(color='green', width=2)
            ))
            fig.update_layout(
                title="Cumulative P&L Over Time",
                xaxis_title="Date",
                yaxis_title="P&L ($)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Strategy Performance")
            # Sample data
            strategies = ['Cross Platform', 'Correlation', 'Market Making']
            performance = [15.2, 8.7, 12.1]
            
            fig = px.bar(
                x=strategies,
                y=performance,
                title="Strategy Returns (%)",
                color=performance,
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        
        # Sample activity data
        activity_data = {
            'Time': ['10:30:15', '10:28:42', '10:25:33', '10:22:18'],
            'Action': ['Trade Executed', 'Opportunity Detected', 'Position Closed', 'Risk Alert'],
            'Market': ['KALSHI_ELECTION', 'KALSHI_SPORTS', 'KALSHI_WEATHER', 'KALSHI_ELECTION'],
            'Details': ['Buy 100 @ 0.65', 'Cross-platform spread 3.2%', 'Sold 150 @ 0.72', 'Exposure limit warning'],
            'Status': ['✅ Success', '🔍 Analyzing', '✅ Success', '⚠️ Warning']
        }
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def _render_opportunities_tab(self):
        """Render opportunities tab."""
        st.header("🎯 Arbitrage Opportunities")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            opportunity_type = st.selectbox(
                "Opportunity Type",
                ["All", "Cross Platform", "Correlation", "Market Making"]
            )
        
        with col2:
            min_profit = st.number_input("Min Profit (%)", min_value=0.0, value=2.0, step=0.1)
        
        with col3:
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.1)
        
        # Opportunities table
        st.subheader("🔍 Current Opportunities")
        
        # Sample opportunities data
        opportunities_data = {
            'ID': ['OPP_001', 'OPP_002', 'OPP_003', 'OPP_004'],
            'Type': ['Cross Platform', 'Correlation', 'Cross Platform', 'Correlation'],
            'Markets': [
                'KALSHI_ELECTION vs POLYMARKET_ELECTION',
                'KALSHI_SPORTS_A vs KALSHI_SPORTS_B',
                'KALSHI_WEATHER vs METACULUS_WEATHER',
                'KALSHI_TECH_A vs KALSHI_TECH_B'
            ],
            'Expected Profit (%)': [3.5, 2.8, 4.1, 1.9],
            'Confidence': [0.85, 0.72, 0.91, 0.65],
            'Required Capital ($)': [1500, 800, 2200, 600],
            'Time Remaining': ['4m 23s', '12m 45s', '1m 12s', '8m 56s'],
            'Action': ['Execute', 'Execute', 'Execute', 'Execute']
        }
        
        df = pd.DataFrame(opportunities_data)
        
        # Apply filters
        if opportunity_type != "All":
            df = df[df['Type'] == opportunity_type]
        
        df = df[df['Expected Profit (%)'] >= min_profit]
        df = df[df['Confidence'] >= min_confidence]
        
        # Display with action buttons
        for idx, row in df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{row['ID']}** - {row['Type']}")
                    st.write(row['Markets'])
                
                with col2:
                    st.metric("Profit", f"{row['Expected Profit (%)']:.1f}%")
                
                with col3:
                    st.metric("Confidence", f"{row['Confidence']:.2f}")
                
                with col4:
                    if st.button(f"Execute {row['ID']}", key=f"exec_{idx}"):
                        st.success(f"Executing {row['ID']}")
                
                st.divider()
    
    def _render_positions_tab(self):
        """Render positions tab."""
        st.header("📈 Current Positions")
        
        # Position summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Positions", "12", delta="2")
        
        with col2:
            st.metric("Total Exposure", "$15,420", delta="$1,200")
        
        with col3:
            st.metric("Unrealized P&L", "$342.18", delta="$45.20")
        
        # Positions table
        st.subheader("📊 Position Details")
        
        # Sample positions data
        positions_data = {
            'Market ID': ['KALSHI_ELECTION_001', 'KALSHI_SPORTS_002', 'KALSHI_WEATHER_003'],
            'Platform': ['Kalshi', 'Kalshi', 'Kalshi'],
            'Side': ['Long', 'Short', 'Long'],
            'Outcome': ['YES', 'NO', 'YES'],
            'Quantity': [150, 200, 100],
            'Avg Price': [0.65, 0.42, 0.58],
            'Current Price': [0.68, 0.39, 0.61],
            'Market Value ($)': [1020, 780, 610],
            'Unrealized P&L ($)': [45.00, 60.00, 30.00],
            'P&L (%)': [4.6, 7.1, 5.2]
        }
        
        df = pd.DataFrame(positions_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Position chart
        st.subheader("📊 Position Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Platform distribution
            platform_counts = df['Platform'].value_counts()
            fig = px.pie(
                values=platform_counts.values,
                names=platform_counts.index,
                title="Positions by Platform"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # P&L distribution
            fig = px.bar(
                x=df['Market ID'],
                y=df['P&L (%)'],
                title="P&L by Position (%)",
                color=df['P&L (%)'],
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_tab(self):
        """Render risk management tab."""
        st.header("⚠️ Risk Management")
        
        # Risk metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Risk Level", "LOW", delta="✅ Normal")
        
        with col2:
            st.metric("VaR (95%)", "$450", delta="$50")
        
        with col3:
            st.metric("Max Drawdown", "3.2%", delta="-0.5%")
        
        with col4:
            st.metric("Daily P&L", "$123.45", delta="$67.89")
        
        # Risk limits
        st.subheader("📊 Risk Limits")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Position limits
            st.write("**Position Limits**")
            
            # Sample data for risk limits
            limits_data = {
                'Metric': ['Total Exposure', 'Platform Exposure', 'Single Position', 'Correlation Exposure'],
                'Current': [15420, 15420, 2200, 3800],
                'Limit': [50000, 25000, 5000, 10000],
                'Usage (%)': [30.8, 61.7, 44.0, 38.0]
            }
            
            df_limits = pd.DataFrame(limits_data)
            
            for idx, row in df_limits.iterrows():
                progress_color = "red" if row['Usage (%)'] > 80 else "orange" if row['Usage (%)'] > 60 else "green"
                
                st.write(f"**{row['Metric']}**: ${row['Current']:,} / ${row['Limit']:,}")
                st.progress(row['Usage (%)'] / 100)
        
        with col2:
            # Risk alerts
            st.write("**Recent Risk Alerts**")
            
            alerts_data = {
                'Time': ['10:25:33', '09:45:12', '09:12:45'],
                'Type': ['Exposure Warning', 'Drawdown Alert', 'Position Limit'],
                'Severity': ['⚠️ Medium', '🔴 High', '⚠️ Medium'],
                'Message': [
                    'Platform exposure at 62%',
                    'Drawdown reached 4.1%',
                    'Position size near limit'
                ]
            }
            
            df_alerts = pd.DataFrame(alerts_data)
            st.dataframe(df_alerts, use_container_width=True, hide_index=True)
        
        # Risk chart
        st.subheader("📈 Risk Metrics Over Time")
        
        # Sample risk history
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        var_95 = [300 + i*5 + (i%5)*10 for i in range(30)]
        drawdown = [abs((i%7)*0.5 - 2) for i in range(30)]
        
        fig = go.Figure()
        
        # VaR
        fig.add_trace(go.Scatter(
            x=dates,
            y=var_95,
            mode='lines',
            name='VaR 95%',
            line=dict(color='red', width=2),
            yaxis='y'
        ))
        
        # Drawdown
        fig.add_trace(go.Scatter(
            x=dates,
            y=drawdown,
            mode='lines',
            name='Drawdown (%)',
            line=dict(color='orange', width=2),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Risk Metrics History",
            xaxis_title="Date",
            yaxis=dict(title="VaR ($)", side="left"),
            yaxis2=dict(title="Drawdown (%)", side="right", overlaying="y"),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_backtesting_tab(self):
        """Render backtesting tab."""
        st.header("🔄 Strategy Backtesting")
        
        # Backtest controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strategy = st.selectbox(
                "Strategy",
                ["Cross Platform Arbitrage", "Correlation Arbitrage", "All Strategies"]
            )
        
        with col2:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        
        with col3:
            end_date = st.date_input("End Date", datetime.now())
        
        if st.button("🚀 Run Backtest"):
            with st.spinner("Running backtest..."):
                # Simulate backtest
                import time
                time.sleep(2)
                st.success("Backtest completed!")
        
        # Backtest results
        st.subheader("📊 Backtest Results")
        
        # Sample backtest results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", "15.4%", delta="2.3%")
        
        with col2:
            st.metric("Sharpe Ratio", "1.85", delta="0.12")
        
        with col3:
            st.metric("Max Drawdown", "3.2%", delta="-0.8%")
        
        with col4:
            st.metric("Win Rate", "73.5%", delta="4.1%")
        
        # Equity curve
        st.subheader("📈 Equity Curve")
        
        # Sample equity curve
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        equity = [100000]
        
        for i in range(1, len(dates)):
            # Simulate equity growth with some volatility
            daily_return = 0.001 + (i % 5) * 0.0005 + np.random.normal(0, 0.002)
            equity.append(equity[-1] * (1 + daily_return))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=equity,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Equity Curve",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade log
        st.subheader("📋 Trade Log")
        
        # Sample trade data
        trade_data = {
            'Time': ['2024-01-15 10:30', '2024-01-15 11:45', '2024-01-15 14:20'],
            'Market': ['KALSHI_ELECTION_001', 'KALSHI_SPORTS_002', 'KALSHI_WEATHER_003'],
            'Action': ['BUY 100 @ 0.65', 'SELL 150 @ 0.42', 'BUY 200 @ 0.58'],
            'P&L': ['$45.00', '$67.50', '$32.10'],
            'Strategy': ['Cross Platform', 'Correlation', 'Cross Platform']
        }
        
        df_trades = pd.DataFrame(trade_data)
        st.dataframe(df_trades, use_container_width=True, hide_index=True)


def main():
    """Main function to run the dashboard."""
    dashboard = ArbitrageDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()