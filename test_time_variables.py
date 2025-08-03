#!/usr/bin/env python3
"""
测试时间变量功能
Test script for the new time variable functionality
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.patrol import PatrolEngine, PatrolTask, PatrolCheck, PatrolType, PatrolFrequency
from core.variables import VariableManager


async def test_time_variables():
    """Test time variable generation during patrol execution"""
    print("🧪 测试时间变量功能...")
    
    # Initialize patrol engine
    engine = PatrolEngine()
    variable_manager = engine.variable_manager
    
    # Create a simple test task
    task = PatrolTask(
        name="时间测试任务",
        description="测试时间变量生成",
        websites=["https://httpbin.org/status/200"],  # Simple test endpoint
        frequency=PatrolFrequency.DAILY,
        generate_report=False,  # Disable report generation for test
        timeout=10
    )
    
    # Add a simple content check
    check = PatrolCheck(
        name="状态检查",
        type=PatrolType.CONTENT_CHECK,
        target="body",
        description="检查页面内容"
    )
    task.checks.append(check)
    
    print(f"📋 创建测试任务: {task.name}")
    engine.add_patrol_task(task)
    
    # Execute patrol task
    print("⚡ 开始执行巡检任务...")
    try:
        results = await engine.execute_patrol_task(task.name)
        print(f"✅ 巡检任务完成，检查了 {len(results)} 个网站")
    except Exception as e:
        print(f"❌ 巡检任务执行失败: {e}")
        return False
    
    # Check if time variables were generated
    print("\n🕐 检查时间变量是否已生成...")
    safe_task_name = task.name.replace(' ', '_').replace('-', '_')
    
    expected_time_vars = [
        f"patrol_time_{safe_task_name}",
        f"patrol_time_formatted_{safe_task_name}",
        f"patrol_date_{safe_task_name}",
        f"patrol_datetime_{safe_task_name}"
    ]
    
    success = True
    for var_name in expected_time_vars:
        value = variable_manager.get_variable(var_name)
        if value:
            print(f"  ✅ {var_name}: {value}")
        else:
            print(f"  ❌ {var_name}: 未找到")
            success = False
    
    # Show all available variables
    print(f"\n📊 所有可用变量 ({variable_manager.get_variable_count()} 个):")
    all_vars = variable_manager.get_all_variables_with_metadata()
    for var_name, var_data in all_vars.items():
        var_type = var_data['metadata'].get('type', 'unknown')
        var_desc = var_data['metadata'].get('description', '')
        print(f"  🏷️ {var_name} ({var_type}): {var_desc}")
    
    # Test variable substitution
    print(f"\n🔄 测试变量替换...")
    test_text = f"巡检报告 - 执行时间: ${{patrol_time_formatted_{safe_task_name}}}"
    substituted = variable_manager.substitute_variables(test_text)
    print(f"  原始文本: {test_text}")
    print(f"  替换后: {substituted}")
    
    return success


def test_variable_formats():
    """Test different time format variables"""
    print("\n📅 测试时间格式变量...")
    
    vm = VariableManager()
    test_time = datetime.now()
    
    # Test different time formats
    formats = {
        "简单时间": test_time.strftime("%H:%M:%S"),
        "完整格式": test_time.strftime("%Y年%m月%d日 %H:%M:%S"),
        "ISO日期": test_time.strftime("%Y-%m-%d"),
        "ISO日期时间": test_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for name, formatted_time in formats.items():
        vm.set_variable(f"test_{name}", formatted_time, "text", f"测试时间格式: {name}")
        print(f"  ✅ {name}: {formatted_time}")
    
    # Test substitution
    test_text = "报告生成于: ${test_完整格式}"
    result = vm.substitute_variables(test_text)
    print(f"\n  📝 替换测试: {test_text} → {result}")
    
    return True


async def main():
    """Main test function"""
    print("🚀 开始测试时间变量功能\n")
    
    # Test 1: Variable formats
    success1 = test_variable_formats()
    
    # Test 2: Patrol execution with time variables
    success2 = await test_time_variables()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！时间变量功能正常工作。")
        return True
    else:
        print("\n❌ 某些测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)