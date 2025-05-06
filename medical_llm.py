import requests
from langchain_core.tools import tool
from langchain_aws import ChatBedrockConverse
from langchain_core.prompts import SystemMessagePromptTemplate,MessagesPlaceholder,HumanMessagePromptTemplate,MessagesPlaceholder,PromptTemplate,ChatPromptTemplate

url = "http://ec2-3-7-43-79.ap-south-1.compute.amazonaws.com:8080/v1/chat/completions"
template="Instruction:\nYour job is to find possible disease the patient is suffering from based on the symptoms they are suffering from.\nSymptoms:\n"

format_template=ChatPromptTemplate.from_messages([
    ("system", '''
Just format the given text from the user.Don't change the actual text
'''),
    ("human", "{input}"),
])
model='medllama2'
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer demo"
}


@tool("find_possible_diseases_from_symptoms")
def medical_llm(query:str):
    """use this tool to get probable diseases a patient is suffering from depending on the syptoms they are suffering from"""
    data = {
    "model": model,
    "messages": [
        {"role": "user", "content": f"{template}{query}"}
    ]
}
    response = requests.post(url, headers=headers, json=data).json()
    content = response['choices'][0]['message']['content']

    formatted_prompt = format_template.format_messages(input=content)

    llm = ChatBedrockConverse(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
)
    formatted_content= llm.invoke(formatted_prompt)

    # Print the content
    return formatted_content


