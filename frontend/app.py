import os
import uuid
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RAG 智能文档问答系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def upload_document(self, file, conversation_id: Optional[str] = None) -> Dict:
        files = {"file": (file.name, file.getvalue(), file.type)}
        params = {}
        if conversation_id:
            params["conversation_id"] = conversation_id

        response = requests.post(
            f"{self.base_url}/documents/upload",
            files=files,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def query(self, question: str, conversation_id: Optional[str] = None) -> Dict:
        payload = {"question": question, "conversation_id": conversation_id}
        response = requests.post(f"{self.base_url}/query", json=payload)
        response.raise_for_status()
        return response.json()

    def get_conversation(self, conversation_id: str) -> Dict:
        response = requests.get(f"{self.base_url}/conversations/{conversation_id}")
        response.raise_for_status()
        return response.json()

    def delete_conversation(self, conversation_id: str) -> Dict:
        response = requests.delete(f"{self.base_url}/conversations/{conversation_id}")
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> Dict:
        response = requests.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict:
        response = requests.get(f"{self.base_url.replace('/api/v1', '')}/health")
        response.raise_for_status()
        return response.json()

    def get_supported_formats(self) -> Dict:
        response = requests.get(f"{self.base_url}/documents/formats")
        response.raise_for_status()
        return response.json()


api_client = APIClient()

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []
if "api_connected" not in st.session_state:
    st.session_state.api_connected = False


def check_api_connection() -> bool:
    try:
        api_client.health_check()
        st.session_state.api_connected = True
        return True
    except Exception:
        st.session_state.api_connected = False
        return False


def create_new_conversation():
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.uploaded_documents = []
    st.success("已创建新对话")


def add_message(role: str, content: str, metadata: Optional[Dict] = None):
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
    )


def display_chat_message(role: str, content: str):
    with st.chat_message(role):
        st.markdown(content)


def render_query_details(result: Dict):
    with st.expander("查询详情"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("范围判定", "命中" if result["is_in_scope"] else "未命中")
        with col2:
            st.metric("置信度", f"{result['confidence']:.2%}")

        st.metric("处理耗时", f"{result['processing_time']:.2f} 秒")

        if result["search_results"]:
            st.subheader("检索结果")
            for i, search_result in enumerate(result["search_results"], start=1):
                st.markdown(f"**片段 {i} - 相似度 {search_result['similarity_score']:.2f}**")
                st.text(search_result["content"][:500] + "...")
                st.caption(f"文档: {search_result['metadata'].get('filename', '未知')}")
                if i < len(result["search_results"]):
                    st.divider()


def render_sidebar():
    with st.sidebar:
        st.title("📚 RAG 智能文档问答")

        if check_api_connection():
            st.success("API 连接正常")
        else:
            st.error("API 连接失败")
            st.info("请先启动后端服务")

        st.subheader("对话管理")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("新建对话", use_container_width=True):
                create_new_conversation()
        with col2:
            if st.session_state.conversation_id and st.button("删除对话", use_container_width=True):
                try:
                    api_client.delete_conversation(st.session_state.conversation_id)
                    create_new_conversation()
                except Exception as exc:
                    st.error(f"删除对话失败: {exc}")

        if st.session_state.conversation_id:
            st.caption(f"对话 ID: `{st.session_state.conversation_id[:8]}...`")

        st.subheader("文档上传")
        uploaded_file = st.file_uploader(
            "选择要上传的文档",
            type=["pdf", "docx", "xlsx", "txt", "md", "json", "csv", "jpg", "jpeg", "png"],
        )

        if uploaded_file is not None and st.button("上传文档", use_container_width=True):
            try:
                with st.spinner("正在上传并处理文档..."):
                    result = api_client.upload_document(uploaded_file, st.session_state.conversation_id)

                st.success(f"文档上传成功: {result['filename']}")
                st.info(f"切分块数: {result['chunks_count']}")
                st.session_state.uploaded_documents.append(
                    {
                        "filename": result["filename"],
                        "document_id": result["document_id"],
                        "chunks_count": result["chunks_count"],
                    }
                )
            except Exception as exc:
                st.error(f"文档上传失败: {exc}")

        if st.session_state.uploaded_documents:
            st.subheader("已上传文档")
            for doc in st.session_state.uploaded_documents:
                st.caption(f"📄 {doc['filename']} ({doc['chunks_count']} 块)")

        st.subheader("系统统计")
        if st.button("查看系统状态", use_container_width=True):
            try:
                stats = api_client.get_stats()
                st.json(stats)
            except Exception as exc:
                st.error(f"获取系统状态失败: {exc}")

        try:
            formats_info = api_client.get_supported_formats()
            st.caption(f"支持 {len(formats_info['supported_formats'])} 种文件格式")
        except Exception:
            st.caption("无法获取支持格式列表")


def main():
    render_sidebar()

    st.title("📖 RAG 智能文档问答系统")

    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])

    if prompt := st.chat_input("请输入您的问题..."):
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = str(uuid.uuid4())

        display_chat_message("user", prompt)
        add_message("user", prompt)

        try:
            with st.spinner("正在查询..."):
                result = api_client.query(prompt, st.session_state.conversation_id)

            display_chat_message("assistant", result["answer"])
            add_message(
                "assistant",
                result["answer"],
                {
                    "is_in_scope": result["is_in_scope"],
                    "confidence": result["confidence"],
                    "search_results": result["search_results"],
                },
            )

            render_query_details(result)
        except Exception as exc:
            error_msg = f"查询失败: {str(exc)}"
            display_chat_message("assistant", error_msg)
            add_message("assistant", error_msg)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"💬 消息数: {len(st.session_state.messages)}")
    with col2:
        st.caption(f"📄 文档数: {len(st.session_state.uploaded_documents)}")
    with col3:
        if st.session_state.conversation_id:
            st.caption(f"🆔 对话ID: {st.session_state.conversation_id[:8]}...")

    with st.expander("使用说明"):
        st.markdown(
            """
            1. 先上传文档，支持 PDF、Word、Excel、TXT、Markdown、JSON、CSV 和图片。
            2. 上传成功后，在输入框里直接提问。
            3. 系统会先检索文档片段，再基于检索结果生成回答。
            4. 若 PDF 为扫描件，系统会自动尝试 OCR。
            """
        )


if __name__ == "__main__":
    main()
