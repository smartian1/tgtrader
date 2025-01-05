from typing import Dict, List, Tuple, Type, Any
from peewee import Model, Field
import inspect
import ast
from dataclasses import dataclass


@dataclass
class FieldInfo:
    """Field information container for model inspection.
    
    Attributes:
        name: Field name
        field_type: Field type in database
        comment: Field comment from source code
        python_type: Python type annotation if available
    """
    name: str
    field_type: str
    comment: str
    python_type: str = ""


def get_model_info(model_class: Type[Model]) -> Tuple[str, List[FieldInfo]]:
    """Extract table name and field information from a Peewee Model class.
    
    Args:
        model_class: A Peewee Model class to inspect
        
    Returns:
        A tuple containing:
            - table_name (str): The name of the database table
            - fields (List[FieldInfo]): List of field information including name, type and comments
    """
    # Get table name
    table_name = model_class._meta.table_name
    
    # Get source code of both the class and its parent class
    field_comments: Dict[str, str] = {}
    
    # Check parent classes for field comments
    for cls in model_class.__mro__:
        if cls == Model or cls == object:
            continue
            
        try:
            source = inspect.getsource(cls)
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # Try to get line comments
                            if (hasattr(node, 'lineno') and 
                                node.lineno > 1 and 
                                isinstance(node.value, ast.Call)):
                                
                                prev_line = source.split('\n')[node.lineno - 2]
                                if '#' in prev_line:
                                    comment = prev_line.split('#')[1].strip()
                                    field_comments[target.id] = comment
                                    continue

                            # Try to get docstring
                            if hasattr(node, 'parent') and isinstance(node.parent, ast.ClassDef):
                                class_body = node.parent.body
                                for stmt in class_body:
                                    if (isinstance(stmt, ast.Expr) and 
                                        isinstance(stmt.value, ast.Str) and 
                                        stmt.lineno == node.lineno - 1):
                                        field_comments[target.id] = stmt.value.s.strip()
                                        
        except (IOError, TypeError):
            continue

    # Get field information
    fields: List[FieldInfo] = []
    for field_name, field_obj in model_class._meta.fields.items():
        field_type = type(field_obj).__name__.replace('Field', '')
        
        # Try to get docstring from field object
        field_doc = getattr(field_obj, '__doc__', '')
        comment = field_comments.get(field_name, '') or field_doc

        fields.append(FieldInfo(
            name=field_name,
            field_type=field_type,
            comment=comment
        ))

    return table_name, fields


def print_model_info(model_class: Type[Model]) -> None:
    """Print table name and field information from a Peewee Model class in a formatted way.
    
    Args:
        model_class: A Peewee Model class to inspect
    """
    table_name, fields = get_model_info(model_class)
    print(f"Table: {table_name}")
    print("Fields:")
    for field in fields:
        print(f"  {field.name}: {field.field_type} # {field.comment}")

