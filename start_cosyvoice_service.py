#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动CosyVoice语音服务
"""

import os
import sys
import subprocess
import time
import requests
import psutil

def check_cosyvoice_service():
    """检查CosyVoice服务状态"""
    try:
        response = requests.get('http://localhost:9880/docs', timeout=5)
        return response.status_code == 200
    except:
        return False

def kill_existing_cosyvoice():
    """终止现有的CosyVoice进程"""
    print("🔄 检查并终止现有CosyVoice进程...")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if ('api.py' in cmdline and 'cosyvoice' in cmdline.lower()) or \
               ('api.cp312-win_amd64.pyd' in cmdline):
                print(f"   终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.terminate()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed_count > 0:
        print(f"   已终止 {killed_count} 个进程")
        time.sleep(3)  # 等待进程完全终止
    else:
        print("   未发现运行中的CosyVoice进程")

def start_cosyvoice_service():
    """启动CosyVoice服务"""
    print("🚀 启动CosyVoice语音服务...")
    
    cosyvoice_dir = "cosyvoice"
    if not os.path.exists(cosyvoice_dir):
        print("❌ 未找到CosyVoice目录")
        return False
    
    # 检查是否存在编译后的API文件
    api_pyd = os.path.join(cosyvoice_dir, "api.cp312-win_amd64.pyd")
    account_file = os.path.join(cosyvoice_dir, "account.txt")
    
    if not os.path.exists(api_pyd):
        print(f"❌ 未找到API文件: {api_pyd}")
        return False
    
    if not os.path.exists(account_file):
        print(f"❌ 未找到账户文件: {account_file}")
        return False
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        
        # 构建启动命令
        # 由于api.py已经被编译成.pyd，我们需要通过Python导入模块的方式启动
        cmd = [
            sys.executable, 
            "-c", 
            f"import sys; sys.path.insert(0, r'{os.path.abspath(cosyvoice_dir)}'); import api"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {cosyvoice_dir}")
        
        # 启动服务进程
        process = subprocess.Popen(
            cmd,
            cwd=cosyvoice_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        print(f"✅ CosyVoice服务已启动 (PID: {process.pid})")
        
        # 等待服务启动
        print("等待服务启动...")
        for i in range(30):
            if check_cosyvoice_service():
                print("✅ CosyVoice服务启动成功!")
                return True
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print("❌ 服务进程已退出")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
            
            time.sleep(1)
            print(f"   等待中... ({i+1}/30)")
        
        print("⚠️  服务启动超时，但进程仍在运行")
        return True
        
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        return False

def start_with_bat_file():
    """使用批处理文件启动服务"""
    print("🔄 尝试使用批处理文件启动...")
    
    bat_file = os.path.join("cosyvoice", "启动接口.bat")
    if not os.path.exists(bat_file):
        print(f"❌ 未找到批处理文件: {bat_file}")
        return False
    
    try:
        # 在新的控制台窗口中启动批处理文件
        process = subprocess.Popen(
            [bat_file],
            cwd="cosyvoice",
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        print(f"✅ 批处理启动成功 (PID: {process.pid})")
        
        # 等待服务启动
        print("等待服务启动...")
        for i in range(60):  # 批处理启动可能需要更长时间
            if check_cosyvoice_service():
                print("✅ CosyVoice服务启动成功!")
                return True
            time.sleep(1)
            print(f"   等待中... ({i+1}/60)")
        
        print("⚠️  服务启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 批处理启动失败: {e}")
        return False

def test_service():
    """测试服务是否正常工作"""
    print("🧪 测试CosyVoice服务...")
    
    if not check_cosyvoice_service():
        print("❌ 服务未运行")
        return False
    
    try:
        # 测试获取音色列表
        response = requests.get('http://localhost:9880/speakers_list', timeout=10)
        if response.status_code == 200:
            speakers = response.json()
            print(f"✅ 服务正常，发现 {len(speakers)} 个音色")
            return True
        else:
            print(f"⚠️  服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎤 CosyVoice语音服务启动器")
    print("=" * 50)
    
    # 1. 检查当前服务状态
    if check_cosyvoice_service():
        print("✅ CosyVoice服务已在运行")
        if test_service():
            print("🎉 服务运行正常!")
            return True
        else:
            print("⚠️  服务运行异常，尝试重启...")
    
    # 2. 终止现有进程
    kill_existing_cosyvoice()
    
    # 3. 尝试启动服务
    success = False
    
    # 方法1: 使用批处理文件启动
    print("\n📋 方法1: 使用批处理文件启动")
    if start_with_bat_file():
        success = True
    
    # 方法2: 如果批处理失败，尝试直接启动
    if not success:
        print("\n🐍 方法2: 直接启动Python模块")
        if start_cosyvoice_service():
            success = True
    
    # 4. 测试服务
    if success:
        time.sleep(5)  # 给服务一些时间完全启动
        if test_service():
            print("\n🎉 CosyVoice服务启动成功!")
            print("   API地址: http://localhost:9880")
            print("   文档地址: http://localhost:9880/docs")
        else:
            print("\n⚠️  服务已启动但测试失败")
            success = False
    
    if not success:
        print("\n❌ CosyVoice服务启动失败")
        print("建议:")
        print("   1. 检查cosyvoice目录下的文件完整性")
        print("   2. 手动运行: cosyvoice/启动接口.bat")
        print("   3. 查看是否有端口冲突")
        print("   4. 重启计算机后再试")
    
    return success

if __name__ == "__main__":
    main()
