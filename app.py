# app.py
import os
import base64
import logging
import mimetypes
from typing import List, Tuple, Dict, Any

import gradio as gr
from anthropic import Anthropic, APIConnectionError, APIStatusError, RateLimitError

# Constants
MODEL_NAME = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 8192
MAX_FILE_SIZE_MB = 10
ALLOWED_MIME_TYPES = {
    "text/", "image/", "application/pdf",
    "application/json", "application/msword"
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_file(file_path: str) -> None:
    """Validate file size and MIME type."""
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # in MB
    if file_size > MAX_FILE_SIZE_MB:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not any(mime_type.startswith(allowed) for allowed in ALLOWED_MIME_TYPES):
        raise ValueError(f"Unsupported file type: {mime_type}")


def process_attachments(files: List[gr.components.File]) -> List[Dict[str, Any]]:
    """Process and validate uploaded files."""
    attachments = []
    for file in files:
        try:
            validate_file(file.name)
            mime_type, _ = mimetypes.guess_type(file.name)

            with open(file.name, "rb") as f:
                file_data = f.read()

            attachments.append({
                "type": "base64",
                "media_type": mime_type or "application/octet-stream",
                "data": base64.b64encode(file_data).decode("utf-8")
            })
            logger.info(f"Successfully processed file: {file.name}")

        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            raise gr.Error(f"File error: {str(e)}") from e

    return attachments


def chat_with_claude(
    message: str,
    history: List[Tuple[str, str]],
    files: List[gr.components.File]
) -> str:
    """
    Send message to Claude API with error handling and logging.
    
    Args:
        message: User's text input
        history: Chat history [(user_msg, bot_msg), ...]
        files: List of uploaded files
        
    Returns:
        Claude's response text
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("API key not found in environment variables")
        raise gr.Error("Configuration error: API key missing")

    try:
        client = Anthropic(api_key=api_key)
        attachments = process_attachments(files)

        messages = [{"role": "user", "content": message, "attachments": attachments}]
        if history:
            for user_msg, bot_msg in history:
                messages.extend([
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": bot_msg}
                ])

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=0.0,
            messages=messages,
            timeout=30
        )

        logger.info("Successfully received response from Claude API")
        return response.content[0].text

    except APIConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        raise gr.Error("Connection error: Please check your internet connection")

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {str(e)}")
        raise gr.Error("Rate limit exceeded: Please wait before sending new messages")

    except APIStatusError as e:
        logger.error(f"API error: {e.status_code} - {str(e)}")
        raise gr.Error(f"API error: {e.response.json().get('error', {}).get('message', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise gr.Error(f"Unexpected error: {str(e)}") from e


def handle_chat(
    message: str,
    history: List[Tuple[str, str]],
    files: List[gr.components.File]
) -> Tuple[List[Tuple[str, str]], List[gr.components.File]]:
    """
    Handle complete chat interaction with state management.
    
    Args:
        message: User input message
        history: Chat history
        files: Uploaded files
        
    Returns:
        Updated chat history and cleared files
    """
    try:
        response = chat_with_claude(message, history, files)
        updated_history = history + [(message, response)]
        return updated_history, []

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        updated_history = history + [(message, error_msg)]
        return updated_history, []


# Gradio Interface
with gr.Blocks(
    title="Claude 3.5 Chat Interface",
    theme=gr.themes.Soft(),
    css=".file-size {font-size: 0.8em; color: #666;}"
) as demo:
    gr.Markdown(f"## 🤖 Claude 3.5 Sonnet Chat (v{os.getenv('APP_VERSION', '1.0')})")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, label="Chat History")
            with gr.Accordion("File Upload", open=False):
                files = gr.Files(
                    label="Attach Files (Max 10MB)",
                    file_count="multiple",
                    file_types=list(ALLOWED_MIME_TYPES)
                )
            msg = gr.Textbox(label="Your Message", placeholder="Type your message...")
            submit_btn = gr.Button("Send", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            with gr.Accordion("Advanced Options", open=False):
                max_tokens = gr.Number(
                    value=MAX_TOKENS,
                    label="Max Tokens",
                    interactive=False
                )
                temperature = gr.Number(
                    value=0.0,
                    label="Temperature",
                    interactive=False
                )
            clear_btn = gr.Button("Clear Chat History", variant="stop")

    # Event Handlers
    submit_btn.click(
        fn=handle_chat,
        inputs=[msg, chatbot, files],
        outputs=[chatbot, files]
    )

    msg.submit(
        fn=handle_chat,
        inputs=[msg, chatbot, files],
        outputs=[chatbot, files]
    )

    clear_btn.click(
        fn=lambda: ([], []),
        inputs=[],
        outputs=[chatbot, files],
        queue=False
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",  # nosec
        server_port=int(os.getenv("PORT", 7860)),
        show_error=True
    )
