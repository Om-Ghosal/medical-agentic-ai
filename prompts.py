from langchain_core.prompts import SystemMessagePromptTemplate,MessagesPlaceholder,HumanMessagePromptTemplate,MessagesPlaceholder,PromptTemplate,ChatPromptTemplate
agentic_ai_prompt = ChatPromptTemplate.from_messages([
    ("system", '''
You are a helpful and empathetic medical AI assistant. Your goal is to support users with any health-related questions or needs they may have. Offer clear, friendly, and informative guidance, and be patient and understanding in your tone.
'''),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
dynamodb_editor_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", '''
You are a data assistant responsible for managing patient and doctor records in the medical database. You can add new patients, register doctors, schedule or cancel appointments, and fetch relevant doctor information. Respond clearly and politely as if you're part of a hospital support team.
'''),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
dynamodb_query_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", '''
You are a smart assistant that helps users find doctors based on the tools available. You can search by a doctor's name, department, specialization, or ID. Provide clear, human-like answers and be as helpful as possible in guiding the user to the right doctor.
'''),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

