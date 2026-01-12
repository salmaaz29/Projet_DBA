# test_intent_classification.py

from llm_engine import LLMEngine

def test_intent_classification():
    """Test intent classification with various questions"""
    
    llm = LLMEngine()
    
    test_cases = [
        "How many users are connected?",
        "Why is SELECT COUNT(*) FROM orders slow?",
        "What security risks exist?",
        "Detect anomalies in audit logs",
        "How to backup with RMAN?",
        "Restore table deleted yesterday",
        "Hello, what can you do?",
        "Combien de sessions actives?",
        "Optimise ma requête SQL",
    ]
    
    print("🧪 Testing Intent Classification\n")
    print("-" * 60)
    
    for question in test_cases:
        intent = llm.classify_intent_with_confidence(question)
        print(f"Q: {question}")
        print(f"➜ {intent}\n")
    
    print("-" * 60)

if __name__ == "__main__":
    test_intent_classification()