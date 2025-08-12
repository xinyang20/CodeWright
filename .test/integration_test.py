#!/usr/bin/env python3
"""
CodeWright 集成测试脚本
"""
import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8001/api/v1"

class CodeWrightTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.project_id = None
        self.file_id = None
        
    def test_user_registration(self):
        """测试用户注册"""
        print("🔧 测试用户注册...")
        
        data = {
            "username": f"testuser_{int(time.time())}",
            "password": "123456"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/register", json=data)
        result = response.json()
        
        assert result["code"] == 0, f"注册失败: {result['message']}"
        print(f"✅ 用户注册成功: {data['username']}")
        
        return data["username"]
    
    def test_user_login(self, username):
        """测试用户登录"""
        print("🔧 测试用户登录...")
        
        data = {
            "username": username,
            "password": "123456"
        }
        
        response = self.session.post(f"{BASE_URL}/auth/token", json=data)
        result = response.json()
        
        assert result["code"] == 0, f"登录失败: {result['message']}"
        
        self.token = result["data"]["access_token"]
        self.user_id = result["data"]["user"]["id"]
        
        # 设置认证头
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        
        print(f"✅ 用户登录成功: {username}")
        
    def test_create_project(self):
        """测试创建项目"""
        print("🔧 测试创建项目...")
        
        data = {
            "project_name": f"测试项目_{int(time.time())}",
            "project_type": "code"
        }
        
        response = self.session.post(f"{BASE_URL}/projects", json=data)
        result = response.json()
        
        assert result["code"] == 0, f"创建项目失败: {result['message']}"
        
        self.project_id = result["data"]["project_id"]
        print(f"✅ 项目创建成功: {data['project_name']} (ID: {self.project_id})")
        
    def test_upload_file(self):
        """测试文件上传"""
        print("🔧 测试文件上传...")
        
        # 创建测试文件
        test_content = '''#!/usr/bin/env python3
"""
测试Python文件
"""

def hello_world():
    """打印Hello World"""
    print("Hello, CodeWright!")

def calculate_sum(a, b):
    """计算两个数的和"""
    return a + b

def main():
    """主函数"""
    hello_world()
    result = calculate_sum(10, 20)
    print(f"10 + 20 = {result}")

if __name__ == "__main__":
    main()
'''
        
        test_file_path = Path("test_upload.py")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_upload.py', f, 'text/plain')}
                response = self.session.post(f"{BASE_URL}/files/upload", files=files)
            
            result = response.json()
            assert result["code"] == 0, f"文件上传失败: {result['message']}"
            
            self.file_id = result["data"]["file_id"]
            print(f"✅ 文件上传成功: test_upload.py (ID: {self.file_id})")
            
        finally:
            # 清理测试文件
            if test_file_path.exists():
                test_file_path.unlink()
    
    def test_add_file_to_project(self):
        """测试添加文件到项目"""
        print("🔧 测试添加文件到项目...")
        
        response = self.session.post(f"{BASE_URL}/projects/{self.project_id}/files/{self.file_id}")
        result = response.json()
        
        assert result["code"] == 0, f"添加文件到项目失败: {result['message']}"
        print(f"✅ 文件添加到项目成功")
        
    def test_preview_file(self):
        """测试文件预览"""
        print("🔧 测试文件预览...")
        
        response = self.session.get(f"{BASE_URL}/files/{self.file_id}/preview")
        result = response.json()
        
        assert result["code"] == 0, f"文件预览失败: {result['message']}"
        assert "highlighted_html" in result["data"], "预览结果缺少高亮HTML"
        
        print(f"✅ 文件预览成功: {result['data']['language']} 语言")
        
    def test_export_project(self):
        """测试项目导出"""
        print("🔧 测试项目导出...")
        
        response = self.session.post(f"{BASE_URL}/exports/projects/{self.project_id}/pdf")
        result = response.json()
        
        assert result["code"] == 0, f"项目导出失败: {result['message']}"
        
        export_id = result["data"]["export_id"]
        print(f"✅ 项目导出成功 (导出ID: {export_id})")
        
        return export_id
        
    def test_download_export(self, export_id):
        """测试下载导出文件"""
        print("🔧 测试下载导出文件...")
        
        response = self.session.get(f"{BASE_URL}/exports/download/{export_id}")
        
        assert response.status_code == 200, f"下载失败: {response.status_code}"
        assert len(response.content) > 0, "下载的文件为空"
        
        # 保存到测试目录
        download_path = Path(".test/downloaded_export.html")
        download_path.parent.mkdir(exist_ok=True)
        
        with open(download_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 导出文件下载成功: {download_path}")
        
    def test_get_project_files(self):
        """测试获取项目文件列表"""
        print("🔧 测试获取项目文件列表...")
        
        response = self.session.get(f"{BASE_URL}/projects/{self.project_id}/files")
        result = response.json()
        
        assert result["code"] == 0, f"获取项目文件失败: {result['message']}"
        assert len(result["data"]["files"]) > 0, "项目文件列表为空"
        
        print(f"✅ 项目文件列表获取成功: {len(result['data']['files'])} 个文件")
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 CodeWright 集成测试")
        print("=" * 50)
        
        try:
            # 用户流程测试
            username = self.test_user_registration()
            self.test_user_login(username)
            
            # 项目管理测试
            self.test_create_project()
            
            # 文件管理测试
            self.test_upload_file()
            self.test_add_file_to_project()
            self.test_get_project_files()
            
            # 预览和导出测试
            self.test_preview_file()
            export_id = self.test_export_project()
            self.test_download_export(export_id)
            
            print("=" * 50)
            print("🎉 所有测试通过！CodeWright 系统运行正常")
            
        except Exception as e:
            print("=" * 50)
            print(f"❌ 测试失败: {str(e)}")
            raise

if __name__ == "__main__":
    tester = CodeWrightTester()
    tester.run_all_tests()
