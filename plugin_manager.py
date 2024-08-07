import importlib
import os

def list_plugin_files(directory):
    # List all Python files in the given directory, excluding __init__.py
    return [
        f for f in os.listdir(directory)
        if f.endswith('_plugin.py') and f != '__init__.py'
    ]

def load_plugins(kernel, plugin_files):
    print("Loading plugins...")
    
    for plugin_file in plugin_files:
        plugin_name = plugin_file.split('.')[0]  # e.g., lights_plugin
        
        try:
            # Import the module dynamically
            spec = importlib.util.spec_from_file_location(plugin_name, os.path.join('plugins', plugin_file))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Assume the class name matches the file name (e.g., LightsPlugin in lights_plugin.py)
            class_name = ''.join(word.title() for word in plugin_name.split('_'))
            plugin_class = getattr(module, class_name, None)
            
            if plugin_class:
                kernel.add_plugin(plugin_class(), plugin_name=plugin_name)
                print(f"Loaded plugin: {plugin_name}")
            else:
                print(f"Plugin class not found in {plugin_name}")
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
