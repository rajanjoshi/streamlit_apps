import streamlit as st
import boto3
import uuid
import difflib

# AWS Configuration
AWS_REGION = "us-east-1"  # Replace with your AWS region
S3_BUCKET_V1 = "your-s3-bucket-v1"  # Replace with your S3 bucket for version 1
S3_BUCKET_V2 = "your-s3-bucket-v2"  # Replace with your S3 bucket for version 2
KNOWLEDGE_BASE_ID_V1 = "your-knowledge-base-id-v1"  # Replace with your Knowledge Base ID for version 1
KNOWLEDGE_BASE_ID_V2 = "your-knowledge-base-id-v2"  # Replace with your Knowledge Base ID for version 2
DATA_SOURCE_ID_V1 = "your-data-source-id-v1"  # Replace with your Data Source ID for version 1
DATA_SOURCE_ID_V2 = "your-data-source-id-v2"  # Replace with your Data Source ID for version 2

# Initialize AWS clients
s3_client = boto3.client("s3", region_name=AWS_REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=AWS_REGION)
bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# Streamlit UI
st.title("📄 BRD Version Comparison")

# Upload BRD Version 1
st.header("Upload BRD Version 1")
brd_v1 = st.file_uploader("Choose BRD Version 1", type=["pdf", "docx", "txt"], key="v1")

# Upload BRD Version 2
st.header("Upload BRD Version 2")
brd_v2 = st.file_uploader("Choose BRD Version 2", type=["pdf", "docx", "txt"], key="v2")

# Function to upload file to S3
def upload_to_s3(file, bucket_name):
    try:
        s3_client.upload_fileobj(file, bucket_name, file.name)
        st.success(f"✅ Uploaded `{file.name}` to `{bucket_name}`")
    except Exception as e:
        st.error(f"❌ Failed to upload `{file.name}` to `{bucket_name}`: {e}")

# Upload files to respective S3 buckets
if st.button("Upload Documents"):
    if brd_v1 and brd_v2:
        upload_to_s3(brd_v1, S3_BUCKET_V1)
        upload_to_s3(brd_v2, S3_BUCKET_V2)
    else:
        st.warning("⚠️ Please upload both BRD versions before proceeding.")

# Function to start ingestion job
def start_ingestion_job(kb_id, ds_id):
    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id
        )
        ingestion_job_id = response['ingestionJob']['ingestionJobId']
        st.success(f"✅ Ingestion job started with ID: `{ingestion_job_id}`")
        return ingestion_job_id
    except Exception as e:
        st.error(f"❌ Failed to start ingestion job: {e}")
        return None

# Ingest documents into respective knowledge bases
if st.button("Ingest Documents"):
    if brd_v1 and brd_v2:
        ingestion_job_id_v1 = start_ingestion_job(KNOWLEDGE_BASE_ID_V1, DATA_SOURCE_ID_V1)
        ingestion_job_id_v2 = start_ingestion_job(KNOWLEDGE_BASE_ID_V2, DATA_SOURCE_ID_V2)
    else:
        st.warning("⚠️ Please upload both BRD versions before ingestion.")

# Function to retrieve document content from S3
def get_document_content(bucket_name, file_name):
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        return obj['Body'].read().decode('utf-8')
    except Exception as e:
        st.error(f"❌ Failed to retrieve `{file_name}` from `{bucket_name}`: {e}")
        return ""

# Compare documents to identify amendments
if st.button("Compare Documents"):
    if brd_v1 and brd_v2:
        content_v1 = get_document_content(S3_BUCKET_V1, brd_v1.name)
        content_v2 = get_document_content(S3_BUCKET_V2, brd_v2.name)

        if content_v1 and content_v2:
            diff = difflib.unified_diff(
                content_v1.splitlines(),
                content_v2.splitlines(),
                fromfile='BRD Version 1',
                tofile='BRD Version 2',
                lineterm=''
            )
            st.markdown("### 📝 Amendments from Previous BRD:")
            st.code('\n'.join(diff), language='diff')
        else:
            st.warning("⚠️ Could not retrieve content for comparison.")
    else:
        st.warning("⚠️ Please upload both BRD versions before comparing.")

# Function to query knowledge base
def query_knowledge_base(kb_id, query_text):
    session_id = str(uuid.uuid4())
    try:
        response = bedrock_runtime.retrieve_and_generate(
            input={"text": query_text},
            knowledgeBaseId=kb_id,
            sessionId=session_id,
        )
        return response["output"]["text"]
    except Exception as e:
        return f"❌ An error occurred while querying knowledge base: {e}"

# Query knowledge bases for amendments
if st.button("Query Amendments"):
    if brd_v1 and brd_v2:
        query = "What are the changes from the previous BRD?"

        response_v1 = query_knowledge_base(KNOWLEDGE_BASE_ID_V1, query)
        response_v2 = query_knowledge_base(KNOWLEDGE_BASE_ID_V2, query)

        with st.expander("📘 BRD Version 1 Response"):
            st.markdown(f"```\n{response_v1}\n```")

        with st.expander("📙 BRD Version 2 Response"):
            st.markdown(f"```\n{response_v2}\n```")
    else:
        st.warning("⚠️ Please upload both BRD versions before querying.")
