from io import BytesIO

import google.generativeai as genai
import PIL.Image

from .auth import is_authorized
from .command import execute_command, models_info_command
from .context import ChatManager, ImageChatManager
from .telegram import Update, send_message
from .printLog import send_log, send_image_log
from .config import GOOGLE_API_KEY, generation_config, safety_settings, gemini_err_info, new_chat_info

# Configure Gemini API
genai.configure(api_key=GOOGLE_API_KEY[0])

# Initialize Gemini models
model_usual = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)

model_vision = genai.GenerativeModel(
    model_name="gemini-pro-vision",
    generation_config=generation_config,
    safety_settings=safety_settings
)

# Chat Manager with Gemini Integration
class ChatConversation:
    """
    Manages an ongoing chat session. If the input is /new,
    it triggers the start of a fresh conversation.
    """

    def __init__(self) -> None:
        self.chat = model_usual.start_chat(history=[])

    def send_message(self, prompt: str) -> str:
        """Send a message to the chat."""
        if prompt.startswith("/new"):
            self.__init__()
            result = new_chat_info
        else:
            try:
                response = self.chat.send_message(prompt)
                result = response.text
            except Exception as e:
                result = f"{gemini_err_info}\n{repr(e)}"
        return result

    @property
    def history(self):
        return self.chat.history

    @property
    def history_length(self):
        return len(self.chat.history)


# Initialize Chat Manager
chat_manager = ChatManager()


def handle_message(update_data):
    """Handle incoming messages and route them to appropriate handlers."""
    update = Update(update_data)

    # Log the received event
    if update.is_group:
        log = (f"{event_received}\n@{update.user_name} id:`{update.from_id}` "
               f"{group} @{update.group_name} id:`{update.chat_id}`\n"
               f"{the_content_sent_is}\n{update.text}\n```json\n{update_data}```")
    else:
        log = (f"{event_received}\n@{update.user_name} id:`{update.from_id}`\n"
               f"{the_content_sent_is}\n{update.text}\n```json\n{update_data}```")
    send_log(log)

    # Check authorization
    authorized = is_authorized(update.is_group, update.from_id, update.user_name, update.chat_id, update.group_name)

    if not authorized:
        if update.is_group:
            send_message(update.chat_id, f"{group_no_permission_info}\nID:`{update.chat_id}`")
            log = (f"@{update.user_name} id:`{update.from_id}` {group} @{update.group_name} id:`{update.chat_id}`"
                   f"{no_rights_to_use},{the_content_sent_is}\n{update.text}")
        else:
            send_message(update.from_id, f"{user_no_permission_info}\nID:`{update.from_id}`")
            log = f"@{update.user_name} id:`{update.from_id}`{no_rights_to_use},{the_content_sent_is}\n{update.text}"
        send_log(log)
        return

    # Handle commands
    if update.type == "command":
        response_text = execute_command(update.from_id, update.text, update.from_type, update.chat_id)
        if response_text:
            send_message(update.chat_id, response_text)
            if update.is_group:
                log = (f"@{update.user_name} id:`{update.from_id}` {group} @{update.group_name} id:`{update.chat_id}`"
                       f"{the_content_sent_is}\n{update.text}\n{the_reply_content_is}\n{response_text}")
            else:
                log = (f"@{update.user_name} id:`{update.from_id}`{the_content_sent_is}\n{update.text}\n"
                       f"{the_reply_content_is}\n{response_text}")
            send_log(log)

    # Handle text messages
    elif update.type == "text":
        chat = chat_manager.get_chat(update.chat_id)
        answer = chat.send_message(update.text)
        extra_text = (
            f"\n\n{prompt_new_info}" if chat.history_length >= prompt_new_threshold * 2 else ""
        )
        response_text = f"{answer}{extra_text}"
        send_message(update.chat_id, response_text)
        dialogue_logarithm = int(chat.history_length / 2)
        if update.is_group:
            log = (f"@{update.user_name} id:`{update.from_id}` {group} @{update.group_name} id:`{update.chat_id}`"
                   f"{the_content_sent_is}\n{update.text}\n{the_reply_content_is}\n{response_text}\n"
                   f"{the_logarithm_of_historical_conversations_is}{dialogue_logarithm}")
        else:
            log = (f"@{update.user_name} id:`{update.from_id}`{the_content_sent_is}\n{update.text}\n"
                   f"{the_reply_content_is}\n{response_text}\n{the_logarithm_of_historical_conversations_is}"
                   f"{dialogue_logarithm}")
        send_log(log)

    # Handle images
    elif update.type == "photo":
        image_bytes = BytesIO(update.file_bytes)
        prompt = update.photo_caption
        response_text = generate_text_with_image(prompt, image_bytes)
        send_message(update.chat_id, response_text, reply_to_message_id=update.message_id)

        photo_url = update.photo_url
        image_id = update.file_id
        if update.is_group:
            log = (f"@{update.user_name} id:`{update.from_id}` {group} @{update.group_name} id:`{update.chat_id}`"
                   f"[photo]({photo_url}),{the_accompanying_message_is}\n{update.photo_caption}\n"
                   f"{the_reply_content_is}\n{response_text}")
        else:
            log = (f"@{update.user_name} id:`{update.from_id}`[photo]({photo_url}),{the_accompanying_message_is}\n"
                   f"{update.photo_caption}\n{the_reply_content_is}\n{response_text}")
        send_image_log("", image_id)
        send_log(log)

    # Handle unrecognized content
    else:
        send_message(update.chat_id, f"{unable_to_recognize_content_sent}\n\n/help")
        if update.is_group:
            log = (f"@{update.user_name} id:`{update.from_id}` {group} @{update.group_name} id:`{update.chat_id}`"
                   f"{send_unrecognized_content}")
        else:
            log = f"@{update.user_name} id:`{update.from_id}`{send_unrecognized_content}"
        send_log(log)


# Command List
command_list = {
    "/start": lambda update, context: send_message(update.chat_id, "Welcome!"),
    "/help": lambda update, context: send_message(update.chat_id, "Help information here."),
    "/models": models_info_command,
}

if __name__ == "__main__":
    print(list_models())