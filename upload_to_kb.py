import streamlit as st
import boto3
import uuid
import os
from botocore.exceptions import NoCredentialsError, ClientError

# AWS Configuration
AWS_REGION = "us-east-1"  # Replace with your AWS region
KNOWLEDGE_BASE_ID = "your-knowledge-base-id"  # Replace with your Knowledge Base ID
DATA_SOURCE_ID = "your-data-source-id"  # Replace with your Data Source ID
S3_BUCKET_NAME = "your-s3-bucket-name"  # Replace with your S3 bucket name
S3_PREFIX = "knowledge-base-docs/"  # Optional: S3 folder prefix

# Initialize AWS clients
bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
bedrock = boto3.client("bedrock", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

def upload_file_to_s3(file, bucket, prefix):
    try:
        file_key = f"{prefix}{file.name}"
        s3_client.upload_fileobj(file, bucket, file_key)
        return file_key
    except (NoCredentialsError, ClientError) as e:
        st.error(f"Failed to upload file to S3: {e}")
        return None

def start_ingestion_job(kb_id, ds_id):
    try:
        response = bedrock.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        return response['ingestionJob']['ingestionJobId']
    except Exception as e:
        st.error(f"Failed to start ingestion job: {e}")
        return None

def query_bedrock_kb(session_id, input_text, kb_id):
    try:
        response = bedrock_agent.retrieve_and_generate(
            input={"text": input_text},
            knowledgeBaseId=kb_id,
            sessionId=session_id,
        )
        return response["output"]["text"]
    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit UI
st.set_page_config(page_title="Amazon Bedrock Knowledge Base Q&A", layout="wide")
st.title("🔍 Amazon Bedrock Knowledge Base Q&A")

# Initialize session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# File upload section
st.header("📂 Upload Documents to Knowledge Base")
uploaded_files = st.file_uploader("Choose files to upload", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Uploading {uploaded_file.name}...")
        file_key = upload_file_to_s3(uploaded_file, S3_BUCKET_NAME, S3_PREFIX)
        if file_key:
            st.success(f"Uploaded {uploaded_file.name} to S3 at {file_key}")
    # Start ingestion job after uploading files
    ingestion_job_id = start_ingestion_job(KNOWLEDGE_BASE_ID, DATA_SOURCE_ID)
    if ingestion_job_id:
        st.success(f"Ingestion job started with ID: {ingestion_job_id}")

# User input section
st.header("💬 Ask a Question")
query = st.text_input("Enter your question:", placeholder="Type your question here...")

if st.button("Ask"):
    if query:
        with st.spinner("Querying Amazon Bedrock..."):
            answer = query_bedrock_kb(
                session_id=st.session_state.session_id,
                input_text=query,
                kb_id=KNOWLEDGE_BASE_ID
            )
            st.markdown("### 📖 Answer")
            st.write(answer)
    else:
        st.warning("Please enter a question to proceed.")
