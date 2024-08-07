import asyncio
import logging
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior

from plugin_manager import load_plugins, list_plugin_files

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'plugins'
app.config['ALLOWED_EXTENSIONS'] = {'py'}

# Initialize the kernel
kernel = Kernel()

# Add Azure OpenAI chat completion
kernel.add_service(AzureChatCompletion(
    deployment_name="gpt-35-turbo",
    api_key='9834a230b1234782838e45cd6aad4d9f',
    base_url="https://soumenopenai.openai.azure.com/openai",
    api_version="2023-03-15-preview"
))

# Set the logging level for debugging
logging.basicConfig(
    format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("kernel").setLevel(logging.DEBUG)

@app.route('/upload_plugin', methods=['POST'])
def upload_plugin():
    if 'file' in request.files and request.files['file'].filename != '':
        # Handle file upload
        file = request.files['file']
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return jsonify({"message": "Plugin uploaded successfully"}), 200
        return jsonify({"error": "Invalid file format"}), 400
    
    if 'plugin_code' in request.json and 'plugin_name' in request.json:
        # Handle raw code upload
        plugin_code = request.json['plugin_code']
        plugin_name = secure_filename(request.json['plugin_name'])
        if not plugin_name.endswith('.py'):
            plugin_name += '.py'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], plugin_name)
        with open(file_path, 'w') as f:
            f.write(plugin_code)
        return jsonify({"message": "Plugin code saved successfully"}), 200

    return jsonify({"error": "No valid data provided"}), 400

@app.route('/load_plugins', methods=['POST'])
def load_plugins_endpoint():
    try:
        plugins_to_load = request.json.get('plugins', [])
        plugin_files = list_plugin_files(app.config['UPLOAD_FOLDER'])
        selected_plugins = [f for f in plugin_files if f.split('.')[0] in plugins_to_load]
        if not selected_plugins:
            return jsonify({"error": "No valid plugins specified"}), 400
        
        load_plugins(kernel, selected_plugins)
        return jsonify({"message": "Selected plugins loaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        user_input = request.json.get('input', '')

        # Enable planning
        execution_settings = AzureChatPromptExecutionSettings(tool_choice="auto")
        execution_settings.function_call_behavior = FunctionCallBehavior.EnableFunctions(auto_invoke=True, filters={})

        # Create a history of the conversation
        history = ChatHistory()
        history.add_user_message(user_input)

        chat_completion = kernel.get_service(type=ChatCompletionClientBase)
        result = (await chat_completion.get_chat_message_contents(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
            arguments=KernelArguments(),
        ))[0]

        history.add_message(result)

        return jsonify({"response": str(result)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=5000)
