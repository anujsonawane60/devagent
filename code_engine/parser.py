"""Code parsing using tree-sitter for AST extraction."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tree_sitter as ts
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts


@dataclass
class CodeEntity:
    """A parsed code entity (function, class, method, etc.)."""
    file_path: str
    name: str
    type: str  # function, class, method, component, import, route
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    signature: Optional[str] = None


@dataclass
class FileParseResult:
    """Result of parsing a single file."""
    file_path: str
    language: str
    entities: List[CodeEntity] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


# Pre-built languages
_PY_LANG = ts.Language(tspython.language())
_JS_LANG = ts.Language(tsjs.language())
_TS_LANG = ts.Language(tsts.language_typescript())
_TSX_LANG = ts.Language(tsts.language_tsx())

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".cache", "env",
}


class CodeParser:
    """Parses source code files into structured entities using tree-sitter."""

    def __init__(self):
        self._parsers = {
            "python": ts.Parser(_PY_LANG),
            "javascript": ts.Parser(_JS_LANG),
            "typescript_ts": ts.Parser(_TS_LANG),
            "typescript_tsx": ts.Parser(_TSX_LANG),
        }

    def parse_file(self, path: str) -> Optional[FileParseResult]:
        """Parse a file and return structured entities. Returns None for unsupported files."""
        ext = Path(path).suffix.lower()
        language = EXTENSION_MAP.get(ext)
        if not language:
            return None

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, IOError):
            return None

        if language == "python":
            return self.parse_python(source, path)
        elif language == "javascript":
            return self.parse_javascript(source, path)
        elif language == "typescript":
            return self.parse_typescript(source, path)
        return None

    def parse_python(self, source: str, path: str) -> FileParseResult:
        """Parse Python source code."""
        result = FileParseResult(file_path=path, language="python")
        tree = self._parsers["python"].parse(source.encode("utf-8"))
        root = tree.root_node

        for node in root.children:
            if node.type == "function_definition":
                entity = self._extract_python_function(node, path)
                result.entities.append(entity)
            elif node.type == "class_definition":
                result.entities.extend(self._extract_python_class(node, path))
            elif node.type == "decorated_definition":
                decorated = self._get_decorated_node(node)
                if decorated and decorated.type == "function_definition":
                    entity = self._extract_python_function(decorated, path)
                    result.entities.append(entity)
                elif decorated and decorated.type == "class_definition":
                    result.entities.extend(self._extract_python_class(decorated, path))
            elif node.type in ("import_statement", "import_from_statement"):
                result.imports.append(node.text.decode("utf-8"))

        return result

    def parse_javascript(self, source: str, path: str) -> FileParseResult:
        """Parse JavaScript source code."""
        result = FileParseResult(file_path=path, language="javascript")
        tree = self._parsers["javascript"].parse(source.encode("utf-8"))
        self._extract_js_ts_nodes(tree.root_node, path, result)
        return result

    def parse_typescript(self, source: str, path: str) -> FileParseResult:
        """Parse TypeScript/TSX source code."""
        result = FileParseResult(file_path=path, language="typescript")
        ext = Path(path).suffix.lower()
        parser_key = "typescript_tsx" if ext == ".tsx" else "typescript_ts"
        tree = self._parsers[parser_key].parse(source.encode("utf-8"))
        self._extract_js_ts_nodes(tree.root_node, path, result)
        return result

    def parse_project(self, project_path: str) -> List[FileParseResult]:
        """Walk a project directory and parse all supported files."""
        results = []
        root = Path(project_path)
        if not root.is_dir():
            return results

        for dirpath, dirnames, filenames in os.walk(root):
            # Skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                parsed = self.parse_file(full_path)
                if parsed:
                    results.append(parsed)
        return results

    # --- Python helpers ---

    def _extract_python_function(self, node, path: str) -> CodeEntity:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        return_node = node.child_by_field_name("return_type")
        name = name_node.text.decode("utf-8") if name_node else "<unknown>"

        sig = f"def {name}"
        if params_node:
            sig += params_node.text.decode("utf-8")
        if return_node:
            sig += f" -> {return_node.text.decode('utf-8')}"

        docstring = self._get_python_docstring(node)

        return CodeEntity(
            file_path=path,
            name=name,
            type="function",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=sig,
            docstring=docstring,
        )

    def _extract_python_class(self, node, path: str) -> List[CodeEntity]:
        entities = []
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode("utf-8") if name_node else "<unknown>"
        docstring = self._get_python_docstring(node)

        # Gather superclasses for signature
        superclasses = node.child_by_field_name("superclasses")
        sig = f"class {name}"
        if superclasses:
            sig += superclasses.text.decode("utf-8")

        entities.append(CodeEntity(
            file_path=path,
            name=name,
            type="class",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=sig,
            docstring=docstring,
        ))

        # Extract methods
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                func_node = None
                if child.type == "function_definition":
                    func_node = child
                elif child.type == "decorated_definition":
                    func_node = self._get_decorated_node(child)
                    if func_node and func_node.type != "function_definition":
                        func_node = None

                if func_node:
                    method = self._extract_python_function(func_node, path)
                    method.type = "method"
                    entities.append(method)

        return entities

    def _get_python_docstring(self, node) -> Optional[str]:
        body = node.child_by_field_name("body")
        if not body or not body.children:
            return None
        first = body.children[0]
        if first.type == "expression_statement" and first.children:
            expr = first.children[0]
            if expr.type == "string":
                text = expr.text.decode("utf-8")
                # Strip triple quotes
                for q in ('"""', "'''"):
                    if text.startswith(q) and text.endswith(q):
                        return text[3:-3].strip()
                return text.strip("\"'").strip()
        return None

    def _get_decorated_node(self, node):
        """Get the actual definition from a decorated_definition node."""
        for child in node.children:
            if child.type in ("function_definition", "class_definition"):
                return child
        return None

    # --- JS/TS helpers ---

    def _extract_js_ts_nodes(self, root, path: str, result: FileParseResult):
        """Extract entities from JS/TS AST."""
        for node in root.children:
            if node.type == "function_declaration":
                entity = self._extract_js_function(node, path)
                result.entities.append(entity)
            elif node.type == "lexical_declaration":
                entities = self._extract_js_lexical(node, path)
                result.entities.extend(entities)
            elif node.type == "export_statement":
                self._extract_js_export(node, path, result)
            elif node.type == "import_statement":
                result.imports.append(node.text.decode("utf-8"))
            elif node.type == "interface_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    result.entities.append(CodeEntity(
                        file_path=path,
                        name=name_node.text.decode("utf-8"),
                        type="class",
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        signature=f"interface {name_node.text.decode('utf-8')}",
                    ))

    def _extract_js_function(self, node, path: str) -> CodeEntity:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        name = name_node.text.decode("utf-8") if name_node else "<unknown>"

        sig = f"function {name}"
        if params_node:
            sig += params_node.text.decode("utf-8")

        # Detect React components (capitalized name + JSX return)
        entity_type = "component" if name[0].isupper() else "function"

        return CodeEntity(
            file_path=path,
            name=name,
            type=entity_type,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            signature=sig,
        )

    def _extract_js_lexical(self, node, path: str) -> List[CodeEntity]:
        """Extract entities from const/let declarations."""
        entities = []
        for child in node.named_children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")
                if not name_node or not value_node:
                    continue
                name = name_node.text.decode("utf-8")
                if value_node.type == "arrow_function":
                    entity_type = "component" if name[0].isupper() else "function"
                    sig = f"const {name} = "
                    params = value_node.child_by_field_name("parameters")
                    if params:
                        sig += params.text.decode("utf-8")
                    else:
                        # single param without parens
                        sig += f"({value_node.children[0].text.decode('utf-8')})"
                    sig += " => ..."
                    entities.append(CodeEntity(
                        file_path=path,
                        name=name,
                        type=entity_type,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        signature=sig,
                    ))
        return entities

    def _extract_js_export(self, node, path: str, result: FileParseResult):
        """Extract entities from export statements."""
        for child in node.named_children:
            if child.type == "function_declaration":
                entity = self._extract_js_function(child, path)
                result.entities.append(entity)
                result.exports.append(entity.name)
            elif child.type == "lexical_declaration":
                entities = self._extract_js_lexical(child, path)
                result.entities.extend(entities)
                for e in entities:
                    result.exports.append(e.name)
