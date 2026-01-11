import sys
sys.path.append('src')
from pages.chatbot import generate_intelligent_response

# Test various query optimization questions
test_questions = [
    'comment faire une sauvegarde ?',
    'pourquoi ma requête est lente',
    'optimise cette requête SELECT COUNT(*) FROM test_orders',
    'ma requête est trop lente',
    'comment accélérer ma requête SQL',
    'plan d\'exécution de ma requête',
    'requête performante'
]

for question in test_questions:
    response = generate_intelligent_response(question)
    response_type = 'BACKUP' if 'Stratégie de Sauvegarde' in response else 'QUERY_OPT' if 'Analyse de Performance' in response else 'OTHER'
    print(f'Question: "{question}"')
    print(f'Response type: {response_type}')
    print('---')
