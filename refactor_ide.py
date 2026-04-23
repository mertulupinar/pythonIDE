import ast
import os

def refactor():
    source_file = "ide.py"
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()
    
    lines = source_code.split('\n')
    
    tree = ast.parse(source_code)
    
    class_bounds = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            class_bounds[node.name] = (start_line, end_line)
            
    # We also need imports. Let's just collect all imports from ide.py
    imports = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            imports.append('\n'.join(lines[start_line:end_line]))
            
    common_imports = '\n'.join(imports) + "\n\n"
    
    # Also Jedi fallback code
    try_jedi = """try:
    import jedi
    JEDI_AVAILABLE = True
except ImportError:
    JEDI_AVAILABLE = False

"""
    common_imports += try_jedi
    
    modules = {
        "core/highlighter.py": ["Pide"],
        "editor/line_number.py": ["LineNumberArea"],
        "editor/minimap.py": ["Minimap"],
        "editor/code_editor.py": ["ModernCodeEditor"],
        "widgets/console.py": ["OutputConsole"],
        "widgets/terminal.py": ["TerminalWidget"],
        "dialogs/find_replace.py": ["FindReplaceDialog"],
        "managers/git_manager.py": ["GitManagerDialog"],
        "managers/pip_manager.py": ["PipManagerDialog"],
        "ui/main_window.py": ["ModernPythonIDE"]
    }
    
    # Create directories
    for path in modules.keys():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
    for file_path, classes in modules.items():
        content = common_imports
        
        # Add local imports for cross-dependencies
        if file_path == "editor/code_editor.py":
            content += "from core.highlighter import Pide\n"
            content += "from editor.line_number import LineNumberArea\n"
            content += "from editor.minimap import Minimap\n\n"
        elif file_path == "ui/main_window.py":
            content += "from editor.code_editor import ModernCodeEditor\n"
            content += "from widgets.console import OutputConsole\n"
            content += "from widgets.terminal import TerminalWidget\n"
            content += "from dialogs.find_replace import FindReplaceDialog\n"
            content += "from managers.git_manager import GitManagerDialog\n"
            content += "from managers.pip_manager import PipManagerDialog\n\n"
            
        for cls in classes:
            start, end = class_bounds[cls]
            # check for decorators (ast.ClassDef lineno is where 'class' starts, decorators are above it)
            # but let's assume no decorators for now, or just trust node.lineno
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name == cls:
                    if node.decorator_list:
                        start = node.decorator_list[0].lineno - 1
            
            content += '\n'.join(lines[start:end]) + "\n\n"
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    # Create main.py
    main_code = common_imports + """
from ui.main_window import ModernPythonIDE

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ide = ModernPythonIDE()
    ide.show()
    sys.exit(app.exec_())
"""
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(main_code)
        
    print("Refactoring completed successfully!")

if __name__ == "__main__":
    refactor()
