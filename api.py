import fastapi
from fastapi import FastAPI, UploadFile, File, Query
from pydantic import BaseModel
import uvicorn
import shutil
import os
from typing import Optional
from agentic_ai import agentic_ai_pipeline

class QueryAgent(BaseModel):
    query: str

app= fastapi.FastAPI()
# Directory to save uploaded images
save_dir = "uploaded_images"
os.makedirs(save_dir, exist_ok=True)


def save_form(form):
    save_path = f"uploaded_forms/{form.filename}"
    os.makedirs("uploaded_forms", exist_ok=True)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(form.file, buffer)


@app.get('/')
async def root():
    return {"message":"Welcome to medical agentic ai"}
# @app.post('/formquery')
# def agentic_ai_endpoint(form:fastapi.UploadFile=fastapi.File(...),q: Optional[str] = fastapi.Query(None)):
#     save_form(form)
#     response=agentic_ai_pipeline(q,form.filename)
#     return response



@app.post('/formquery')
def agentic_ai_endpoint(
    form: UploadFile = File(...),
    q: Optional[str] = Query(None)
):
    # Save the uploaded image locally
    file_path = os.path.join(save_dir, form.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(form.file, buffer)

    # Process the saved image using your pipeline
    # response = agentic_ai_pipeline(q, form.filename)
    response = "the form is working"
    return response

class QueryInput(BaseModel):
    q: str

@app.post('/query')
def agentic_ai_query_endpoint(data: QueryInput):
    response = agentic_ai_pipeline(data.q)
    return response['output'][0]['text']

if __name__=='__main__':
    uvicorn.run("api:app", host="0.0.0.0",reload=True)