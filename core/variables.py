"""
Variable management system for storing and retrieving monitoring data
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
import json
from pathlib import Path


class VariableManager:
    """Manages variables collected during monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._variables: Dict[str, Any] = {}
        self._variable_metadata: Dict[str, Dict[str, Any]] = {}
    
    def set_variable(self, name: str, value: Any, variable_type: str = "auto", description: str = "") -> None:
        """Set a variable value"""
        try:
            # Auto-detect type if not specified
            if variable_type == "auto":
                if isinstance(value, str) and (value.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))):
                    variable_type = "image"
                elif isinstance(value, str) and Path(value).exists():
                    variable_type = "file"
                elif isinstance(value, (int, float)):
                    variable_type = "number"
                elif isinstance(value, bool):
                    variable_type = "boolean"
                else:
                    variable_type = "text"
            
            self._variables[name] = value
            self._variable_metadata[name] = {
                'type': variable_type,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.logger.debug(f"Set variable '{name}' = '{value}' (type: {variable_type})")
            
        except Exception as e:
            self.logger.error(f"Failed to set variable '{name}': {e}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value"""
        return self._variables.get(name, default)
    
    def get_variable_with_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get variable value with metadata"""
        if name not in self._variables:
            return None
        
        return {
            'name': name,
            'value': self._variables[name],
            'metadata': self._variable_metadata.get(name, {})
        }
    
    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables"""
        return self._variables.copy()
    
    def get_all_variables_with_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get all variables with their metadata"""
        result = {}
        for name, value in self._variables.items():
            result[name] = {
                'value': value,
                'metadata': self._variable_metadata.get(name, {})
            }
        return result
    
    def update_variable(self, name: str, value: Any) -> None:
        """Update an existing variable value"""
        if name in self._variables:
            self._variables[name] = value
            if name in self._variable_metadata:
                self._variable_metadata[name]['updated_at'] = datetime.now().isoformat()
            self.logger.debug(f"Updated variable '{name}' = '{value}'")
        else:
            self.logger.warning(f"Variable '{name}' does not exist, creating new one")
            self.set_variable(name, value)
    
    def delete_variable(self, name: str) -> bool:
        """Delete a variable"""
        if name in self._variables:
            del self._variables[name]
            if name in self._variable_metadata:
                del self._variable_metadata[name]
            self.logger.debug(f"Deleted variable '{name}'")
            return True
        return False
    
    def clear_variables(self) -> None:
        """Clear all variables"""
        self._variables.clear()
        self._variable_metadata.clear()
        self.logger.info("Cleared all variables")
    
    def get_variables_by_type(self, variable_type: str) -> Dict[str, Any]:
        """Get all variables of a specific type"""
        result = {}
        for name, value in self._variables.items():
            metadata = self._variable_metadata.get(name, {})
            if metadata.get('type') == variable_type:
                result[name] = value
        return result
    
    def get_image_variables(self) -> Dict[str, str]:
        """Get all image variables (screenshots, etc.)"""
        return self.get_variables_by_type("image")
    
    def get_file_variables(self) -> Dict[str, str]:
        """Get all file variables (downloads, etc.)"""
        return self.get_variables_by_type("file")
    
    def get_text_variables(self) -> Dict[str, str]:
        """Get all text variables"""
        return self.get_variables_by_type("text")
    
    def get_number_variables(self) -> Dict[str, float]:
        """Get all number variables"""
        return self.get_variables_by_type("number")
    
    def variable_exists(self, name: str) -> bool:
        """Check if a variable exists"""
        return name in self._variables
    
    def get_variable_names(self) -> list:
        """Get list of all variable names"""
        return list(self._variables.keys())
    
    def get_variable_count(self) -> int:
        """Get total number of variables"""
        return len(self._variables)
    
    def export_variables(self, file_path: str) -> None:
        """Export variables to JSON file"""
        try:
            export_data = {
                'variables': self._variables,
                'metadata': self._variable_metadata,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported variables to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export variables: {e}")
    
    def import_variables(self, file_path: str, overwrite: bool = False) -> None:
        """Import variables from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            variables = import_data.get('variables', {})
            metadata = import_data.get('metadata', {})
            
            for name, value in variables.items():
                if not overwrite and name in self._variables:
                    self.logger.warning(f"Variable '{name}' already exists, skipping")
                    continue
                
                self._variables[name] = value
                if name in metadata:
                    self._variable_metadata[name] = metadata[name]
            
            self.logger.info(f"Imported variables from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to import variables: {e}")
    
    def substitute_variables(self, text: str) -> str:
        """Substitute variable placeholders in text with actual values"""
        try:
            result = text
            
            # Find all variable references in format ${variable_name}
            import re
            pattern = r'\$\{([^}]+)\}'
            
            def replace_variable(match):
                var_name = match.group(1)
                var_value = self.get_variable(var_name)
                
                if var_value is not None:
                    return str(var_value)
                else:
                    self.logger.warning(f"Variable '{var_name}' not found, keeping placeholder")
                    return match.group(0)  # Keep original placeholder
            
            result = re.sub(pattern, replace_variable, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to substitute variables in text: {e}")
            return text
    
    def get_variable_summary(self) -> Dict[str, Any]:
        """Get a summary of variables"""
        type_counts = {}
        for metadata in self._variable_metadata.values():
            var_type = metadata.get('type', 'unknown')
            type_counts[var_type] = type_counts.get(var_type, 0) + 1
        
        return {
            'total_variables': len(self._variables),
            'by_type': type_counts,
            'variable_names': list(self._variables.keys())
        }