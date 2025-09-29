
import streamlit as st
import os
from financial_agent import (
    CustomerProfile, 
    FinancialAgent, 
    load_customers
)

from dotenv import load_dotenv
load_dotenv()
api_key=os.getenv("OPENROUTER_API_KEY")
# Page config
st.set_page_config(
    page_title="Financial AI Agent",
    page_icon="🏦",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'conversation_started' not in st.session_state:
    st.session_state.conversation_started = False
if 'messages' not in st.session_state:
    st.session_state.messages = []


def initialize_agent(customer: CustomerProfile, api_key: str):
    """Initialize the agent with a customer"""
    st.session_state.agent = FinancialAgent(customer, api_key)
    st.session_state.conversation_started = False
    st.session_state.messages = []


def start_conversation():
    """Start the conversation"""
    if st.session_state.agent and not st.session_state.conversation_started:
        with st.spinner("Agent is initiating conversation..."):
            initial_message = st.session_state.agent.start_conversation()
            st.session_state.messages.append({
                "role": "agent",
                "content": initial_message
            })
            st.session_state.conversation_started = True


def send_message(user_input: str):
    """Send a message and get response"""
    if st.session_state.agent:
        # Add user message
        st.session_state.messages.append({
            "role": "customer",
            "content": user_input
        })
        
        # Get agent response
        with st.spinner("Agent is thinking..."):
            response = st.session_state.agent.sense_plan_act(user_input)
            st.session_state.messages.append({
                "role": "agent",
                "content": response
            })


def display_customer_profile(customer: CustomerProfile):
    """Display customer information"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Amount Due", f"€{customer.amount_due:.2f}")
        st.metric("Days Late", customer.days_late)
    
    with col2:
        st.metric("Payment History", customer.payment_history.title())
        st.metric("Risk Score", f"{customer.risk_score:.2f}")
    
    with col3:
        consent_status = "✅ Yes" if customer.consent_to_store_transcript else "❌ No"
        st.metric("Transcript Consent", consent_status)
        st.metric("Retention Days", customer.transcript_retention_days)


def main():
    st.title("🏦 Financial AI Agent - Collection Assistant")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Load customers
        try:
            customers = load_customers("customers.json")
            st.success(f"✅ Loaded {len(customers)} customers")
        except FileNotFoundError:
            st.error("❌ customers.json not found!")
            st.stop()
        
        # Customer selection
        customer_options = {f"{c.name} ({c.id})": c for c in customers}
        selected_name = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys())
        )
        
        selected_customer = customer_options[selected_name]
        
        # Initialize button
        if st.button("🚀 Initialize Agent", use_container_width=True):
            initialize_agent(selected_customer, api_key)
            st.success(f"Agent initialized for {selected_customer.name}")
            st.rerun()
        
        # Save conversation button
        if st.session_state.agent and st.session_state.conversation_started:
            st.markdown("---")
            if st.button("💾 Save Conversation", use_container_width=True):
                st.session_state.agent.save_conversation()
                st.success("Conversation saved!")
        
        # Reset conversation button
        if st.session_state.conversation_started:
            if st.button("🔄 Reset Conversation", use_container_width=True):
                st.session_state.conversation_started = False
                st.session_state.messages = []
                st.rerun()
        
        # Policy info
        st.markdown("---")
        st.header("📋 Policy Rules")
        
        with st.expander("Payment Plan Eligibility"):
            st.write("**Requirements:**")
            st.write("- Amount ≤ €1,000")
            st.write("- Days late ≤ 30")
            st.write("- History: good or average")
            st.write("- Risk score ≤ 0.65")
            st.write("")
            st.write("**Terms:**")
            st.write("- €0-300: 3 installments")
            st.write("- €301-600: 4 installments")
            st.write("- €601-1000: 6 installments")
        
        with st.expander("Settlement Discount"):
            st.write("**Requirements:**")
            st.write("- Days late ≤ 15")
            st.write("- History: good")
            st.write("- Risk score ≤ 0.30")
            st.write("")
            st.write("**Discount:**")
            st.write("- 5% off full payment")
        
        with st.expander("Escalation Triggers"):
            st.write("**Auto-escalate when:**")
            st.write("- Amount > €2,000")
            st.write("- Risk score > 0.80")
            st.write("- Poor history + high amount")
            st.write("- Complex customer situations")
    
    # Main content area
    if not st.session_state.agent:
        st.info("👈 Please select a customer and initialize the agent from the sidebar")
        
        # Show demo info
        st.markdown("### 📚 About This Agent")
        st.markdown("""
        This Financial AI Agent demonstrates:
        - **Sense → Plan → Act** agentic architecture
        - **Policy-compliant** decision making with guardrails
        - **Tool-based** approach preventing hallucinations
        - **Consent-aware** conversation logging
        - **Proactive** conversation initiation
        
        The agent will:
        1. Load customer profile and context
        2. Initiate conversation (not wait for customer)
        3. Check eligibility using deterministic policy rules
        4. Explain decisions clearly with reasoning
        5. Escalate when unable to help within policies
        """)
        
        st.stop()
    
    # Display customer profile
    st.header(f"Customer: {selected_customer.name}")
    display_customer_profile(selected_customer)
    st.markdown("---")
    
    # Start conversation button
    if not st.session_state.conversation_started:
        st.info("👇 Click below to start the conversation. The agent will greet the customer first.")
        if st.button("▶️ Start Conversation", use_container_width=True, type="primary"):
            start_conversation()
            st.rerun()
        st.stop()
    
    # Display conversation
    st.header("💬 Conversation")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "agent":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(msg["content"])
            else:
                with st.chat_message("user", avatar="👤"):
                    st.write(msg["content"])
    
    # Input area
    st.markdown("---")
    
    # Quick response buttons
    st.markdown("**Quick Responses:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 Payment Plan Info", use_container_width=True):
            send_message("What payment plans are available for me?")
            st.rerun()
    
    with col2:
        if st.button("💰 Settlement Discount", use_container_width=True):
            send_message("Can I get a discount if I pay immediately?")
            st.rerun()
    
    with col3:
        if st.button("❓ Ask Question", use_container_width=True):
            send_message("I have some questions about my options.")
            st.rerun()
    
    with col4:
        if st.button("✅ Interested", use_container_width=True):
            send_message("Yes, I'm interested in hearing about payment options.")
            st.rerun()
    
    st.markdown("")
    
    # Text input with send button
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Your message",
            key="user_input",
            placeholder="Type your message here...",
            label_visibility="collapsed"
        )
    
    with col2:
        send_btn = st.button("Send", use_container_width=True, type="primary")
    
    # Send message
    if send_btn and user_input:
        send_message(user_input)
        st.rerun()
    
    # Additional info at bottom
    st.markdown("---")
    with st.expander("ℹ️ Agent Information"):
        st.markdown("""
        **Guardrails Active:**
        - ✅ Tool-based architecture (no direct policy access)
        - ✅ Deterministic policy engine (no AI in rules)
        - ✅ Structured tool outputs (no ambiguity)
        - ✅ Automatic escalation for edge cases
        - ✅ Consent-aware logging
        
        **Sense → Plan → Act Loop:**
        1. **SENSE:** Understand customer input and context
        2. **PLAN:** Determine which tools to use
        3. **ACT:** Execute tools and provide fact-based response
        """)
    
    # Conversation stats
    if len(st.session_state.messages) > 0:
        agent_msgs = len([m for m in st.session_state.messages if m["role"] == "agent"])
        customer_msgs = len([m for m in st.session_state.messages if m["role"] == "customer"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", len(st.session_state.messages))
        with col2:
            st.metric("Agent Messages", agent_msgs)
        with col3:
            st.metric("Customer Messages", customer_msgs)


if __name__ == "__main__":
    main()
