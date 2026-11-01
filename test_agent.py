from backend.agents import run_krishimitra

city = input("Enter city: ")
crop = input("Enter crop: ")
question = input("Ask your question: ")

response = run_krishimitra(
    city=city,
    crop=crop,
    question=question
)

print("\n===== KRISHIMITRA AI =====\n")
print(response)