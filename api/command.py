from time import sleep
import google.generativeai as genai
from .auth import is_admin
from .config import *
from .printLog import send_log
from .telegram import send_message

# List of models and their descriptions
models_info = {
    "gemini-pro": "General-purpose, highly capable LLM.",
    "gemini-pro-vision": "Pro with image understanding.",
    "gemini-ultra": "Most powerful, for complex tasks.",
    "gemini-ultra-vision": "Ultra with image capabilities.",
    "gemini-1.0-pro": "Earlier versions.",
    "gemini-1.0-pro-vision": "Earlier versions with vision.",
    "gemini-1.0-ultra": "Earlier versions.",
    "gemini-1.0-ultra-vision": "Earlier versions with vision.",
    "gemini-1.5-pro": "Intermediate versions.",
    "gemini-1.5-pro-vision": "Intermediate versions with vision.",
    "gemini-1.5-ultra": "Intermediate versions.",
    "gemini-1.5-ultra-vision": "Intermediate versions with vision.",
    "gemini-nano": "Efficient for on-device use.",
    "gemini-nano-vision": "Nano with visual input.",
    "gemini-flash": "Optimized for speed.",
    "gemini-2.0-flash": "Improved speed and performance.",
    "gemini-experimental": "Developing features.",
    "gemini-experimental-vision": "Developing features with vision.",
    "Gemma 3 27B": "Gemma 3 27B model.",
    "Gemma 2 2B": "Gemma 2 2B model.",
    "Gemma 2 9B": "Gemma 2 9B model.",
    "Gemma 2 27B": "Gemma 2 27B model."
}

def help():
    result = f"{help_text}\n\n{command_list}"
    return result

def list_models():
    for m in genai.list_models():
        #send_log(str(m))
        print(str(m))
        if 'generateContent' in m.supported_generation_methods:
            send_log(str(m.name))
            print(str(m.name))
    return ""

def models_info_command(update, context):
    """Send a list of available models and their descriptions."""
    message = "Available models:\n\n"
    for model, description in models_info.items():
        message += f"{model}: {description}\n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def get_my_info(id):
    return f"your telegram id is: `{id}`"

def get_group_info(type, chat_id):
    if type == "supergroup":
        return f"this group id is: `{chat_id}`"
    return "Please use this command in a group"

def get_allowed_users():
    send_log(f"```json\n{ALLOWED_USERS}```")
    return ""

def get_allowed_groups():
    send_log(f"```json\n{ALLOWED_GROUPS}```")
    return ""

def get_API_key():
    send_log(f"```json\n{GOOGLE_API_KEY}```")
    return ""

def speed_test(id):
    """ This command seems useless, but it must be included in every robot I make. """
    send_message(id, "开始测速")
    sleep(5)
    return "测试完成，您的5G速度为：\n**114514B/s**"

def send_message_test(id, command):
    if not is_admin(id):
        return admin_auch_info
    a = command.find(" ")
    b = command.find(" ", a + 1)
    if a == -1 or b == -1:
        return command_format_error_info
    to_id = command[a+1:b]
    text = command[b+1:]
    try:
        send_message(to_id, text)
    except Exception as e:
        send_log(f"err:\n{e}")
        return
    send_log("success")
    return ""

def excute_command(from_id, command, from_type, chat_id):
    if command.startswith("start") or command.startswith("help"):
        return help()

    elif command.startswith("get_my_info"):
        return get_my_info(from_id)

    elif command.startswith("get_group_info"):
        return get_group_info(from_type, chat_id)

    elif command.startswith("5g_test"):
        return speed_test(chat_id)

    elif command.startswith("send_message"):
        return send_message_test(from_id, command)

    elif command in ["get_allowed_users", "get_allowed_groups", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE == "0":
            return debug_mode_info

        if command == "get_allowed_users":
            return get_allowed_users()
        elif command == "get_allowed_groups":
            return get_allowed_groups
        elif command == "get_api_key":
            return get_API_key()
        elif command == "list_models":
            return list_models()

    elif command == "models":
        return models_info_command()

    else:
        return command_format_error_info