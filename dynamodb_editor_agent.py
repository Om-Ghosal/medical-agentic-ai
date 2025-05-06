import boto3
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain.agents import create_tool_calling_agent, AgentExecutor
from prompts import dynamodb_editor_agent_prompt

class PatientAdmissionData(BaseModel):
    phone_no: str = Field(description="Patient's Phone number")
    name: str = Field(description="Patient's name")
    dob: str = Field(description="Patient's Date of Birth")
    address: str = Field(description="Patient's home address")
    gender: str = Field(description="Patient's gender")
    symptoms: Optional[List[str]] = Field(default=None, description="List of patient's symptoms")
    suggested_doctor: Optional[str] = Field(default=None, description="Suggested doctor of the patient")

class Appointment(BaseModel):
    date: str = Field(description="Date of the appointment (e.g., '2025-05-01')")
    time_slot: str = Field(description="Time slot of the appointment (e.g., 'morning', 'evening')")

class DoctorRegistrationData(BaseModel):
    id: str = Field(description="Doctor's ID")
    doctor_name: str = Field(description="Doctor's full name")
    specialization: str = Field(description="The Doctor specializes in")
    appointments: Optional[List[Appointment]] = Field(default=None, description="List of current ongoing appointments")

class Appointment(BaseModel):
    date: str = Field(description="Date of the appointment")
    name: str = Field(description="Name of the patient")
    phone_no: str = Field(description="Phone number of the patient")
    slot: str = Field(description="Time slot of the appointment (e.g., morning, afternoon)")

class DoctorAppointment(BaseModel):
    id: str = Field(description="ID of the doctor")
    doctor_name: str= Field(description="Name of the doctor")
    specialization: str = Field(default=None, description="Doctor's specialization")
    appointments: List[Appointment] = Field(default_factory=list, description="List of appointments for the doctor")




@tool("patient_admission", args_schema=PatientAdmissionData)
def add_patient(data: PatientAdmissionData):
    """Use this tool to register a new Patient into the Hospital"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')  
    table = dynamodb.Table('Patients')
    
    item = {
        'phone_no': data.phone_no,
        'name': data.name,
        'dob': data.dob,
        'address': data.address,
        'gender': data.gender,
        'discharged': 'no'
    }
    
    if data.symptoms:
        item['symptoms'] = data.symptoms
    if data.suggested_doctor:
        item['suggested_doctor'] = data.suggested_doctor
    
    table.put_item(Item=item)
    return "Patient record added successfully."

@tool("doctor_registration")
def add_doctor(id: str,
    doctor_name: str,
    specialization: str,
    appointments: Optional[List[Appointment]] = None):
    """Use this tool to register Doctor to the hospital database"""
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')  
    table = dynamodb.Table('Doctors')
    item = {
        'id': id,
        'doctor_name': doctor_name,
        'specialization': specialization,
    }

    if appointments:
        # Convert each appointment (likely a Pydantic model) to a dict
        item['appointments'] = [appointment.dict() for appointment in appointments]
    else:
        item['appointments']=[]

    table.put_item(Item=item)
    return f"Doctor {doctor_name} added successfully."

@tool("add_appointment_to_doctor")
def add_doctor_appointment(id,appointment):
    """use this tool to assign appointments to the doctor"""
    dynamodb=boto3.resource('dynamodb',region_name='ap-south-1')
    table=dynamodb.Table("Doctors")

    response = table.get_item(Key={'id': id})
    item = response.get('Item', {'id': id})
    appointments = item.get('appointments', [])

    if type(appointment)==list:
        print(type(appointment))
        appointments.extend(appointment)
    else:
        appointments.append(appointment)
    
    table.update_item(
        Key={'id': id},
        UpdateExpression="SET appointments = :a",
        ExpressionAttributeValues={':a': appointments}
    )
    print(f"appiointment added for {id}")



@tool("dynamodb_editor_agent")
def dynamodb_editor_agent(query):
    """Use this AI Agent to register patients and doctors into the hospital's database and also use this to add doctor's appointments"""
    tools=[add_patient,add_doctor,add_doctor_appointment]
    agent_llm = ChatBedrockConverse(model_id='anthropic.claude-3-sonnet-20240229-v1:0')
    agent = create_tool_calling_agent(agent_llm, tools, dynamodb_editor_agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools,return_intermediate_steps=True,verbose=True)

    output = agent_executor.invoke({"input": query})

    return output