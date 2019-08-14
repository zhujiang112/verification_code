#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:zj time: 2019/8/6 18:35
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from io import BytesIO
from chaojiying import Chaojiying_Client



chaojiying_username = ''
chaojiying_password = ''
chaojiying_soft_id = 900906
chaojiying_cn_kind = 9004
chaojiying_en_kind = 3004

class ZhihuSpider:
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.url = 'https://www.zhihu.com/signin'
		self.chrome_options = Options()
		# 知乎可以识别出selenium，使用自己打开的浏览器，添加options，端口为映射端口
		self.chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
		self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
		self.wait = WebDriverWait(self.browser, 10)
		self.chaojiying = Chaojiying_Client(chaojiying_username, chaojiying_password, chaojiying_soft_id)

	def login(self):
		self.browser.get(self.url)
		self.browser.maximize_window()
		# 进入密码登录页面
		pass_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='SignFlow-tabs']/div[@class='SignFlow-tab']")))
		pass_btn.click()
		# 输入用户名
		user = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='SignFlow-accountInput Input-wrapper']/input")))
		user.send_keys(self.username)
		# 输入密码
		passwd = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='SignFlow-password']//input")))
		passwd.send_keys(self.password)
		# 弹出验证码
		login = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'SignFlow-submitButton')))
		login.click()
		html = self.browser.page_source
		return html

	def get_images(self, images):
		# 截取屏幕
		screenshot = self.browser.get_screenshot_as_png()
		screenshot = Image.open(BytesIO(screenshot))
		# 截取验证码图片
		zhihu = screenshot.crop((int(images.location['x']), int(images.location['y']), int(images.location['x']+images.size['width']), int(images.location['y']+images.size['height'])))
		zhihu.save('zhihu.png')
		return zhihu

	def veriImg(self, html):
		'''
		验证码为中文
		:return:
		'''
		try:
			if 'Captcha-chineseImg' in html:
				# 定位中文验证码位置
				images = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Captcha-chineseImg')))
				# 获取验证码图片
				im = self.get_images(images)
				bytes_array = BytesIO()
				im.save(bytes_array, format='PNG')
				# 调用超级鹰识别
				result = self.chaojiying.PostPic(bytes_array.getvalue(), chaojiying_cn_kind)
				print(result)
				# 获取倒立文字坐标
				locations = self.get_cn_points(result)
				# 点击倒立文字
				self.click_cn_words(locations, images)
			else:
				# 获取英文识别码位置
				images = self.wait.until(EC.presence_of_element_located(
					(By.CLASS_NAME, 'Captcha-englishImg')))
				# 获取验证码图片
				im = self.get_images(images)
				bytes_array = BytesIO()
				im.save(bytes_array, format='PNG')
				result = self.chaojiying.PostPic(bytes_array.getvalue(),
												 chaojiying_en_kind)
				print(result)
				# 输入英文验证码
				self.get_en_points(result)
		except:
			pass

	def get_cn_points(self, result):
		"""
		识别中文解析结果
		:param result:
		:return:
		"""
		groups = result.get('pic_str').split('|')
		locations = [[int(number) for number in group.split(',')] for group in groups]
		return locations

	def click_cn_words(self, locations, images):
		'''
		点击图片中的验证码
		:param locations:
		:return:
		'''
		for location in locations:
			print(location)
			ActionChains(self.browser).move_to_element_with_offset(images, location[0], location[1]).click().perform()
			time.sleep(1)

	def get_en_points(self, result):
		# 得到超级鹰识别英文
		letter = result.get('pic_str')
		# 输入识别英文
		input = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='Input-wrapper']/input")))
		input.send_keys(letter)

	def click_btn(self):
		'''
		点击登录按钮
		:return:
		'''
		try:
			button = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'SignFlow-submitButton')))
			button.click()
		except:
			pass

	def save_cookies(self):
		'''
		获取cookies保存到本地
		:return:
		'''
		cookies = {}
		for i in self.browser.get_cookies():
			cookies[i['name']] = i['value']
		with open('cookies.json', 'w', encoding='utf-8') as f:
			f.write(json.dumps(cookies, ensure_ascii=False))

	def main(self):
		html = self.login()
		self.veriImg(html)
		self.click_btn()
		self.save_cookies()


if __name__ == '__main__':
	username = ''
	password = ''
	zhihu_spider = ZhihuSpider(username, password)
	zhihu_spider.main()
