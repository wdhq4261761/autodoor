"""
测试鼠标滚动功能
"""
import pyautogui
import time

print("测试PyAutoGUI滚动功能...")
print("3秒后开始测试，请将鼠标移动到浏览器或其他可滚动窗口上...")
time.sleep(3)

print("\n测试1: 向下滚动5次，每次1个单位")
for i in range(5):
    pyautogui.scroll(-1)
    print(f"  执行第{i+1}次滚动")
    time.sleep(0.1)

time.sleep(1)

print("\n测试2: 向上滚动5次，每次1个单位")
for i in range(5):
    pyautogui.scroll(1)
    print(f"  执行第{i+1}次滚动")
    time.sleep(0.1)

time.sleep(1)

print("\n测试3: 向下滚动1次，5个单位")
pyautogui.scroll(-5)

time.sleep(1)

print("\n测试4: 向上滚动1次，5个单位")
pyautogui.scroll(5)

print("\n测试完成！")
print("如果滚动没有生效，可能的原因：")
print("1. 目标窗口没有焦点")
print("2. 目标窗口不支持滚动")
print("3. 滚动幅度太小")
print("4. 需要管理员权限")
