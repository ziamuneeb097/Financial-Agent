import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
api_key=os.getenv("OPENROUTER_API_KEY")


@dataclass
class CustomerProfile:
    id: str
    name: str
    amount_due: float
    days_late: int
    payment_history: str
    risk_score: float
    consent_to_store_transcript: bool
    transcript_retention_days: int


class PolicyEngine:
    @staticmethod
    def check_payment_plan_eligibility(customer: CustomerProfile) -> Tuple[bool, str]:
        reasons = []
        
        if customer.amount_due > 1000:
            reasons.append(f"balance exceeds €1,000 (current: €{customer.amount_due:.2f})")
        
        if customer.days_late > 30:
            reasons.append(f"payment is overdue by more than 30 days (current: {customer.days_late} days)")
        
        if customer.payment_history == 'poor':
            reasons.append("payment history is classified as poor")
        
        if customer.risk_score > 0.65:
            reasons.append(f"risk score is too high (current: {customer.risk_score:.2f})")
        
        if reasons:
            return False, " and ".join(reasons)
        
        return True, "all eligibility criteria are met"
    
    @staticmethod
    def check_immediate_settlement_discount(customer: CustomerProfile) -> Tuple[bool, str]:
        reasons = []
        
        if customer.days_late > 15:
            reasons.append(f"payment is overdue by more than 15 days (current: {customer.days_late} days)")
        
        if customer.payment_history != 'good':
            reasons.append("payment history must be 'good'")
        
        if customer.risk_score > 0.30:
            reasons.append(f"risk score exceeds 0.30 (current: {customer.risk_score:.2f})")
        
        if reasons:
            return False, " and ".join(reasons)
        
        return True, "all criteria for settlement discount are met"
    
    @staticmethod
    def calculate_payment_plan_terms(customer: CustomerProfile) -> Optional[Dict]:
        eligible, _ = PolicyEngine.check_payment_plan_eligibility(customer)
        
        if not eligible:
            return None

        if customer.amount_due <= 300:
            installments = 3
        elif customer.amount_due <= 600:
            installments = 4
        else:
            installments = 6
        
        monthly_payment = customer.amount_due / installments
        
        return {
            "installments": installments,
            "monthly_payment": round(monthly_payment, 2),
            "total_amount": customer.amount_due
        }
    
    @staticmethod
    def calculate_settlement_discount(customer: CustomerProfile) -> Optional[Dict]:
        eligible, _ = PolicyEngine.check_immediate_settlement_discount(customer)
        
        if not eligible:
            return None
        
        discount_rate = 0.05
        discount_amount = customer.amount_due * discount_rate
        final_amount = customer.amount_due - discount_amount
        
        return {
            "original_amount": customer.amount_due,
            "discount_rate": discount_rate * 100,
            "discount_amount": round(discount_amount, 2),
            "final_amount": round(final_amount, 2)
        }


class ToolRegistry:
    def __init__(self, customer: CustomerProfile, policy_engine: PolicyEngine):
        self.customer = customer
        self.policy = policy_engine
        self.tools = {
            "check_payment_plan_eligibility": self.check_payment_plan_eligibility,
            "get_payment_plan_options": self.get_payment_plan_options,
            "check_settlement_discount_eligibility": self.check_settlement_discount_eligibility,
            "get_settlement_discount_details": self.get_settlement_discount_details,
            "escalate_to_human": self.escalate_to_human,
            "log_customer_question": self.log_customer_question
        }
    
    def check_payment_plan_eligibility(self) -> Dict:
        eligible, reason = self.policy.check_payment_plan_eligibility(self.customer)
        return {
            "eligible": eligible,
            "reason": reason,
            "customer_id": self.customer.id
        }
    
    def get_payment_plan_options(self) -> Dict:
        terms = self.policy.calculate_payment_plan_terms(self.customer)
        if terms is None:
            eligible, reason = self.policy.check_payment_plan_eligibility(self.customer)
            return {
                "available": False,
                "reason": f"Not eligible because {reason}"
            }
        
        return {
            "available": True,
            "terms": terms
        }
    
    def check_settlement_discount_eligibility(self) -> Dict:
        eligible, reason = self.policy.check_immediate_settlement_discount(self.customer)
        return {
            "eligible": eligible,
            "reason": reason,
            "customer_id": self.customer.id
        }
    
    def get_settlement_discount_details(self) -> Dict:
        discount = self.policy.calculate_settlement_discount(self.customer)
        if discount is None:
            eligible, reason = self.policy.check_immediate_settlement_discount(self.customer)
            return {
                "available": False,
                "reason": f"Not eligible because {reason}"
            }
        
        return {
            "available": True,
            "discount": discount
        }
    
    def escalate_to_human(self, reason: str) -> Dict:
        return {
            "escalated": True,
            "reason": reason,
            "customer_id": self.customer.id,
            "timestamp": datetime.now().isoformat()
        }
    
    def log_customer_question(self, question: str) -> Dict:
        return {
            "logged": True,
            "question": question,
            "customer_id": self.customer.id
        }


class ConversationLogger:    
    def __init__(self, customer: CustomerProfile):
        self.customer = customer
        self.log = []
    
    def add_message(self, role: str, content: str):
        if self.customer.consent_to_store_transcript:
            self.log.append({
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": content
            })
    
    def save_to_file(self, filename: str):
        if not self.customer.consent_to_store_transcript:
            print(f"⚠️  Conversation not saved: Customer {self.customer.id} has not consented to transcript storage")
            return
        
        log_data = {
            "customer_id": self.customer.id,
            "customer_name": self.customer.name,
            "conversation_date": datetime.now().isoformat(),
            "retention_days": self.customer.transcript_retention_days,
            "messages": self.log
        }
        
        os.makedirs("logs", exist_ok=True)
        filepath = os.path.join("logs", filename)
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"✅ Conversation saved to {filepath}")


class FinancialAgent:
    def __init__(self, customer: CustomerProfile, api_key: str):
        self.customer = customer
        self.policy = PolicyEngine()
        self.tools = ToolRegistry(customer, self.policy)
        self.logger = ConversationLogger(customer)
        self.api_key = api_key
        self.conversation_history = []

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        return f"""You are a professional financial collection agent working for a bank. Your role is to have a respectful, empathetic conversation with customers about their overdue payments.

CUSTOMER PROFILE:
- Name: {self.customer.name}
- Customer ID: {self.customer.id}
- Outstanding Balance: €{self.customer.amount_due:.2f}
- Days Overdue: {self.customer.days_late} days
- Payment History: {self.customer.payment_history}
- Risk Score: {self.customer.risk_score}

CRITICAL RULES (GUARDRAILS):
1. NEVER invent payment options or terms - only use information from tools
2. NEVER make promises outside the defined policies
3. NEVER guess or assume information not provided
4. ALWAYS explain decisions using information from tool results - state the specific reasons from eligibility checks
5. ALWAYS explain why an option is available or not based on the customer's profile
6. If you cannot help (high risk, poor history, high amount), escalate to human
7. Be empathetic and professional at all times
8. Start the conversation yourself - greet the customer by name

AVAILABLE TOOLS:
- check_payment_plan_eligibility: Check if customer qualifies for installment plan
- get_payment_plan_options: Get specific payment plan terms
- check_settlement_discount_eligibility: Check if customer qualifies for immediate payment discount
- get_settlement_discount_details: Get discount details
- escalate_to_human: Transfer to human agent with reason
- log_customer_question: Log questions that need clarification

YOUR APPROACH:
1. SENSE: Understand what the customer is asking or needs
2. PLAN: Determine which tools to use to help them
3. ACT: Use tools to get accurate information, then respond with facts

Begin the conversation by greeting {self.customer.name} and mentioning their outstanding balance of €{self.customer.amount_due:.2f}. Offer to help them find a repayment solution."""
    
    def _get_available_tools_schema(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_payment_plan_eligibility",
                    "description": "Check if the customer is eligible for a payment plan based on their profile",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_payment_plan_options",
                    "description": "Get detailed payment plan terms and options for eligible customers",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_settlement_discount_eligibility",
                    "description": "Check if customer qualifies for immediate settlement discount",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_settlement_discount_details",
                    "description": "Get settlement discount amount and final payment details",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": "Escalate the conversation to a human agent when unable to help",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "The reason for escalation"
                            }
                        },
                        "required": ["reason"]
                    }
                }
            }
        ]
    
    def _call_llm(self, messages: List[Dict], use_tools: bool = True) -> Tuple[str, Optional[List]]:
        try:
            call_params = {
                "extra_headers": {
                    "X-Title": "Financial AI Agent",
                },
                "model": "openai/gpt-4o",
                "messages": messages
            }

            if use_tools:
                call_params["tools"] = self._get_available_tools_schema()
                call_params["tool_choice"] = "auto"
            
            completion = self.client.chat.completions.create(**call_params)
            
            message = completion.choices[0].message
            content = message.content or ""
            tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else None
            
            return content, tool_calls
            
        except Exception as e:
            return f"Error calling LLM: {str(e)}", None
    
    def sense_plan_act(self, user_input: Optional[str] = None) -> str:
        if user_input:
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self.logger.add_message("customer", user_input)

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        agent_response, tool_calls = self._call_llm(messages, use_tools=True)

        if tool_calls:

            self.conversation_history.append({
                "role": "assistant",
                "content": agent_response,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                
                if function_name in self.tools.tools:
                    tool_result = self.tools.tools[function_name](**function_args)

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(tool_result)
                    })

            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            agent_response, _ = self._call_llm(messages, use_tools=False)

        self.conversation_history.append({
            "role": "assistant",
            "content": agent_response
        })
        self.logger.add_message("agent", agent_response)
        
        return agent_response
    
    def start_conversation(self) -> str:
        print(f"\n{'='*60}")
        print(f"Starting conversation with {self.customer.name} ({self.customer.id})")
        print(f"{'='*60}\n")

        initial_message = self.sense_plan_act()
        return initial_message
    
    def save_conversation(self):
        filename = f"conversation_{self.customer.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.logger.save_to_file(filename)


def load_customers(json_file: str = "customers.json") -> List[CustomerProfile]:
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    customers = []
    for cust_data in data['customers']:
        customers.append(CustomerProfile(**cust_data))
    
    return customers


def run_conversation(customer: CustomerProfile, api_key: str, max_turns: int = 10):
    agent = FinancialAgent(customer, api_key)

    agent_msg = agent.start_conversation()
    print(f"Agent: {agent_msg}\n")

    turn_count = 0
    while turn_count < max_turns:
        try:
            user_input = input("Customer: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n⚠️  Conversation interrupted")
            agent.save_conversation()
            print(f"\n{'='*60}\n")
            return True  # Signal to exit
        
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\n👋 Ending conversation...")
            agent.save_conversation()
            print(f"\n{'='*60}\n")
            return True  # Signal to exit
        
        if not user_input:
            continue
        
        print()
        agent_msg = agent.sense_plan_act(user_input)
        print(f"Agent: {agent_msg}\n")

        if "escalate" in agent_msg.lower() or "transfer" in agent_msg.lower():
            print("⚠️  Conversation escalated to human agent")
            break
        
        turn_count += 1

    agent.save_conversation()
    print(f"\n{'='*60}\n")
    return False  # Don't exit, allow new customer selection


def main():
    try:
        customers = load_customers("customers.json")
        print(f"✅ Loaded {len(customers)} customer personas\n")
    except FileNotFoundError:
        print("❌ Error: customers.json not found")
        print("Please ensure customers.json is in the same directory")
        return
    
    # Display customer list
    print("Available customers:")
    for idx, customer in enumerate(customers, 1):
        print(f"{idx}. {customer.name} ({customer.id}) - €{customer.amount_due:.2f}, {customer.days_late} days late")
    
    # Customer selection loop
    while True:
        try:
            selection = input("\nSelect a customer (1-5): ").strip()
            
            if not selection:
                print("Please enter a number between 1 and 5")
                continue
            
            customer_idx = int(selection) - 1
            
            if 0 <= customer_idx < len(customers):
                selected_customer = customers[customer_idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(customers)}")
        
        except ValueError:
            print("Invalid input. Please enter a number")
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Exiting...")
            return
    
    # Run conversation with selected customer
    print(f"\n{'='*60}")
    print(f"Selected: {selected_customer.name} ({selected_customer.id})")
    print(f"{'='*60}\n")
    
    should_exit = run_conversation(selected_customer, api_key, max_turns=10)
    
    # Exit program if user ended conversation with exit command
    if should_exit:
        return


if __name__ == "__main__":
    main()
