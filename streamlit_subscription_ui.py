#!/usr/bin/env python3
"""
Streamlit Subscription Management UI
Interface for viewing plans, managing subscriptions, and tracking usage
"""

import streamlit as st
from typing import Dict, Any, Optional
import requests
import json
from datetime import datetime
import pandas as pd

from ui_styles_refactored import apply_theme
from enhanced_components_refactored import (
    enhanced_button,
    enhanced_card,
    enhanced_progress_indicator,
    enhanced_metric,
    enhanced_tabs
)

class SubscriptionUI:
    """Subscription management interface"""
    
    def __init__(self):
        self.api_base_url = st.session_state.get('api_base_url', 'http://localhost:8000/api')
        self.headers = self._get_auth_headers()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if 'access_token' in st.session_state:
            return {'Authorization': f"Bearer {st.session_state.access_token}"}
        return {}
    
    def _api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
    
    def render_main(self):
        """Render main subscription interface"""
        st.title("💎 Subscription & Billing")
        
        # Apply theme
        apply_theme(st.session_state.get('theme', 'light'))
        
        # Get current subscription
        current_sub = self._api_request('GET', '/subscriptions/current')
        
        # Tab selection
        if current_sub.get('status') == 'none':
            tabs = ["Pricing Plans", "Usage"]
        else:
            tabs = ["Current Plan", "Usage", "Billing", "Payment Methods"]
        
        selected_tab = enhanced_tabs(tabs, key="subscription_tabs")
        
        if selected_tab == "Pricing Plans" or selected_tab == "Current Plan":
            self._render_plans_tab(current_sub)
        elif selected_tab == "Usage":
            self._render_usage_tab()
        elif selected_tab == "Billing":
            self._render_billing_tab()
        elif selected_tab == "Payment Methods":
            self._render_payment_methods_tab()
    
    def _render_plans_tab(self, current_sub: Dict):
        """Render pricing plans"""
        if current_sub.get('status') != 'none':
            # Show current plan info
            st.header("Current Plan")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                with enhanced_card():
                    st.subheader(current_sub['plan']['name'])
                    st.write(current_sub['plan']['description'])
                    
                    if current_sub.get('billing_interval'):
                        st.write(f"**Billing:** {current_sub['billing_interval'].title()}")
                    
                    if current_sub.get('current_period_end'):
                        end_date = datetime.fromisoformat(current_sub['current_period_end'])
                        st.write(f"**Renews:** {end_date.strftime('%B %d, %Y')}")
                    
                    if current_sub.get('canceled_at'):
                        st.warning("⚠️ Subscription will cancel at end of billing period")
            
            with col2:
                if current_sub.get('status') == 'active' and not current_sub.get('canceled_at'):
                    if enhanced_button("Change Plan", "secondary", key="change_plan"):
                        st.session_state.show_plans = True
                    
                    if enhanced_button("Cancel Subscription", "danger", key="cancel_sub"):
                        st.session_state.show_cancel_dialog = True
                elif current_sub.get('canceled_at'):
                    if enhanced_button("Reactivate", "primary", key="reactivate"):
                        self._reactivate_subscription()
            
            with col3:
                if enhanced_button("Manage Billing", "secondary", key="manage_billing"):
                    self._open_customer_portal()
        
        # Show pricing plans
        if current_sub.get('status') == 'none' or st.session_state.get('show_plans', False):
            st.header("Choose Your Plan")
            
            plans = self._api_request('GET', '/subscriptions/plans')
            
            if plans:
                # Billing interval selector
                col1, col2 = st.columns(2)
                with col1:
                    billing_interval = st.radio(
                        "Billing Interval",
                        ["monthly", "yearly"],
                        format_func=lambda x: f"{x.title()} {'(Save 17%)' if x == 'yearly' else ''}",
                        horizontal=True
                    )
                
                # Display plans
                cols = st.columns(len(plans))
                
                for idx, (col, plan) in enumerate(zip(cols, plans)):
                    with col:
                        with st.container():
                            # Plan card styling
                            if plan['tier'] == 'pro':
                                st.markdown('<div class="recommended-badge">RECOMMENDED</div>', unsafe_allow_html=True)
                            
                            with enhanced_card():
                                st.subheader(plan['name'])
                                
                                # Price
                                if billing_interval == 'monthly':
                                    price = plan['monthly_price']
                                    period = '/month'
                                else:
                                    price = plan['yearly_price']
                                    period = '/year'
                                
                                if price == 0:
                                    st.markdown("### Free")
                                else:
                                    st.markdown(f"### ${price:.0f}{period}")
                                
                                st.caption(plan['description'])
                                
                                # Highlights
                                st.markdown("**Includes:**")
                                for highlight in plan['highlights']:
                                    st.markdown(f"✓ {highlight}")
                                
                                # Subscribe button
                                if current_sub.get('plan', {}).get('tier') == plan['tier']:
                                    st.info("Current Plan")
                                else:
                                    button_type = "primary" if plan['tier'] == 'pro' else "secondary"
                                    if enhanced_button(
                                        "Get Started" if price == 0 else "Subscribe",
                                        button_type,
                                        key=f"subscribe_{plan['tier']}"
                                    ):
                                        self._start_subscription(plan['tier'], billing_interval)
                                
                                # View all features
                                with st.expander("View all features"):
                                    self._render_plan_features(plan)
        
        # Cancel dialog
        if st.session_state.get('show_cancel_dialog', False):
            self._render_cancel_dialog()
    
    def _render_usage_tab(self):
        """Render usage tracking tab"""
        st.header("Usage & Limits")
        
        usage_summary = self._api_request('GET', '/subscriptions/usage')
        
        if not usage_summary:
            st.error("Failed to load usage data")
            return
        
        # Plan info
        with enhanced_card():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{usage_summary['plan']['name']} Plan")
                if usage_summary['plan']['billing_interval'] != 'none':
                    st.caption(f"Billed {usage_summary['plan']['billing_interval']}")
            with col2:
                if usage_summary['plan']['tier'] != 'enterprise':
                    if enhanced_button("Upgrade", "primary", key="upgrade_from_usage"):
                        st.session_state.show_plans = True
        
        # Usage metrics
        st.subheader("Current Usage")
        
        # Transcripts
        col1, col2 = st.columns([3, 1])
        with col1:
            self._render_usage_metric(
                "Transcripts",
                usage_summary['usage']['transcripts']['used'],
                usage_summary['usage']['transcripts']['limit'],
                usage_summary['usage']['transcripts']['percentage']
            )
        
        # Minutes
        col1, col2 = st.columns([3, 1])
        with col1:
            self._render_usage_metric(
                "Minutes",
                usage_summary['usage']['minutes']['used'],
                usage_summary['usage']['minutes']['limit'],
                usage_summary['usage']['minutes']['percentage']
            )
        
        # Storage
        col1, col2 = st.columns([3, 1])
        with col1:
            self._render_usage_metric(
                "Storage",
                f"{usage_summary['usage']['storage']['used_gb']:.1f}",
                usage_summary['usage']['storage']['limit_gb'],
                usage_summary['usage']['storage']['percentage'],
                unit="GB"
            )
        
        # API Calls
        col1, col2 = st.columns([3, 1])
        with col1:
            self._render_usage_metric(
                "API Calls",
                usage_summary['usage']['api_calls']['used'],
                usage_summary['usage']['api_calls']['limit'],
                usage_summary['usage']['api_calls']['percentage']
            )
        
        # Features
        st.subheader("Available Features")
        
        features = usage_summary.get('features', {})
        
        feature_cols = st.columns(3)
        feature_names = {
            'api_access': 'API Access',
            'advanced_analytics': 'Advanced Analytics',
            'custom_models': 'Custom Models',
            'priority_support': 'Priority Support',
            'batch_processing': 'Batch Processing',
            'real_time_collab': 'Real-time Collaboration'
        }
        
        for idx, (key, name) in enumerate(feature_names.items()):
            col = feature_cols[idx % 3]
            with col:
                if features.get(key, False):
                    st.success(f"✓ {name}")
                else:
                    st.info(f"✗ {name}")
    
    def _render_usage_metric(self, name: str, used: Any, limit: Any, percentage: float, unit: str = ""):
        """Render a usage metric with progress bar"""
        with enhanced_card():
            st.write(f"**{name}**")
            
            if limit == -1:
                st.write(f"Used: {used} {unit} (Unlimited)")
                enhanced_progress_indicator(0, key=f"progress_{name}")
            else:
                st.write(f"Used: {used} / {limit} {unit}")
                
                # Color based on usage
                if percentage >= 90:
                    color = "🔴"
                elif percentage >= 75:
                    color = "🟡"
                else:
                    color = "🟢"
                
                enhanced_progress_indicator(int(percentage), f"{color} {percentage:.0f}%", key=f"progress_{name}")
    
    def _render_billing_tab(self):
        """Render billing history tab"""
        st.header("Billing History")
        
        # This would fetch from API - for now mock data
        billing_data = [
            {
                'date': '2024-01-01',
                'description': 'Pro Plan - Monthly',
                'amount': '$99.00',
                'status': 'Paid',
                'invoice': 'Download'
            },
            {
                'date': '2023-12-01',
                'description': 'Pro Plan - Monthly',
                'amount': '$99.00',
                'status': 'Paid',
                'invoice': 'Download'
            }
        ]
        
        if billing_data:
            df = pd.DataFrame(billing_data)
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("No billing history available")
        
        # Customer portal button
        if enhanced_button("View in Stripe Portal", "secondary", key="stripe_portal"):
            self._open_customer_portal()
    
    def _render_payment_methods_tab(self):
        """Render payment methods tab"""
        st.header("Payment Methods")
        
        payment_methods = self._api_request('GET', '/subscriptions/payment-methods')
        
        # Add payment method button
        col1, col2 = st.columns([3, 1])
        with col2:
            if enhanced_button("Add Payment Method", "primary", key="add_payment"):
                st.session_state.show_add_payment = True
        
        if payment_methods:
            for pm in payment_methods:
                with enhanced_card():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        card_icon = self._get_card_icon(pm.get('brand', ''))
                        st.write(f"{card_icon} •••• {pm['last_four']}")
                        st.caption(f"Expires {pm['exp_month']}/{pm['exp_year']}")
                    
                    with col2:
                        if pm['is_default']:
                            st.success("Default")
                        else:
                            if st.button("Set Default", key=f"default_{pm['id']}"):
                                self._set_default_payment_method(pm['id'])
                    
                    with col3:
                        if st.button("Remove", key=f"remove_{pm['id']}"):
                            self._remove_payment_method(pm['id'])
        else:
            st.info("No payment methods on file")
        
        # Add payment method dialog
        if st.session_state.get('show_add_payment', False):
            self._render_add_payment_dialog()
    
    def _render_plan_features(self, plan: Dict):
        """Render detailed plan features"""
        features = plan.get('features', {})
        limits = plan.get('limits', {})
        
        st.markdown("**Limits:**")
        for key, value in limits.items():
            display_value = "Unlimited" if value == -1 else str(value)
            st.write(f"- {key.replace('_', ' ').title()}: {display_value}")
        
        if isinstance(features, dict):
            st.markdown("**Features:**")
            for key, value in features.items():
                if isinstance(value, bool):
                    if value:
                        st.write(f"- ✓ {key.replace('_', ' ').title()}")
                else:
                    st.write(f"- {key.replace('_', ' ').title()}: {value}")
    
    def _render_cancel_dialog(self):
        """Render subscription cancellation dialog"""
        with st.container():
            st.markdown("### Cancel Subscription")
            st.warning("Are you sure you want to cancel your subscription?")
            st.info("Your subscription will remain active until the end of the current billing period.")
            
            col1, col2 = st.columns(2)
            with col1:
                if enhanced_button("Cancel Subscription", "danger", key="confirm_cancel"):
                    result = self._api_request('POST', '/subscriptions/cancel')
                    if result:
                        st.success("Subscription canceled. It will remain active until the end of the billing period.")
                        st.session_state.show_cancel_dialog = False
                        st.rerun()
            
            with col2:
                if enhanced_button("Keep Subscription", "primary", key="keep_sub"):
                    st.session_state.show_cancel_dialog = False
                    st.rerun()
    
    def _render_add_payment_dialog(self):
        """Render add payment method dialog"""
        st.markdown("### Add Payment Method")
        st.info("You will be redirected to Stripe to securely add a payment method.")
        
        col1, col2 = st.columns(2)
        with col1:
            if enhanced_button("Continue to Stripe", "primary", key="stripe_add_payment"):
                self._open_customer_portal()
        
        with col2:
            if enhanced_button("Cancel", "secondary", key="cancel_add_payment"):
                st.session_state.show_add_payment = False
                st.rerun()
    
    def _start_subscription(self, tier: str, billing_interval: str):
        """Start subscription checkout"""
        # Create checkout session
        result = self._api_request('POST', '/subscriptions/checkout-session', {
            'plan_tier': tier,
            'billing_interval': billing_interval,
            'success_url': f"{st.session_state.get('app_url', 'http://localhost:8501')}/subscription?success=true",
            'cancel_url': f"{st.session_state.get('app_url', 'http://localhost:8501')}/subscription"
        })
        
        if result and result.get('checkout_url'):
            # Redirect to Stripe checkout
            st.markdown(f'<meta http-equiv="refresh" content="0; url={result["checkout_url"]}">', unsafe_allow_html=True)
    
    def _reactivate_subscription(self):
        """Reactivate canceled subscription"""
        result = self._api_request('PUT', '/subscriptions/update', {
            'cancel_at_period_end': False
        })
        
        if result:
            st.success("Subscription reactivated!")
            st.rerun()
    
    def _open_customer_portal(self):
        """Open Stripe customer portal"""
        result = self._api_request('GET', '/subscriptions/customer-portal', {
            'return_url': st.session_state.get('app_url', 'http://localhost:8501') + '/subscription'
        })
        
        if result and result.get('portal_url'):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={result["portal_url"]}">', unsafe_allow_html=True)
    
    def _set_default_payment_method(self, payment_method_id: int):
        """Set default payment method"""
        # This would call the API
        st.success("Payment method set as default")
        st.rerun()
    
    def _remove_payment_method(self, payment_method_id: int):
        """Remove payment method"""
        result = self._api_request('DELETE', f'/subscriptions/payment-methods/{payment_method_id}')
        
        if result:
            st.success("Payment method removed")
            st.rerun()
    
    def _get_card_icon(self, brand: str) -> str:
        """Get card brand icon"""
        icons = {
            'visa': '💳',
            'mastercard': '💳',
            'amex': '💳',
            'discover': '💳',
            'diners': '💳',
            'jcb': '💳',
            'unionpay': '💳'
        }
        return icons.get(brand.lower(), '💳')

# Initialize and render
def main():
    """Main function to render subscription UI"""
    subscription_ui = SubscriptionUI()
    subscription_ui.render_main()

if __name__ == "__main__":
    main()