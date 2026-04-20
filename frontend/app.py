import os
import uuid
from html import escape
from datetime import datetime
from typing import Dict, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
SUPPORTED_UPLOAD_TYPES = ["pdf", "docx", "xlsx", "txt", "md", "json", "csv", "jpg", "jpeg", "png"]


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
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    def query(self, question: str, conversation_id: Optional[str] = None) -> Dict:
        payload = {"question": question, "conversation_id": conversation_id}
        response = requests.post(f"{self.base_url}/query", json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def get_conversation(self, conversation_id: str) -> Dict:
        response = requests.get(f"{self.base_url}/conversations/{conversation_id}", timeout=30)
        response.raise_for_status()
        return response.json()

    def delete_conversation(self, conversation_id: str) -> Dict:
        response = requests.delete(f"{self.base_url}/conversations/{conversation_id}", timeout=30)
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> Dict:
        response = requests.get(f"{self.base_url}/stats", timeout=30)
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict:
        response = requests.get(f"{self.base_url.replace('/api/v1', '')}/health", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_supported_formats(self) -> Dict:
        response = requests.get(f"{self.base_url}/documents/formats", timeout=30)
        response.raise_for_status()
        return response.json()


api_client = APIClient()


def configure_page():
    st.set_page_config(
        page_title="RAG 智能文档问答",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --page-bg: #f6f7f9;
            --panel: #ffffff;
            --ink: #17202a;
            --muted: #667085;
            --line: #e4e7ec;
            --accent: #007a7a;
            --accent-soft: #e6f5f4;
            --amber-soft: #fff7df;
        }

        .stApp {
            background: var(--page-bg);
            color: var(--ink);
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.85rem;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.5rem;
            padding-bottom: 5rem;
        }

        .app-hero {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 1rem;
        }

        .app-hero h1 {
            margin: 0 0 0.35rem;
            font-size: 1.75rem;
            line-height: 1.2;
            letter-spacing: 0;
        }

        .app-hero p {
            margin: 0;
            color: var(--muted);
        }

        .status-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-bottom: 1rem;
        }

        .status-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }

        .status-card span {
            color: var(--muted);
            display: block;
            font-size: 0.84rem;
            margin-bottom: 0.25rem;
        }

        .status-card strong {
            font-size: 1.05rem;
        }

        .empty-chat {
            background: var(--panel);
            border: 1px dashed #b7c0cc;
            border-radius: 8px;
            padding: 2.25rem;
            text-align: center;
            margin-top: 1rem;
        }

        .empty-chat h2 {
            font-size: 1.25rem;
            margin-bottom: 0.45rem;
        }

        .empty-chat p {
            color: var(--muted);
            margin: 0;
        }

        .doc-chip {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.7rem 0.75rem;
            background: #fbfcfd;
            margin-bottom: 0.45rem;
        }

        .doc-chip strong {
            display: block;
            overflow-wrap: anywhere;
        }

        .doc-chip span {
            color: var(--muted);
            font-size: 0.82rem;
        }

        .source-card {
            border-left: 3px solid var(--accent);
            background: #fbfcfd;
            padding: 0.75rem 0.85rem;
            margin: 0.6rem 0;
        }

        .source-card p {
            margin: 0.35rem 0 0;
            color: #344054;
            white-space: pre-wrap;
        }

        .footer-note {
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 1.25rem;
        }

        div[data-testid="stChatMessage"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.5rem;
        }

        div[data-testid="stChatInput"] {
            border-top: 1px solid var(--line);
            background: rgba(246, 247, 249, 0.94);
        }

        @media (max-width: 760px) {
            .status-row {
                grid-template-columns: 1fr;
            }

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state():
    defaults = {
        "conversation_id": None,
        "messages": [],
        "uploaded_documents": [],
        "api_connected": False,
        "last_query_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_confidence(confidence: float) -> str:
    return f"{confidence:.2%}"


def format_document_summary(document: Dict) -> str:
    return f"{document['filename']} · {document['chunks_count']} 个片段"


def get_scope_label(is_in_scope: bool) -> str:
    return "已命中文档范围" if is_in_scope else "未命中文档范围"


def escape_html(value: str) -> str:
    return escape(value, quote=True)


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
    st.session_state.last_query_result = None
    st.toast("已创建新对话", icon="✨")


def add_message(role: str, content: str, metadata: Optional[Dict] = None):
    st.session_state.messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
    )


def render_sidebar():
    with st.sidebar:
        st.title("📚 文档问答")

        api_connected = check_api_connection()
        if api_connected:
            st.success("API 连接正常")
        else:
            st.error("API 连接失败")

        st.divider()
        st.subheader("会话")
        new_col, delete_col = st.columns(2)
        with new_col:
            if st.button("新建", use_container_width=True):
                create_new_conversation()
        with delete_col:
            delete_disabled = not st.session_state.conversation_id
            if st.button("删除", use_container_width=True, disabled=delete_disabled):
                delete_current_conversation()

        if st.session_state.conversation_id:
            st.caption(f"ID `{st.session_state.conversation_id[:8]}...`")

        st.divider()
        st.subheader("文档")
        uploaded_file = st.file_uploader(
            "上传文件",
            type=SUPPORTED_UPLOAD_TYPES,
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            st.caption(uploaded_file.name)
            if st.button("上传文档", type="primary", use_container_width=True):
                upload_current_document(uploaded_file)

        if st.session_state.uploaded_documents:
            st.markdown("##### 当前文档")
            for document in st.session_state.uploaded_documents:
                filename = escape_html(document["filename"])
                st.markdown(
                    f"""
                    <div class="doc-chip">
                        <strong>{filename}</strong>
                        <span>{document['chunks_count']} 个片段</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()
        render_system_panel()


def delete_current_conversation():
    try:
        api_client.delete_conversation(st.session_state.conversation_id)
        create_new_conversation()
    except Exception as exc:
        st.error(f"删除会话失败: {exc}")


def upload_current_document(uploaded_file):
    if not st.session_state.conversation_id:
        st.session_state.conversation_id = str(uuid.uuid4())

    try:
        with st.spinner("正在处理文档..."):
            result = api_client.upload_document(uploaded_file, st.session_state.conversation_id)

        st.session_state.uploaded_documents.append(
            {
                "filename": result["filename"],
                "document_id": result["document_id"],
                "chunks_count": result["chunks_count"],
            }
        )
        st.success(f"已上传 {format_document_summary(result)}")
    except Exception as exc:
        st.error(f"文档上传失败: {exc}")


def render_system_panel():
    with st.expander("系统状态", expanded=False):
        try:
            formats_info = api_client.get_supported_formats()
            st.caption(
                f"支持 {len(formats_info['supported_formats'])} 种格式，"
                f"单文件上限 {formats_info['max_file_size_mb']} MB"
            )
        except Exception:
            st.caption("暂时无法获取格式列表")

        if st.button("刷新统计", use_container_width=True):
            try:
                stats = api_client.get_stats()
                st.json(stats)
            except Exception as exc:
                st.error(f"获取统计失败: {exc}")


def render_header():
    st.markdown(
        """
        <section class="app-hero">
            <h1>RAG 智能文档问答</h1>
            <p>围绕当前文档进行连续追问，答案下方保留可展开的检索依据。</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_status_row():
    status = "在线" if st.session_state.api_connected else "离线"
    conversation = st.session_state.conversation_id[:8] if st.session_state.conversation_id else "未创建"
    documents_count = len(st.session_state.uploaded_documents)
    messages_count = len(st.session_state.messages)

    st.markdown(
        f"""
        <div class="status-row">
            <div class="status-card"><span>服务状态</span><strong>{status}</strong></div>
            <div class="status-card"><span>当前会话</span><strong>{conversation}</strong></div>
            <div class="status-card"><span>内容规模</span><strong>{documents_count} 文档 · {messages_count} 消息</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message_history():
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-chat">
                <h2>对话区</h2>
                <p>当前会话的问答会显示在这里。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_query_details(result: Dict):
    with st.expander("检索依据", expanded=False):
        metric_cols = st.columns(3)
        metric_cols[0].metric("范围判定", get_scope_label(result["is_in_scope"]))
        metric_cols[1].metric("置信度", format_confidence(result["confidence"]))
        metric_cols[2].metric("处理耗时", f"{result['processing_time']:.2f} 秒")

        if result.get("scope_reasoning"):
            st.info(result["scope_reasoning"])

        search_results = result.get("search_results") or []
        if not search_results:
            st.caption("没有返回引用片段。")
            return

        for index, search_result in enumerate(search_results, start=1):
            filename = escape_html(search_result["metadata"].get("filename", "未知文档"))
            similarity = search_result["similarity_score"]
            preview = search_result["content"][:700]
            if len(search_result["content"]) > 700:
                preview += "..."
            preview = escape_html(preview)

            st.markdown(
                f"""
                <div class="source-card">
                    <strong>片段 {index} · {filename} · 相似度 {similarity:.2f}</strong>
                    <p>{preview}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def handle_chat_input():
    prompt = st.chat_input("向当前文档提问")
    if not prompt:
        return

    if not st.session_state.conversation_id:
        st.session_state.conversation_id = str(uuid.uuid4())

    with st.chat_message("user"):
        st.markdown(prompt)
    add_message("user", prompt)

    try:
        with st.spinner("正在检索并生成回答..."):
            result = api_client.query(prompt, st.session_state.conversation_id)

        with st.chat_message("assistant"):
            st.markdown(result["answer"])
        add_message(
            "assistant",
            result["answer"],
            {
                "is_in_scope": result["is_in_scope"],
                "confidence": result["confidence"],
                "search_results": result["search_results"],
            },
        )
        st.session_state.last_query_result = result
        render_query_details(result)
    except Exception as exc:
        error_msg = f"查询失败: {exc}"
        with st.chat_message("assistant"):
            st.error(error_msg)
        add_message("assistant", error_msg)


def render_last_query_details():
    result = st.session_state.last_query_result
    if result:
        render_query_details(result)


def render_footer():
    st.markdown(
        '<p class="footer-note">支持 PDF、Word、Excel、TXT、Markdown、JSON、CSV 和图片文件。</p>',
        unsafe_allow_html=True,
    )


def main():
    configure_page()
    inject_styles()
    init_session_state()
    render_sidebar()
    render_header()
    render_status_row()
    render_message_history()
    render_last_query_details()
    handle_chat_input()
    render_footer()


if __name__ == "__main__":
    main()
