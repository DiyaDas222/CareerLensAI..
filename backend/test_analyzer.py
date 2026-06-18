from app import analyze_resume_locally

text = "Experienced software engineer with 5 years building REST APIs in Python, Flask, Docker, AWS. Implemented CI/CD pipelines and automated tests. Improved latency by 30% and led a small team."

print('--- Software Engineer ---')
print(analyze_resume_locally(text, 'Software Engineer'))
print('\n--- Data Scientist ---')
print(analyze_resume_locally(text, 'Data Scientist'))
print('\n--- Frontend Developer ---')
print(analyze_resume_locally(text, 'Frontend Developer'))
