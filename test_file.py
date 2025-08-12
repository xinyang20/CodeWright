#!/usr/bin/env python3
"""
测试Python文件
这是一个用于测试文件上传功能的示例Python文件
"""

def hello_world():
    """打印Hello World"""
    print("Hello, World!")

def add_numbers(a, b):
    """计算两个数的和"""
    return a + b

def main():
    """主函数"""
    hello_world()
    result = add_numbers(10, 20)
    print(f"10 + 20 = {result}")

if __name__ == "__main__":
    main()
