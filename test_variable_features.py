#!/usr/bin/env python3
"""
Test script for the new variable functionality in Word editor
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_variable_manager():
    """Test the basic variable manager functionality"""
    try:
        from core.variables import VariableManager
        
        vm = VariableManager()
        
        # Test setting variables
        vm.set_variable('test_text', 'Hello World', 'text', 'Test text variable')
        vm.set_variable('test_number', 42, 'number', 'Test number variable')
        vm.set_variable('test_image', '/path/to/screenshot.png', 'image', 'Test image variable')
        
        # Test variable substitution
        text_with_vars = "检查结果: ${test_text}, 数量: ${test_number}, 截图: ${test_image}"
        substituted = vm.substitute_variables(text_with_vars)
        
        print("✅ Variable Manager Test:")
        print(f"   Original: {text_with_vars}")
        print(f"   Substituted: {substituted}")
        
        # Test getting variables with metadata
        all_vars = vm.get_all_variables_with_metadata()
        print(f"   Total variables: {len(all_vars)}")
        
        for var_name, var_info in all_vars.items():
            var_type = var_info.get('metadata', {}).get('type', 'unknown')
            print(f"   - {var_name} ({var_type}): {var_info['value']}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Variable Manager Error: {e}")
        return False

def test_patrol_result_simulation():
    """Simulate patrol results and test variable creation"""
    try:
        from core.variables import VariableManager
        
        vm = VariableManager()
        
        # Simulate patrol results data
        mock_results = [
            {
                'task_name': '主网站巡检',
                'website_url': 'https://example.com',
                'screenshot_path': '/reports/screenshots/example_com_20250102_143052.png',
                'check_results': {
                    '用户数量检查': {
                        'extracted_value': '1,234 用户',
                        'success': True
                    },
                    '页面标题检查': {
                        'extracted_value': '主页 - 示例网站',
                        'success': True
                    }
                },
                'extracted_data': {
                    'active_users': 1234,
                    'page_load_time': '2.5秒'
                }
            }
        ]
        
        # Simulate variable population from results
        for result in mock_results:
            safe_task_name = "".join(c for c in result['task_name'] if c.isalnum() or c in ('_',))
            safe_url = result['website_url'].replace("://", "_").replace("/", "_").replace(".", "_").replace(":", "_")
            
            # Screenshot variable
            if result.get('screenshot_path'):
                var_name = f"screenshot_{safe_task_name}_{safe_url}"
                vm.set_variable(var_name, result['screenshot_path'], "image", f"页面截图来源: {result['website_url']}")
            
            # Extracted values
            if result.get('check_results'):
                for check_name, check_result in result['check_results'].items():
                    if check_result.get('extracted_value'):
                        safe_check_name = "".join(c for c in check_name if c.isalnum() or c in ('_',))
                        var_name = f"extracted_{safe_check_name}_{safe_task_name}"
                        vm.set_variable(var_name, check_result['extracted_value'], "text", f"提取值来源: {check_name}")
            
            # Other data
            if result.get('extracted_data'):
                for key, value in result['extracted_data'].items():
                    safe_key = "".join(c for c in key if c.isalnum() or c in ('_',))
                    var_name = f"data_{safe_key}_{safe_task_name}"
                    vm.set_variable(var_name, value, "auto", f"数据来源: {result['website_url']}")
        
        print("\n✅ Patrol Result Variables Test:")
        all_vars = vm.get_all_variables_with_metadata()
        for var_name, var_info in all_vars.items():
            var_type = var_info.get('metadata', {}).get('type', 'unknown')
            description = var_info.get('metadata', {}).get('description', '')
            print(f"   - ${{{var_name}}} ({var_type}): {var_info['value']}")
            print(f"     描述: {description}")
        
        # Test variable substitution in report template
        template_text = """
巡检报告摘要:

网站截图: ${screenshot_主网站巡检_https___example_com}
用户数量: ${extracted_用户数量检查_主网站巡检}
页面标题: ${extracted_页面标题检查_主网站巡检}
活跃用户: ${data_active_users_主网站巡检}
加载时间: ${data_page_load_time_主网站巡检}
""".strip()
        
        substituted_template = vm.substitute_variables(template_text)
        
        print("\n✅ Template Substitution Test:")
        print("   原始模板:")
        for line in template_text.split('\n'):
            print(f"     {line}")
        print("\n   替换后:")
        for line in substituted_template.split('\n'):
            print(f"     {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Patrol Result Test Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Variable Features for Word Editor\n")
    
    all_passed = True
    
    # Test basic variable manager
    all_passed &= test_variable_manager()
    
    # Test patrol result variable creation
    all_passed &= test_patrol_result_simulation()
    
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed!'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())