from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

llm = ChatOpenAI(model="GPT-4o-mini", temperature=0.7)

prompt_template = PromptTemplate(
    input_variables=["prompt"],
    template="{prompt}"
)

chain = LLMChain(llm=llm, prompt=prompt_template)

def generate_post_langchain(prompt: str, num_variations: int = 1):
    results = []
    for i in range(num_variations):
        print(f"Generating variation {i+1}...")
        res = chain.run(prompt=prompt)
        results.append(res.strip())
    return results