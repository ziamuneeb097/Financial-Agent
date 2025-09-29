# Financial AI Agent

A conversational AI agent for handling customer payment discussions. The agent loads customer profiles, initiates conversations, checks payment eligibility against predefined policies, and logs interactions with consent awareness.

## What This Does

This is a Python-based chatbot that talks to customers about overdue payments. It checks if customers qualify for payment plans or discounts based on their profile (amount owed, payment history, risk score, etc.). The agent always starts the conversation and explains decisions based on policy rules.

## Features

- Loads customer data from JSON file
- Agent initiates conversations (doesn't wait for customer to speak first)
- Checks eligibility for payment plans and settlement discounts
- Uses actual LLM calls (Claude via OpenRouter) - no fake responses
- Explains why customers qualify or don't qualify
- Escalates to human agents when needed
- Logs conversations only if customer gave consent
- Interactive terminal mode or web UI (Streamlit)

## Customer Personas

The system includes 5 test customers:

**Sarah Mitchell (CUST-001)** - €120 owed, 5 days late, good history, low risk  
**Marco Rossi (CUST-002)** - €350 owed, 20 days late, average history, medium risk  
**Elena Müller (CUST-003)** - €800 owed, 60 days late, poor history, high risk  
**Jean Dubois (CUST-004)** - €2400 owed, 75 days late, poor history, high risk  
**Anna Kowalski (CUST-005)** - €980 owed, 32 days late, average history, medium risk, no logging consent  

## Policy Rules

**Payment Plan Eligibility:**
- Amount must be ≤ €1,000
- Overdue ≤ 30 days
- Payment history must be "good" or "average"
- Risk score must be ≤ 0.65

If eligible, customers get 3-6 monthly installments depending on amount.

**Settlement Discount:**
- Overdue ≤ 15 days
- Payment history must be "good"
- Risk score must be ≤ 0.30
- Discount: 5% off full payment

If not eligible, agent explains why and escalates if needed.

## How It Works

The agent follows a sense-plan-act approach. When a customer says something, the agent:
1. Understands what they're asking (sense)
2. Figures out which tools to use to answer (plan)
3. Calls those tools and responds with facts (act)

Tools are functions like `check_payment_plan_eligibility()` or `get_settlement_discount_details()`. The agent cannot make up payment options - it must use these tools to get information from the policy engine.

## Installation

### Requirements
- Python 3.8 or higher
- OpenRouter API key (get one at https://openrouter.ai/)

### Install Dependencies

use the requirements file:
```bash
pip install -r requirements.txt
```

### Set Your API Key
Set the api key in the .env file
```bash
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Running the Agent

You have two options:

### Option 1: Terminal Mode (Interactive)

```bash
python financial_agent.py
```

**What happens:**
1. Shows list of 5 customers
2. You pick a customer by number (1-5)
3. Agent starts the conversation
4. You type responses
5. Agent replies using actual LLM
6. Conversation saves to `logs/` folder when done

**Sample Session:**

```
✅ Loaded 5 customer personas

Available customers:
1. Sarah Mitchell (CUST-001) - €120.00, 5 days late
2. Marco Rossi (CUST-002) - €350.00, 20 days late
3. Elena Müller (CUST-003) - €800.00, 60 days late
4. Jean Dubois (CUST-004) - €2400.00, 75 days late
5. Anna Kowalski (CUST-005) - €980.00, 32 days late

Select a customer (1-5): 1

============================================================
Selected: Sarah Mitchell (CUST-001)
============================================================

============================================================
Starting conversation with Sarah Mitchell
============================================================

Agent: Hello Sarah, I hope you're doing well. I'm reaching out because 
I see you have an outstanding balance of €120.00 that is 5 days overdue. 
I'd like to help you find a suitable repayment option that works for you. 
Would you be interested in discussing payment options?

Customer: yes what options do i have

Agent: Let me check what payment options are available for your situation. 
Based on your account profile, you qualify for a payment plan because your 
balance is below €1,000, you're only 5 days late, and your payment history 
is good. I can offer you a plan with 3 monthly installments of €40.00 each, 
for a total of €120.00. Would this work for you?

Customer: can i get a discount instead

Agent: Let me check if you qualify for our settlement discount. Yes, you do! 
If you can pay the full amount today, I can offer you a 5% discount. Your 
original amount is €120.00, and with the discount you would pay €114.00, 
saving you €6.00. You qualify because you're only 5 days late, your payment 
history is good, and your risk score is low. Would you like to take advantage 
of this offer?

Customer: exit

👋 Ending conversation...
✅ Conversation saved to logs/conversation_CUST-001_20250929_143022.json
```

Type `exit`, `quit`, `bye`, or `goodbye` to end the conversation.

### Option 2: Web UI (Streamlit)

```bash
streamlit run streamlit_app.py
```

This opens a web interface at http://localhost:8501 where you can:
- Select a customer from dropdown
- See their profile (amount, days late, history, risk)
- Chat in real-time
- Use quick response buttons
- Save conversations

For ease, this app has also been deployed to streamlit cloud:
```
https://financial-agent-test-project.streamlit.app/
```

## Sample Conversations

### Example: Approved Payment Plan (Sarah)

**Agent:** Hello Sarah, I see you have €120.00 outstanding that is 5 days overdue. I'd like to help you find a repayment option.

**Customer:** What are my options?

**Agent:** You qualify for a payment plan with 3 monthly installments of €40.00 each because your balance is below €1,000, you're only 5 days late, and your payment history is good.

**Result:** ✅ Payment plan offered with clear explanation

## How Guardrails Work

The agent can't make things up because:

1. **Tool-based architecture** - Agent cannot access policy rules directly. It must call tools like `check_payment_plan_eligibility()` to get information.

2. **Deterministic policy engine** - All eligibility rules are hard-coded if/else statements. No AI decides policies. For example:
   ```python
   if amount_due > 1000:
       return False, "amount exceeds €1,000"
   ```

3. **Structured tool responses** - Tools return JSON like `{"eligible": true, "reason": "meets criteria"}`. Agent can't invent fields.

4. **System prompt constraints** - Agent is instructed to NEVER invent offers, NEVER guess data, ALWAYS use tools.

5. **Escalation safety net** - If agent is unsure or customer doesn't qualify, it escalates to a human instead of making things up.

## File Structure

```
financial-ai-agent/
├── financial_agent.py           # Main agent code
├── streamlit_app.py             # Web UI
├── customers.json               # Customer data (5 personas)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── .gitignore                   # Files ignored from git
├── logs/                        # Saved conversations (generated)
├──.env
```

## What Gets Logged

When a customer has `consent_to_store_transcript: true`, conversations are saved to `logs/` as JSON files. Each log includes:
- Customer ID and name
- Timestamp for each message
- Complete conversation history
- Retention period

Anna (CUST-005) has `consent: false` so her conversations are NOT saved.

## Framework Used

- **Language:** Python 3.8+
- **LLM API:** OpenRouter (using OpenAI Python SDK)
- **Model:** Openai gpt 4o
- **Function Calling:** OpenAI-compatible tool/function calling API
- **UI:** Streamlit for web interface
- **Testing:** unittest

## AI Assistance

Parts of this code were developed with assistance:
- Initial code structure
- OpenAI SDK integration
- Best practices

The core logic, policy rules, and architectural decisions are human-designed. The guardrail strategy and tool-based approach were specifically implemented to ensure the agent stays within policy constraints.
