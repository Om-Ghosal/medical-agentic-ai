import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain.agents import create_tool_calling_agent, AgentExecutor
from prompts import dynamodb_query_agent_prompt

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional


def extract_basic_doctor_info(data):
    """
    Extracts only doctor_name, specialization, and id from the doctor data,
    and removes other fields like appointments.
    """
    allowed_fields = {"doctor_name", "specialization", "id"}
    
    if isinstance(data, list):
        return [{k: v for k, v in item.items() if k in allowed_fields} for item in data]
    elif isinstance(data, dict):
        return {k: v for k, v in data.items() if k in allowed_fields}
    return data

@tool("find_doctor_by_name")
def get_doctors_by_name(name: str):
    """Use this tool to find the doctor in the database using their name."""
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table("Doctors")
    try:
        response = table.scan(
            FilterExpression=Attr('doctor_name').eq(name)
        )
        doctors = response.get('Items', [])
        return extract_basic_doctor_info(doctors)
    except ClientError as e:
        return f"Error: {e}"

@tool("Find_doctor_by_specialization")
def get_doctors_by_specialization(specialization: str):
    """Use this tool to find doctors by their specialization or department."""
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('Doctors')
    try:
        response = table.scan(
            FilterExpression=Attr('specialization').eq(specialization.lower())
        )
        print(response)
        doctors = response.get('Items', [])
        return extract_basic_doctor_info(doctors)
    except ClientError as e:
        return f"Error: {e}"

@tool("Find_doctor_by_id")
def get_doctors_by_id(doctor_id: str):
    """Use this tool to get a doctor's information using their ID."""
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('Doctors')
    try:
        response = table.get_item(Key={'id': doctor_id})
        print(response)
        doctor = response.get('Item')
        return extract_basic_doctor_info(doctor)
    except ClientError as e:
        return f"Error: {e}"

@tool("dynamodb_query_agent")
def dynamodb_query_agent(query:str):
    """Use this AI Agent to Search and Retrieve Information about Doctors from Hospital's Database depending on the doctor's department,specialization,id or there name"""
    tools=[get_doctors_by_name,get_doctors_by_specialization,get_doctors_by_id]
    agent_llm = ChatBedrockConverse(model_id='anthropic.claude-3-sonnet-20240229-v1:0')
    agent = create_tool_calling_agent(agent_llm, tools, dynamodb_query_agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools,return_intermediate_steps=True,verbose=True)

    output = agent_executor.invoke({"input": query})

    return output
    