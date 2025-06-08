import streamlit as st
import boto3
import uuid
import os

# Set AWS region and Knowledge Base ID
AWS_REGION = "us-east-1"  # Replace with your AWS region
KNOWLEDGE_BASE_ID = "your-knowledge-base-id"  # Replace with your Knowledge Base ID

# Initialize the Bedrock Agent Runtime client
bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

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

# User input
query = st.text_input("Enter your question:", placeholder="Type your question here...")

# Submit button
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
