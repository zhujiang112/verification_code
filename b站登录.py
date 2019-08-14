#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author:zj time: 2019/8/4 16:16
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import numpy as np
from selenium.webdriver.common.action_chains import ActionChains


class Bili:
	def __init__(self):
		self.url = 'https://passport.bilibili.com/login'
		self.username = ''
		self.password = ''
		self.browser = webdriver.Chrome()
		self.browser.get(self.url)
		self.wait = WebDriverWait(self.browser, 10)

	def login(self):
		self.browser.maximize_window()
		user = self.wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
		user.send_keys(self.username)
		passwd = self.wait.until(EC.presence_of_element_located((By.ID, 'login-passwd')))
		passwd.send_keys(self.password)
		btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-login')))
		btn.click()

	def get_images(self):
		self.login()
		# 定位背景图片和滑块图片
		bg = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_bg')))
		seg = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_canvas_slice')))

		# 调用js隐藏背景图片
		self.browser.execute_script("arguments[0].setAttribute('style', 'display:none;')", bg)
		# 网页截屏
		screenshot = self.browser.get_screenshot_as_png()
		# 用Image打开,因为Image有很多操作
		screenshot = Image.open(BytesIO(screenshot))
		# 根据拼图位置获取划块
		imgSeg = screenshot.crop((seg.location['x'], seg.location['y'], seg.location['x'] + seg.size['width'], seg.location['y'] + seg.size['height']))
		# 保存拼图到文件
		imgSeg.save('bili/seg.png')
		# 隐藏划块，放出背景图片
		self.browser.execute_script("arguments[0].setAttribute('style', 'display:block;')", bg)
		self.browser.execute_script("arguments[0].setAttribute('style', 'display:none;')", seg)
		# 网页截屏
		screenshot = self.browser.get_screenshot_as_png()
		# 用Image打开,因为Image有很多操作
		screenshot = Image.open(BytesIO(screenshot))
		# 根据图片位置获取背景图片
		imgBg = screenshot.crop((bg.location['x'], bg.location['y'], bg.location['x'] + bg.size['width'], bg.location['y'] + bg.size['height']))
		imgBg.save('bili/bg.png')
		# 显示出滑块图
		self.browser.execute_script("arguments[0].setAttribute('style', 'display:block;')", seg)
		return imgSeg, imgBg


	def get_distance(self, imgSeg ,imgBg):
		# 滑块图的四周的极限值
		left = 100
		top = 155
		right = 0
		bottom = 0
		# 获取滑块左上角第一个像素
		pb = imgSeg.getpixel((0,0))
		# 遍历图片像素
		for x in range(0, 100):
			for y in range(0, 155):
				p = imgSeg.getpixel((x, y))
				# 和第一个像素比较，为什么阈值是 15 而不是 1，因为后面有段背景是灰色非土块和开始颜色不一致，过滤掉背景部分
				if (abs(pb[0] - p[0]) > 15 or abs(pb[1] - p[1]) > 15 or abs(pb[2] - p[2]) > 15):
					if x < left:
						left = x
					if x > right:
						right = x
					if y < top:
						top = y
					if y > bottom:
						bottom = y

		# 减去描边和凹凸部分
		offset = 5
		# 计算位置和大小
		left += offset
		top += offset
		right -= offset
		bottom -= offset
		width = right - left
		height = bottom - top

		# # 裁减出图块
		imgC0 = imgSeg.crop((left, top, right, bottom))

		# 差值
		val = 4
		# 滑块当前位置
		pos =right

		# 从左到右移动滑块位置
		for x in range(right, 250 - right):
			# 获取背景图片相应位置截图
			imgC1 = imgBg.crop((x, top, x+width, bottom))
			# 计算对应点的RGB的差值
			score = np.sum(np.absolute(np.array(imgC0) - np.array(imgC1))) / (height*width) / 255
			if score < val:
				val = score
				pos = x
		distance = pos - left
		return distance


	def move_to_gap(self, distance):
		# 获取划块
		slider = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_slider_button')))
		# 移动到滑块位置
		ActionChains(self.browser).move_to_element(slider).perform()
		# 点击滑块并向右移动
		ActionChains(self.browser).click_and_hold(slider).move_by_offset(xoffset=distance, yoffset=0).perform()
		time.sleep(1)
		# 松开滑块
		ActionChains(self.browser).release().perform()


if __name__ == '__main__':
	bili = Bili()
	imgSeg, imgBg  = bili.get_images()
	distance = bili.get_distance(imgSeg, imgBg)
	bili.move_to_gap(distance)
