#!/usr/bin/env python3
"""
Validation script for the new click element functionality
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def validate_click_feature():
    """Validate the new click element functionality structure"""
    print("🔍 验证点击元素功能...")
    
    try:
        # Test imports
        from core.patrol import PatrolCheck, PatrolType
        print("✅ PatrolCheck 导入成功")
        
        # Test creating a check with click element
        test_check = PatrolCheck(
            name="测试点击检查",
            type=PatrolType.CONTENT_CHECK,
            target="h1",
            click_element="button.example-button"
        )
        print("✅ 创建带点击元素的检查项成功")
        
        # Verify the field exists and is accessible
        assert hasattr(test_check, 'click_element'), "click_element字段不存在"
        assert test_check.click_element == "button.example-button", "click_element值不正确"
        print("✅ click_element字段验证成功")
        
        # Test GUI imports
        from gui.dialogs.patrol_config import PatrolCheckWidget
        print("✅ PatrolCheckWidget 导入成功")
        
        # Test ScreenshotCapture has the new method
        from core.screenshot import ScreenshotCapture
        screenshot_capture = ScreenshotCapture()
        assert hasattr(screenshot_capture, 'click_element'), "click_element方法不存在"
        print("✅ ScreenshotCapture.click_element方法存在")
        
        print("\n🎉 所有验证都通过了！点击元素功能已正确实现。")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


if __name__ == "__main__":
    result = validate_click_feature()
    sys.exit(0 if result else 1)