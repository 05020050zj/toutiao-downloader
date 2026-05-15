#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今日头条视频下载器 - Android APK版
使用 Kivy 构建界面
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty
import threading
import os
import re
import json
import requests
import subprocess

# 设置窗口背景色
Window.clearcolor = (0.95, 0.95, 0.95, 1)


class ToutiaoDownloaderApp(App):
    status_text = StringProperty("准备就绪")
    
    def build(self):
        self.title = "今日头条视频下载器"
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题
        title = Label(
            text="[b]今日头条视频下载器[/b]",
            markup=True,
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.4, 0.8, 1)
        )
        main_layout.add_widget(title)
        
        # 说明文字
        hint = Label(
            text="粘贴分享链接或短链接",
            font_size='14sp',
            size_hint_y=None,
            height=30,
            color=(0.4, 0.4, 0.4, 1)
        )
        main_layout.add_widget(hint)
        
        # 输入框
        self.url_input = TextInput(
            hint_text="粘贴链接，例如：https://m.toutiao.com/is/xxxxx/",
            multiline=True,
            size_hint_y=None,
            height=120,
            font_size='16sp',
            padding=[15, 15],
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1)
        )
        main_layout.add_widget(self.url_input)
        
        # 按钮区域
        btn_layout = BoxLayout(size_hint_y=None, height=60, spacing=15)
        
        self.parse_btn = Button(
            text="解析视频",
            font_size='18sp',
            background_color=(0.2, 0.6, 0.9, 1),
            color=(1, 1, 1, 1)
        )
        self.parse_btn.bind(on_press=self.on_parse)
        btn_layout.add_widget(self.parse_btn)
        
        self.download_btn = Button(
            text="下载视频",
            font_size='18sp',
            background_color=(0.2, 0.7, 0.4, 1),
            color=(1, 1, 1, 1),
            disabled=True
        )
        self.download_btn.bind(on_press=self.on_download)
        btn_layout.add_widget(self.download_btn)
        
        main_layout.add_widget(btn_layout)
        
        # 清空按钮
        clear_btn = Button(
            text="清空",
            font_size='16sp',
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        clear_btn.bind(on_press=self.on_clear)
        main_layout.add_widget(clear_btn)
        
        # 状态显示区域
        status_label = Label(
            text="[b]状态:[/b]",
            markup=True,
            font_size='16sp',
            size_hint_y=None,
            height=30,
            color=(0.3, 0.3, 0.3, 1),
            halign='left'
        )
        status_label.bind(size=status_label.setter('text_size'))
        main_layout.add_widget(status_label)
        
        # 状态文本（可滚动）
        scroll = ScrollView(size_hint=(1, 1))
        self.status_label = Label(
            text=self.status_text,
            font_size='14sp',
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top',
            padding=[10, 10]
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        scroll.add_widget(self.status_label)
        main_layout.add_widget(scroll)
        
        # 底部信息
        footer = Label(
            text="支持: 标准链接 / APP短链接 / 分享文本",
            font_size='12sp',
            size_hint_y=None,
            height=30,
            color=(0.5, 0.5, 0.5, 1)
        )
        main_layout.add_widget(footer)
        
        # 绑定属性更新
        self.bind(status_text=self.update_status_label)
        
        # 存储解析后的信息
        self.video_info = None
        self.download_path = None
        
        return main_layout
    
    def update_status_label(self, instance, value):
        self.status_label.text = value
    
    def log(self, message):
        """添加日志"""
        current = self.status_text
        if current == "准备就绪":
            self.status_text = message
        else:
            self.status_text = current + "\n" + message
    
    def on_clear(self, instance):
        """清空输入"""
        self.url_input.text = ""
        self.status_text = "准备就绪"
        self.video_info = None
        self.download_btn.disabled = True
    
    def on_parse(self, instance):
        """解析视频"""
        text = self.url_input.text.strip()
        if not text:
            self.show_popup("错误", "请输入链接")
            return
        
        self.parse_btn.disabled = True
        self.status_text = "正在解析..."
        
        # 在后台线程中执行
        thread = threading.Thread(target=self._do_parse, args=(text,))
        thread.daemon = True
        thread.start()
    
    def _do_parse(self, text):
        """后台解析"""
        try:
            # 提取URL
            url = self._extract_url(text)
            if not url:
                Clock.schedule_once(lambda dt: self._parse_error("未找到有效链接"), 0)
                return
            
            self.log(f"提取链接: {url}")
            
            # 解析短链接
            if '/is/' in url:
                self.log("检测到短链接，正在解析...")
                resolved = self._resolve_short_url(url)
                if resolved:
                    url = resolved
                    self.log(f"解析成功: {url}")
            
            # 获取视频信息
            self.log("正在获取视频信息...")
            info = self._get_video_info(url)
            
            if info:
                self.video_info = {
                    'url': url,
                    'title': info.get('title', '未知标题'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', '')
                }
                Clock.schedule_once(self._parse_success, 0)
            else:
                Clock.schedule_once(lambda dt: self._parse_error("无法获取视频信息，视频可能已删除"), 0)
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self._parse_error(f"解析出错: {str(e)}"), 0)
    
    def _parse_success(self, dt):
        """解析成功回调"""
        info = self.video_info
        self.log(f"✓ 解析成功!")
        self.log(f"标题: {info['title']}")
        self.log(f"时长: {info['duration']}秒")
        if info['uploader']:
            self.log(f"作者: {info['uploader']}")
        self.parse_btn.disabled = False
        self.download_btn.disabled = False
    
    def _parse_error(self, message):
        """解析失败回调"""
        self.log(f"✗ {message}")
        self.parse_btn.disabled = False
    
    def on_download(self, instance):
        """下载视频"""
        if not self.video_info:
            self.show_popup("错误", "请先解析视频")
            return
        
        self.download_btn.disabled = True
        self.log("\n开始下载视频...")
        
        thread = threading.Thread(target=self._do_download)
        thread.daemon = True
        thread.start()
    
    def _do_download(self):
        """后台下载"""
        try:
            url = self.video_info['url']
            title = self._sanitize_filename(self.video_info['title'])
            
            # 下载目录
            download_dir = os.path.join(os.path.expanduser('~'), 'Download')
            if not os.path.exists(download_dir):
                download_dir = '/sdcard/Download'
            if not os.path.exists(download_dir):
                download_dir = os.getcwd()
            
            output_path = os.path.join(download_dir, f"{title}.mp4")
            
            self.log(f"保存路径: {output_path}")
            
            # 使用 yt-dlp 下载
            # 注意：在APK中需要确保 yt-dlp 可用
            try:
                import yt_dlp
                
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': output_path,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    Clock.schedule_once(
                        lambda dt: self._download_success(output_path, size), 0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: self._download_error("下载失败，文件未生成"), 0
                    )
                    
            except ImportError:
                # 如果没有 yt_dlp，使用 requests 简单下载
                self.log("使用备用下载方式...")
                self._simple_download(url, output_path)
                
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._download_error(f"下载出错: {str(e)}"), 0
            )
    
    def _simple_download(self, url, output_path):
        """简单下载方式（备用）"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.0.36'
            }
            
            # 先尝试获取真实视频URL
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            # 从页面找视频链接
            video_urls = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', resp.text)
            
            if video_urls:
                video_url = video_urls[0]
                self.log(f"找到视频地址，开始下载...")
                
                r = requests.get(video_url, headers=headers, stream=True, timeout=120)
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    Clock.schedule_once(
                        lambda dt: self._download_success(output_path, size), 0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: self._download_error("下载失败"), 0
                    )
            else:
                Clock.schedule_once(
                    lambda dt: self._download_error("未找到视频地址"), 0
                )
                
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._download_error(f"下载出错: {str(e)}"), 0
            )
    
    def _download_success(self, path, size):
        """下载成功回调"""
        self.log(f"✓ 下载成功!")
        self.log(f"文件大小: {size/1024/1024:.2f} MB")
        self.log(f"保存位置: {path}")
        self.download_btn.disabled = False
        self.show_popup("下载完成", f"视频已保存到:\n{path}")
    
    def _download_error(self, message):
        """下载失败回调"""
        self.log(f"✗ {message}")
        self.download_btn.disabled = False
    
    def _extract_url(self, text):
        """从文本中提取URL"""
        match = re.search(r'(https?://[^\s`<>"\']+)', text)
        if match:
            return match.group(1).rstrip('`')
        return None
    
    def _resolve_short_url(self, short_url):
        """解析短链接"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13)'}
            resp = requests.get(short_url, allow_redirects=True, headers=headers, timeout=15)
            match = re.search(r'/video/(\d+)/', resp.url)
            if match:
                return f"https://www.toutiao.com/video/{match.group(1)}/"
            match = re.search(r'/video/(\d+)/', resp.text)
            if match:
                return f"https://www.toutiao.com/video/{match.group(1)}/"
        except:
            pass
        return None
    
    def _get_video_info(self, url):
        """获取视频信息"""
        try:
            # 尝试使用 yt-dlp
            try:
                import yt_dlp
                ydl_opts = {'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info
            except ImportError:
                pass
            
            # 备用：直接请求页面
            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13)'}
            resp = requests.get(url, headers=headers, timeout=15)
            
            # 尝试从页面提取标题
            title_match = re.search(r'<title>([^<]+)</title>', resp.text)
            title = title_match.group(1) if title_match else '未知标题'
            title = title.replace(' - 今日头条', '').strip()
            
            return {'title': title, 'duration': 0, 'uploader': ''}
            
        except Exception as e:
            print(f"获取信息出错: {e}")
            return None
    
    def _sanitize_filename(self, name):
        """清理文件名"""
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        name = name.strip(' .')
        if len(name) > 50:
            name = name[:50]
        return name or "video"
    
    def show_popup(self, title, message):
        """显示弹窗"""
        popup = Popup(
            title=title,
            content=Label(text=message, text_size=(300, None)),
            size_hint=(None, None),
            size=(350, 200)
        )
        popup.open()


if __name__ == '__main__':
    ToutiaoDownloaderApp().run()
