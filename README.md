<div align="center">

# 🐍 PyIDE — Professional Python Development Environment

### Developed by **Mert Ulupınar** ✨

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**A feature-rich, modern Python IDE built with PyQt5**  
Combining power, elegance, and simplicity for Python developers of all levels.

[Features](#-features) • [Installation](#️-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#️-installation)
- [Usage](#-usage)
- [Architecture & Design](#-architecture--design)
- [Key Technologies](#-key-technologies)
- [Keyboard Shortcuts](#⌨️-keyboard-shortcuts)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**PyIDE** is a professional-grade Python Integrated Development Environment designed to provide developers with a seamless coding experience. Built entirely with PyQt5, it combines modern UI/UX principles with powerful development tools.

### 🎪 Why PyIDE?

- **🎨 Beautiful & Modern Interface**: VS Code-inspired dark themes with customizable color schemes
- **⚡ Lightweight & Fast**: No bloat, just pure Python development tools
- **🔧 All-in-One Solution**: Code editor, terminal, debugger, and package manager in one place
- **🎓 Beginner-Friendly**: Clean UI with intuitive controls, perfect for learning Python
- **💪 Professional Tools**: Git integration, debugging, error highlighting for serious development

---

## 🚀 Recent Updates (v2.0)

- **🏗️ Modular Architecture**: The massive monolithic codebase (~2500 lines) was completely refactored into a highly scalable, world-class folder structure (`core/`, `editor/`, `ui/`, `managers/`).
- **🧠 Jedi IntelliSense**: Upgraded from static word lists to intelligent, context-aware autocompletion using the `jedi` library.
- **🏃‍♂️ Native Code Execution**: Fixed the tempfile execution bug. Saved scripts now natively execute from their actual directory, meaning relative paths and `__file__` variables work perfectly.
- **🔄 Dynamic Explorer Sync**: The file explorer now actively follows your context. Switching between tabs or opening new files automatically syncs the file tree and working directory to the active file's location.
- **🌍 Language Consistency**: Fully standardized the entire UI into English for a professional, consistent developer experience.

---

## ✨ Features

### 🎨 **Advanced Code Editor**

#### **Intelligent Syntax Highlighting**

- **Why**: Makes code more readable and helps identify syntax errors instantly
- **How**: Uses custom `QSyntaxHighlighter` with regex patterns
- **Features**:
  - Python keywords (`def`, `class`, `if`, `for`, etc.)
  - Built-in functions with validation
  - Dynamic module import detection
  - String literals with multi-line support
  - Comments and numbers
  - Variables (declaration vs. usage)
  - Function calls with color-coded validation

#### **Smart Code Features**

- **Line Numbers**: Custom painted line number area with dynamic width
- **Current Line Highlighting**: Visual indicator for active line
- **Auto-Indentation**: Automatically indents after colons (`:`)
- **Auto-Pairing**: Automatically closes brackets, quotes, and parentheses
- **Tab to Spaces**: Converts tabs to 4 spaces for PEP 8 compliance

#### **Intelligent Autocomplete (Ctrl+Space)**

- **Why**: Speed up coding by suggesting completions as you type
- **How**: Uses `QCompleter` with pre-populated word lists
- **Features**:
  - **100+ Built-in Completions**: Python keywords, built-in functions, common modules
  - **Manual Trigger**: Press `Ctrl+Space` to show suggestions
  - **Auto-Popup**: Automatically appears after typing 2+ characters
  - **Case-Insensitive**: Finds matches regardless of case
  - **Styled Popup**: Dark theme dropdown with syntax highlighting
  - **Smart Filtering**: Narrows down results as you type
  - **Keyboard Navigation**: Use arrow keys and Enter to select
- **Supported Categories**:
  - Python keywords: `def`, `class`, `if`, `for`, `while`, `try`, etc.
  - Built-in functions: `print`, `len`, `range`, `map`, `filter`, etc.
  - Common modules: `os`, `sys`, `math`, `random`, `json`, `re`, etc.

#### **Minimap Code Overview**

- **Why**: Navigate large files quickly and see code structure at a glance
- **How**: Custom painted widget showing miniature code representation
- **Features**:
  - **120px Sidebar**: Compact code overview on the right side
  - **Click to Jump**: Click any line in minimap to jump there instantly
  - **Visual Density**: Line length indicates code density
  - **Visible Area Indicator**: Blue highlight shows current viewport
  - **Scroll Sync**: Mouse wheel on minimap scrolls the main editor
  - **Real-Time Updates**: Updates as you type
  - **Color Coding**: Brighter lines indicate code, darker for empty lines
- **Perfect For**: Long files (100+ lines) where you need quick navigation

### 🐛 **Error Detection & Debugging**

#### **Real-Time Error Highlighting**

- **Why**: Instantly see where errors occur without searching through output
- **How**: Parses stderr output using regex to extract line numbers
- **Features**:
  - Red background highlighting on error lines
  - Error line numbers displayed in console
  - Automatic error detection from Python traceback
  - Persistent highlighting until next run

#### **Integrated Debugger (pdb)**

- **Why**: Step through code line-by-line to understand program flow
- **How**: Launches Python's built-in debugger in a separate terminal
- **Usage**: Press `Shift+F5` or go to `Run → Debug Mode`
- **Commands**:
  - `n` (next): Execute current line
  - `s` (step): Step into functions
  - `c` (continue): Continue execution
  - `l` (list): Show source code
  - `p variable`: Print variable value
  - `q` (quit): Exit debugger

### 🔍 **Search & Edit Tools**

#### **Find & Replace Dialog (Ctrl+F)**

- **Why**: Quickly search and modify text across your code
- **How**: Uses `QTextDocument` search with regex support
- **Features**:
  - **Find Next/Previous**: Navigate through matches with F3/Shift+F3
  - **Replace Single**: Replace current match
  - **Replace All**: Replace all occurrences at once
  - **Case Sensitive**: Toggle case-sensitive matching
  - **Whole Word**: Match complete words only
  - **Regex Support**: Use regular expressions for complex patterns
  - **Smart Wrapping**: Automatically wraps to start/end when no more matches
  - **Status Messages**: Real-time feedback on search results
  - **Modeless Dialog**: Keep dialog open while editing
  - **Visual Highlighting**: Selected matches are highlighted in editor
- **Keyboard Shortcuts**:
  - `Ctrl+F`: Open Find & Replace dialog
  - `F3`: Find next occurrence
  - `Shift+F3`: Find previous occurrence
  - `Enter`: Replace current and find next

#### **Code Snippets (Tab Expansion)**

- **Why**: Write boilerplate code faster with templates
- **How**: Type trigger word + Tab to expand into full template
- **Built-in Snippets**:
  1. **`def` + Tab**: Function template
     ```python
     def function_name():
         pass
     ```
  2. **`class` + Tab**: Class template with **init**
     ```python
     class ClassName:
         def __init__(self):
             pass
     ```
  3. **`if` + Tab**: If statement
     ```python
     if condition:
         pass
     ```
  4. **`for` + Tab**: For loop
     ```python
     for item in items:
         pass
     ```
  5. **`while` + Tab**: While loop
     ```python
     while condition:
         pass
     ```
  6. **`try` + Tab**: Try-except block
     ```python
     try:
         pass
     except Exception as e:
         pass
     ```
  7. **`with` + Tab**: Context manager
     ```python
     with open("file.txt", "r") as f:
         content = f.read()
     ```
  8. **`main` + Tab**: Main guard
     ```python
     if __name__ == "__main__":
         pass
     ```
  9. **`init` + Tab**: Constructor method
  10. **`str` + Tab**: String representation method
  11. **`repr` + Tab**: Object representation method
- **Usage**: Type snippet name, press `Tab`, then edit placeholders
- **Smart Cursor**: Automatically selects first editable part

### 📂 **File Management**

#### **Dynamic File Explorer**

- **Why**: Quick navigation and project organization with real-time updates
- **How**: Uses `QTreeWidget` with `QFileSystemWatcher` for live monitoring
- **Features**:
  - **Real-Time Updates**: Automatically refreshes when files change
  - **Manual Refresh**: 🔄 button in header for instant refresh
  - **Hierarchical Structure**: Nested folder display with expand/collapse
  - **File Type Icons**: Python (🐍), folders (📁), text files (📄)
  - **Smart Filtering**: Auto-hides junk folders (`.git`, `__pycache__`, `node_modules`, `venv`)
  - **Double-Click to Open**: Quick file access
  - **Right-Click Context Menu**:
    - 📄 **New File**: Create new file in selected folder
    - 📁 **New Folder**: Create new folder
    - ✏️ **Rename**: Rename files/folders with dialog
    - 🗑️ **Delete**: Delete with confirmation (irreversible!)
    - 📂 **Show in Explorer**: Open in system file manager (Windows/Mac/Linux)
  - **Debounced Refresh**: 500ms delay prevents excessive updates
  - **Cross-Platform**: Works on Windows (Explorer), macOS (Finder), Linux (xdg-open)

#### **Multi-Tab Editor**

- **Why**: Work with multiple files simultaneously
- **Features**:
  - Unlimited tabs
  - Per-tab file tracking
  - Closable tabs with protection (won't close last tab)
  - Tab switching with keyboard/mouse
  - Unique file path tracking prevents duplicate tabs

### 💻 **Terminal Integration**

#### **Embedded Terminal**

- **Why**: Execute commands without leaving the IDE
- **How**: Uses `QProcess` to embed cmd/bash
- **Features**:
  - Full terminal emulation
  - Real-time output streaming
  - Command history
  - Color-coded output (green for stdout, red for stderr)
  - Cross-platform (CMD on Windows, Bash on Linux/Mac)

### 🏃 **Code Execution**

#### **Smart Run System**

- **Why**: Execute Python code with proper handling of input/output
- **How**: Uses `subprocess` with temporary file execution
- **Features**:
  - **Input Detection**: Automatically detects `input()` calls
  - **Console Mode**: For input-free code, shows output in IDE
  - **Terminal Mode**: For interactive code, opens new terminal window
  - **Error Parsing**: Automatically highlights error lines
  - **Timeout Protection**: 30-second timeout prevents infinite loops

### 📦 **Package Manager (pip)**

#### **Visual pip Interface**

- **Why**: Manage Python packages without command line
- **How**: Wraps pip commands with GUI controls
- **Features**:
  - **List Packages**: Shows all installed packages with versions
  - **Search**: Real-time filtering of package list
  - **Install**: Add new packages with progress tracking
  - **Uninstall**: Remove packages with confirmation dialog
  - **Progress Indicators**: Visual feedback during operations
  - **Log Output**: Detailed command output for troubleshooting

**Access**: `Tools → Package Manager (pip)`

### 🔀 **Git Integration**

#### **Visual Git Interface**

- **Why**: Version control without command line
- **How**: Executes git commands via subprocess with GUI feedback
- **Features**:
  - **Status**: View current branch and changed files
  - **Add All**: Stage all changes (`git add .`)
  - **Commit**: Commit with custom message
  - **Push**: Upload changes to remote
  - **Pull**: Download changes from remote
  - **Real-time Output**: Command results shown in log
  - **Confirmation Dialogs**: Prevents accidental pushes

**Access**: `Tools → Git Manager`

### 🎨 **Theme System**

#### **7 Professional Built-in Themes**

- **Why**: Reduce eye strain and personalize appearance
- **How**: Dynamic stylesheet switching with instant apply
- **Themes**:

  1. **⚫ Default (VS Code Dark)**: Classic dark theme with blue accents

     - Background: `#1e1e1e`, Accent: `#007acc`
     - Best for: General use, VS Code users

  2. **🧛 Dracula**: Popular purple-accented dark theme

     - Background: `#282a36`, Accent: `#bd93f9`
     - Best for: Night coding, purple lovers

  3. **🌊 Nord**: Arctic-inspired blue/cyan theme

     - Background: `#2e3440`, Accent: `#88c0d0`
     - Best for: Calm, professional look

  4. **🌙 Monokai**: Sublime Text's classic theme

     - Background: `#272822`, Accent: `#a6e22e`
     - Best for: Long coding sessions, Sublime users

  5. **☀️ Solarized Dark**: Scientific color precision theme

     - Background: `#002b36`, Accent: `#b58900`
     - Best for: Reduced eye strain, academic work

  6. **🔵 One Dark (Atom)**: Atom editor's default theme

     - Background: `#282c34`, Accent: `#98c379`
     - Best for: Modern look, Atom users

  7. **🐙 GitHub Dark**: GitHub's official dark theme

     - Background: `#0d1117`, Accent: `#f78166`
     - Best for: GitHub integration, familiar interface

  8. **🟤 Gruvbox**: Retro warm theme
     - Background: `#282828`, Accent: `#fabd2f`
     - Best for: Vintage feel, Vim users

**Access**: `🎨 Theme → [Select Theme]`  
**Switch Instantly**: No restart required, changes apply immediately

### 📊 **Output Console**

#### **Dual-Panel System**

- **Output Tab**: Shows Python script results
- **Terminal Tab**: Interactive command line
- **Features**:
  - Syntax-highlighted output
  - Scrollable history
  - Clear button for quick cleanup
  - HTML-formatted messages (colors, bold, italic)
  - Auto-scrolls to latest output

---

## 🛠️ Installation

### ✅ Prerequisites

- **Python 3.7+**: [Download Python](https://www.python.org/downloads/)
- **pip**: Usually comes with Python

### 📦 Dependencies

PyIDE requires only one external dependency:

```bash
pip install PyQt5
```

**Why PyQt5?**

- Cross-platform GUI framework
- Professional-grade widgets
- Excellent performance
- Rich documentation

### 🚀 Quick Start

1. **Clone or Download**:

   ```bash
   git clone https://github.com/https:/mertulupinar/pyide.git
   cd pyide
   ```

2. **Install Requirements**:

   ```bash
   pip install -r requirements.txt
   ```

   _Or manually_:

   ```bash
   pip install PyQt5
   ```

3. **Run**:
   ```bash
   python main.py
   ```

### 📁 Project Structure

```text
pythonIDE/
│
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── LICENSE                  # MIT License
│
├── core/
│   └── highlighter.py       # Syntax Highlighting engine
├── editor/
│   ├── code_editor.py       # Main code editor widget
│   ├── line_number.py       # Line number area component
│   └── minimap.py           # Code minimap navigation
├── dialogs/
│   └── find_replace.py      # Find & Replace dialog
├── managers/
│   ├── git_manager.py       # Git integration manager
│   └── pip_manager.py       # Pip package manager
├── widgets/
│   ├── console.py           # Output console widget
│   └── terminal.py          # Built-in terminal widget
└── ui/
    ├── main_window.py       # Main IDE window assembly
    └── icons/               # UI Icons
        ├── folder.png       # Folder icon
        ├── file.png         # Generic file icon
        └── python.png       # Python file icon
```

---

## 📖 Usage

### Getting Started

1. **Launch PyIDE**: Run `python main.py`
2. **Open a File**:
   - Click `File → Open` or press `Ctrl+O`
   - Or double-click a file in the explorer
3. **Write Code**: Use the main editor with syntax highlighting
4. **Run Code**: Press `F5` or click the `▶ Run` button
5. **Debug**: Press `Shift+F5` for step-by-step debugging

### Working with Files

#### Creating New Files

```
File → New (Ctrl+N)
```

Opens a new untitled tab. Use `Save As` to give it a name.

#### Opening Projects

The file explorer shows your current working directory. Files are automatically filtered to show only relevant types.

#### Saving Work

```
File → Save (Ctrl+S)
File → Save As (Ctrl+Shift+S)
```

### Running Code

#### Method 1: No Input Required

```python
# Example
print("Hello, World!")
for i in range(5):
    print(f"Number: {i}")
```

Press `F5` → Output appears in the Output tab.

#### Method 2: With Input

```python
# Example
name = input("Your name: ")
age = input("Your age: ")
print(f"Hello {name}, you are {age} years old!")
```

Press `F5` → New terminal window opens for interaction.

### Managing Packages

1. Open: `Tools → Package Manager (pip)`
2. **To Install**:
   - Type package name (e.g., `requests`)
   - Click `📦 Install`
3. **To Uninstall**:
   - Select package from list
   - Click `🗑 Remove`

### Using Autocomplete

1. **Automatic Popup**:

   - Start typing: `pri`
   - Autocomplete appears after 2 characters
   - Use arrow keys to select `print`
   - Press `Enter` to insert

2. **Manual Trigger**:

   - Type partial word: `ma`
   - Press `Ctrl+Space`
   - Select from suggestions: `map`, `max`, `math`, etc.

3. **Module Names**:
   - Type: `im`
   - Press `Ctrl+Space`
   - Select: `import`, `importlib`, etc.

### Using Snippets

1. **Function Snippet**:

   ```python
   # Type: def
   # Press: Tab
   # Result:
   def function_name():
       pass
   ```

2. **Class Snippet**:

   ```python
   # Type: class
   # Press: Tab
   # Result:
   class ClassName:
       def __init__(self):
           pass
   ```

3. **Try-Except Snippet**:
   ```python
   # Type: try
   # Press: Tab
   # Result:
   try:
       pass
   except Exception as e:
       pass
   ```

### Using Find & Replace

1. **Basic Search**:

   - Press `Ctrl+F`
   - Type search term: `variable_name`
   - Press `F3` to find next
   - Press `Shift+F3` to find previous

2. **Replace Text**:

   - Press `Ctrl+F`
   - Find: `old_name`
   - Replace: `new_name`
   - Click `Replace` for single or `Replace All` for all

3. **Regex Search**:
   - Press `Ctrl+F`
   - Check `Regex` checkbox
   - Find: `def\s+\w+`
   - Finds all function definitions

### Using Minimap

1. **Quick Navigation**:

   - Look at minimap on right side
   - Click anywhere to jump to that line
   - Blue highlight shows current view

2. **Scroll with Minimap**:
   - Hover over minimap
   - Use mouse wheel to scroll
   - Main editor scrolls in sync

### Using Dynamic File Explorer

1. **Basic Operations**:

   - **Open File**: Double-click any file
   - **Refresh**: Click 🔄 button in header
   - **Auto-Refresh**: Files update automatically when changed

2. **Create New Items**:

   ```
   Right-click in explorer → 📄 New File
   Enter name: "config.py" → File created and appears instantly

   Right-click in explorer → 📁 New Folder
   Enter name: "utils" → Folder created
   ```

3. **Rename**:

   ```
   Right-click file → ✏️ Rename
   Change "old_name.py" to "new_name.py"
   Tree updates automatically
   ```

4. **Delete**:

   ```
   Right-click file/folder → 🗑️ Delete
   Confirm deletion (⚠️ Cannot be undone!)
   Item disappears from tree
   ```

5. **Show in System Explorer**:

   ```
   Right-click file → 📂 Show in Explorer
   Opens Windows Explorer/Finder/File Manager
   File is highlighted
   ```

6. **Auto-Refresh Examples**:
   - Create file externally → Appears in tree (500ms delay)
   - Delete from terminal → Disappears from tree
   - Rename outside IDE → Updates in tree

### Switching Themes

1. **Open Theme Menu**:

   - Click `🎨 Theme` in menu bar
   - See 8 available themes

2. **Apply Theme**:

   ```
   Theme → 🧛 Dracula → Instant purple theme
   Theme → 🌊 Nord → Instant blue/cyan theme
   Theme → 🐙 GitHub Dark → GitHub's official dark theme
   ```

3. **Theme Comparison**:
   - **Dracula**: Purple accents, great for night coding
   - **Nord**: Cool blues, professional look
   - **Monokai**: Green accents, Sublime Text classic
   - **One Dark**: Atom editor style
   - **Gruvbox**: Warm retro colors

### Using Git

1. Open: `Tools → Git Manager`
2. **Check Status**: Click `📊 Status`
3. **Make Commit**:
   - Click `➕ Add All`
   - Write commit message
   - Click `💾 Commit`
4. **Sync**:
   - `⬆ Push`: Upload to remote
   - `⬇ Pull`: Download from remote

### Debugging Code

1. Set up your code
2. Press `Shift+F5` or `Run → Debug Mode`
3. A terminal opens with pdb debugger
4. Use commands:
   - `n`: Next line
   - `s`: Step into
   - `c`: Continue
   - `p variable_name`: Check values

---

## 🏗️ Architecture & Design

### Code Structure

#### **1. Syntax Highlighter (`Pide` class)**

```python
class Pide(QSyntaxHighlighter):
```

- **Purpose**: Real-time code coloring
- **Technology**: `QSyntaxHighlighter` + `QRegExp`
- **Features**:
  - Pattern matching for keywords
  - Dynamic module loading via `importlib`
  - Function validation via `hasattr`
  - Caching for performance

#### **2. Code Editor (`ModernCodeEditor` class)**

```python
class ModernCodeEditor(QPlainTextEdit):
```

- **Purpose**: Main text editing widget
- **Technology**: `QPlainTextEdit` with custom painting
- **Features**:
  - Custom line number area + minimap
  - Error line highlighting
  - Auto-indentation and auto-pairing
  - Autocomplete with `QCompleter`
  - Snippet expansion system
  - Signal/slot connections

#### **3. Line Numbers (`LineNumberArea` class)**

```python
class LineNumberArea(QWidget):
```

- **Purpose**: Display line numbers
- **Technology**: Custom `paintEvent` with `QPainter`
- **Features**:
  - Dynamic width calculation
  - Synchronized scrolling
  - Custom styling

#### **4. Minimap (`Minimap` class)**

```python
class Minimap(QWidget):
```

- **Purpose**: Code overview and quick navigation
- **Technology**: Custom painting with line density visualization
- **Features**:
  - 120px fixed-width sidebar
  - Click-to-jump navigation
  - Visible area indicator
  - Real-time updates

#### **5. Find & Replace Dialog (`FindReplaceDialog` class)**

```python
class FindReplaceDialog(QDialog):
```

- **Purpose**: Search and text replacement
- **Technology**: `QTextDocument` find with regex
- **Features**:
  - Case-sensitive/whole-word options
  - Regex pattern matching
  - Replace single/all
  - Modeless dialog

#### **6. Terminal Widget (`TerminalWidget` class)**

```python
class TerminalWidget(QWidget):
```

- **Purpose**: Embedded terminal
- **Technology**: `QProcess` for process management
- **Features**:
  - Real-time I/O streaming
  - Command input field
  - Color-coded output

#### **7. Main IDE Window (`ModernPythonIDE` class)**

```python
class ModernPythonIDE(QMainWindow):
```

- **Purpose**: Main application window
- **Technology**: `QMainWindow` with splitters
- **Layout**:
  - Left: File explorer
  - Center: Tabbed editor
  - Bottom: Output/Terminal tabs
  - Top: Menu + Toolbar

### Design Patterns Used

1. **Model-View Pattern**: Separate data (code) from presentation (highlighting)
2. **Observer Pattern**: Signal/slot connections for events + `QFileSystemWatcher`
3. **Factory Pattern**: Dynamic widget creation for tabs
4. **Singleton Pattern**: Single IDE instance
5. **Strategy Pattern**: Different run modes (console vs terminal)
6. **Command Pattern**: Context menu actions (New File, Delete, Rename)
7. **Decorator Pattern**: Debounced refresh with QTimer wrapper

---

## 👨‍💻 Author & Credits

**Developed and Maintained by:**
### Mert Ulupınar

This IDE was crafted to provide an elegant, lightweight, and powerful Python development experience.

---

<div align="center">
  <i>"Code is poetry, written with logic."</i><br><br>
  Built with ❤️ by Mert Ulupınar
</div>
---

## 🔧 Key Technologies

### PyQt5 Components

| Component            | Purpose               | Why                        |
| -------------------- | --------------------- | -------------------------- |
| `QMainWindow`        | Main window container | Professional app structure |
| `QPlainTextEdit`     | Code editor           | Efficient for large text   |
| `QSyntaxHighlighter` | Syntax coloring       | Real-time pattern matching |
| `QTreeWidget`        | File explorer         | Hierarchical data display  |
| `QTabWidget`         | Multi-file tabs       | Document management        |
| `QSplitter`          | Resizable panels      | Flexible layout            |
| `QProcess`           | External processes    | Terminal & code execution  |
| `QPainter`           | Custom drawing        | Line numbers & minimap     |
| `QTextEdit`          | Output console        | Rich text support          |
| `QFileSystemWatcher` | File monitoring       | Auto-refresh explorer      |
| `QMenu`              | Context menus         | Right-click actions        |
| `QCompleter`         | Autocomplete          | Code completion            |

### Python Standard Library

| Module       | Purpose                        |
| ------------ | ------------------------------ |
| `subprocess` | Execute Python code & commands |
| `ast`        | Parse code for imports         |
| `importlib`  | Dynamic module loading         |
| `tempfile`   | Temporary file handling        |
| `re`         | Regex for error parsing        |
| `os`         | File system operations         |

---

## ⌨️ Keyboard Shortcuts

### File Operations

| Shortcut       | Action           |
| -------------- | ---------------- |
| `Ctrl+N`       | New file         |
| `Ctrl+O`       | Open file        |
| `Ctrl+S`       | Save file        |
| `Ctrl+Shift+S` | Save as          |
| `Ctrl+Q`       | Quit application |

### Code Editing

| Shortcut     | Action                            |
| ------------ | --------------------------------- |
| `Ctrl+Space` | Show autocomplete suggestions     |
| `Ctrl+F`     | Open Find & Replace dialog        |
| `F3`         | Find next                         |
| `Shift+F3`   | Find previous                     |
| `Tab`        | Insert 4 spaces OR expand snippet |
| `Enter`      | Auto-indent                       |

### Code Execution

| Shortcut   | Action           |
| ---------- | ---------------- |
| `F5`       | Run Python file  |
| `Shift+F5` | Debug mode (pdb) |

---

## 📸 Screenshots

### Main Interface with Minimap

```
┌─────────────────────────────────────────────────────────────┐
│  File  Edit  Run  Tools  Theme                             │
├──────────┬────────────────────────────────────────┬─────────┤
│          │  1  def greet(name):                   │ ▓▓▓▓▓   │
│ Explorer │  2      return f"Hello, {name}!"       │ ▓▓▓▓▓   │
│          │  3                                     │         │
│ 📁 Proj  │  4  # Type 'def' + Tab for snippet    │ ▓▓▓▓▓▓  │
│  └ 🐍.py │  5  result = greet("World")            │ ▓▓▓▓▓   │
│  └ 📄.md │  6  print(result)    # Ctrl+Space ↓    │ ▓▓▓▓    │
│          │  7  ┌──────────────┐                   │ ▓▓▓▓    │
│          │  8  │ print        │                   │         │
│          │  9  │ property     │← Autocomplete     │ [----]  │
│          │ 10  │ pow          │                   │ Visible │
│          │     └──────────────┘                   │  Area   │
├──────────┴────────────────────────────────────────┴─────────┤
│ Output │ Terminal                                            │
│ > Running Python code...                                    │
│ > Hello, World!                                             │
└─────────────────────────────────────────────────────────────┘
```

### Find & Replace Dialog

```
┌─────────────────────────────────────────────────┐
│  Find & Replace                             × │
├─────────────────────────────────────────────────┤
│  Find:    [old_variable_name          ]        │
│  Replace: [new_variable_name          ]        │
│                                                 │
│  ☑ Case sensitive  ☐ Whole word  ☐ Regex       │
│                                                 │
│  [⬇ Find Next] [⬆ Find Previous]               │
│  [Replace]     [Replace All]                   │
│                                                 │
│  ✓ Found                                        │
└─────────────────────────────────────────────────┘
```

### Snippet Expansion

```
Before:           After pressing Tab:
────────          ─────────────────────
class|            class ClassName:
                      def __init__(self):
                          pass|


def|              def function_name():
                      pass|


try|              try:
                      pass
                  except Exception as e:
                      pass|
```

### Dynamic File Explorer with Context Menu

```
┌─────────────────────────┐
│ EXPLORER          🔄    │  ← Refresh button
├─────────────────────────┤
│ 📁 MyProject           │
│   ├─ 🐍 main.py        │  ← Right-click here
│   ├─ 📄 README.md      │     ┌──────────────────────┐
│   ├─ 📁 utils          │     │ 📄 New File          │
│   │  └─ 🐍 helper.py   │     │ 📁 New Folder        │
│   └─ 📁 tests          │     ├──────────────────────┤
│                         │     │ ✏️ Rename             │
│  Auto-refresh: ON ✓    │     │ 🗑️ Delete            │
│  Watcher: Active 👁️    │     ├──────────────────────┤
└─────────────────────────┘     │ 📂 Show in Explorer  │
                                 └──────────────────────┘
```

### Theme Gallery

```
⚫ Default (VS Code)    🧛 Dracula             🌊 Nord
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ #1e1e1e          │   │ #282a36          │   │ #2e3440          │
│   Blue accent    │   │   Purple accent  │   │   Cyan accent    │
│   Professional   │   │   Night coding   │   │   Arctic calm    │
└──────────────────┘   └──────────────────┘   └──────────────────┘

🌙 Monokai            ☀️ Solarized          🔵 One Dark
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ #272822          │   │ #002b36          │   │ #282c34          │
│   Green accent   │   │   Yellow accent  │   │   Green accent   │
│   Sublime Text   │   │   Eye comfort    │   │   Atom editor    │
└──────────────────┘   └──────────────────┘   └──────────────────┘

🐙 GitHub Dark        🟤 Gruvbox
┌──────────────────┐   ┌──────────────────┐
│ #0d1117          │   │ #282828          │
│   Orange accent  │   │   Yellow accent  │
│   GitHub style   │   │   Retro warm     │
└──────────────────┘   └──────────────────┘
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Feature Ideas

Completed ✅:

- [x] Code completion (autocomplete) - **Ctrl+Space**
- [x] Find & Replace (Ctrl+F) - **With regex support**
- [x] Code snippets - **Tab expansion**
- [x] Minimap - **120px sidebar overview**
- [x] Dynamic file explorer - **Real-time updates with QFileSystemWatcher**
- [x] Context menu - **New File/Folder, Rename, Delete, Show in Explorer**
- [x] 7 Professional themes - **Dracula, Nord, Monokai, Solarized, One Dark, GitHub, Gruvbox**

Planned 📋:

- [ ] Multi-cursor support (Ctrl+Click)
- [ ] Code folding (collapse functions/classes)
- [ ] Plugin system
- [ ] Integrated linter (pylint/flake8)
- [ ] Code formatter (Black/autopep8)
- [ ] Virtual environment management
- [ ] Jupyter notebook support
- [ ] Bracket matching highlighter
- [ ] TODO/FIXME comment scanner
- [ ] Project templates

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Mert Ulupınar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

- **PyQt5**: For the amazing GUI framework
- **Python**: For being an incredible language
- **VS Code**: UI/UX inspiration
- **Dracula Theme**: Beautiful color palette
- **Nord Theme**: Arctic-inspired colors
- **The Python Community**: For continuous support and inspiration

---

<div align="center">

### 🌟 If you like PyIDE, give it a star! ⭐

[![GitHub](https://img.shields.io/badge/GitHub-mertulupinar-black?style=flat&logo=github)](https://github.com/mertulupinar)
[![Python](https://img.shields.io/badge/Python-Powered-blue?style=flat&logo=python)](https://python.org)

_Happy Coding! 🚀_

</div>
