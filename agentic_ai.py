from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain.agents import create_tool_calling_agent


from langchain.agents import AgentExecutor
from prompts import agentic_ai_prompt
from patientintake_pipeline import patientintake_pipeline
from dynamodb_editor_agent import dynamodb_editor_agent
from dynamodb_query_agent import dynamodb_query_agent
from medical_llm import medical_llm



def agentic_ai_pipeline(query=None,img_path=None):
    tools = [patientintake_pipeline,dynamodb_query_agent,dynamodb_editor_agent,medical_llm]
    agent_llm = ChatBedrockConverse(model_id='anthropic.claude-3-sonnet-20240229-v1:0')

    if query is None:
        query = ''

    if img_path is not None:
        query+=f'''\n\n the form's image is at this path: uploaded_forms/{img_path}'''

    

    agent = create_tool_calling_agent(agent_llm, tools, agentic_ai_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools,return_intermediate_steps=True,verbose=True)

    output = agent_executor.invoke({"input": query,"form_img_path":f'uploaded_forms/{img_path}'})

    return output


