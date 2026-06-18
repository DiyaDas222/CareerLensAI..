from app import generate_ai_feedback

text = "Experienced software engineer with 5 years building REST APIs in Python, Flask, Docker, AWS. Implemented CI/CD pipelines and automated tests. Improved latency by 30% and led a small team."

for role in ['Software Engineer', 'Data Scientist', 'Frontend Developer']:
    print('---', role, '---')
    fb = generate_ai_feedback(text, role)
    print(fb[:400])
    print('\n')
