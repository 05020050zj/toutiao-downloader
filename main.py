#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今日头条视频下载器 - Android APK版
修复中文显示 + 优化UI
"""

import os
import re
import json
import threading
import requests

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.graphics import Color, Rectangle

# ============================================================
# 修复中文显示：注册中文字体
# ============================================================
def register_chinese_font():
    """尝试多种方式加载中文字体"""
    font_registered = False

    # 1. Android 系统字体路径
    android_font_paths = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/NotoSansSC-Regular.otf',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansHans-Regular.otf',
        '/system/fonts/NotoSansCJKsc-Regular.otf',
        '/system/usr/share/fonts/NotoSansCJK/NotoSansCJKsc-Regular.otf',
    ]

    for fp in android_font_paths:
        if os.path.exists(fp):
            try:
                LabelBase.register('NotoSansCJK', fp)
                font_registered = True
                break
            except:
                continue

    # 2. 如果系统字体都找不到，尝试下载
    if not font_registered:
        try:
            font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fonts')
            os.makedirs(font_dir, exist_ok=True)
            font_path = os.path.join(font_dir, 'NotoSansCJKsc-Regular.otf')

            if not os.path.exists(font_path):
                # 下载中文字体
                download_urls = [
                    'https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf',
                ]
                for url in download_urls:
                    try:
                        r = requests.get(url, timeout=30)
                        if r.status_code == 200 and len(r.content) > 10000:
                            with open(font_path, 'wb') as f:
                                f.write(r.content)
                            break
                    except:
                        continue

            if os.path.exists(font_path):
                LabelBase.register('NotoSansCJK', font_path)
                font_registered = True
        except:
            pass

    return font_registered


# ============================================================
# 主题颜色
# ============================================================
COLORS = {
    'primary': (0.25, 0.47, 0.85, 1),
    'success': (0.18, 0.74, 0.42, 1),
    'danger': (0.91, 0.30, 0.24, 1),
    'warning': (1.0, 0.76, 0.03, 1),
    'bg': (0.96, 0.96, 0.98, 1),
    'card': (1.0, 1.0, 1.0, 1),
    'text': (0.2, 0.2, 0.2, 1),
    'text_light': (0.55, 0.55, 0.55, 1),
}


# ============================================================
# 带背景色的容器
# ============================================================
class ColoredBox(BoxLayout):
    """可以设置背景色的 BoxLayout"""
    def __init__(self, bg_color=(1,1,1,1), **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        with self.canvas.before:
            Color(*bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


# ============================================================
# 主应用
# ============================================================
class ToutiaoDownloaderApp(App):
    status_text = StringProperty("准备就绪，请粘贴分享链接")

    def build(self):
        self.title = "视频下载器"

        # 注册中文字体
        self.font_ok = register_chinese_font()
        self.font_name = 'NotoSansCJK' if self.font_ok else 'Roboto'

        Window.clearcolor = COLORS['bg']

        # 主布局
        root = BoxLayout(orientation='vertical', padding=0, spacing=0)

        # === 顶部标题栏 ===
        header = ColoredBox(
            bg_color=COLORS['primary'],
            size_hint_y=None, height='56dp',
            padding=[20, 0], spacing=10
        )
        title_label = Label(
            text="今日头条视频下载器",
            font_size='20sp',
            font_name=self.font_name,
            bold=True,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        header.add_widget(title_label)
        root.add_widget(header)

        # === 内容区域（可滚动）===
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None,
                           padding='16dp', spacing='12dp')
        content.bind(minimum_height=content.setter('height'))

        # --- 提示卡片 ---
        tip_card = ColoredBox(
            bg_color=COLORS['warning'],
            orientation='vertical', size_hint_y=None, height='44dp',
            padding=[16, 0]
        )
        tip_label = Label(
            text="支持粘贴分享文本 / 短链接 / 标准链接",
            font_size='13sp', font_name=self.font_name,
            color=(0.3, 0.3, 0.3, 1),
            halign='center', valign='middle'
        )
        tip_label.bind(size=tip_label.setter('text_size'))
        tip_card.add_widget(tip_label)
        content.add_widget(tip_card)

        # --- 输入框卡片 ---
        input_card = ColoredBox(
            bg_color=COLORS['card'],
            orientation='vertical', size_hint_y=None, height='130dp',
            padding=[16, 12]
        )
        input_label = Label(
            text="请输入链接或粘贴分享文本：",
            font_size='14sp', font_name=self.font_name,
            color=COLORS['text'], halign='left', valign='middle',
            size_hint_y=None, height='24dp'
        )
        input_label.bind(size=input_label.setter('text_size'))
        input_card.add_widget(input_label)

        self.url_input = TextInput(
            hint_text="粘贴链接，例如：\nhttps://m.toutiao.com/is/xxxxx/",
            multiline=True,
            font_size='15sp',
            font_name=self.font_name,
            padding=[12, 10],
            background_color=(0.97, 0.97, 0.98, 1),
            foreground_color=COLORS['text'],
            cursor_color=COLORS['primary'],
            size_hint_y=None, height='80dp'
        )
        input_card.add_widget(self.url_input)
        content.add_widget(input_card)

        # --- 按钮区域 ---
        btn_row = BoxLayout(
            size_hint_y=None, height='52dp', spacing='12dp',
            padding=[0, 4]
        )

        self.parse_btn = Button(
            text="解析视频",
            font_size='16sp', font_name=self.font_name,
            background_color=COLORS['primary'],
            color=(1, 1, 1, 1),
            background_normal='',
        )
        self.parse_btn.bind(on_press=self.on_parse)
        btn_row.add_widget(self.parse_btn)

        self.download_btn = Button(
            text="下载视频",
            font_size='16sp', font_name=self.font_name,
            background_color=COLORS['success'],
            color=(1, 1, 1, 1),
            background_normal='',
            disabled=True
        )
        self.download_btn.bind(on_press=self.on_download)
        btn_row.add_widget(self.download_btn)
        content.add_widget(btn_row)

        # --- 视频信息卡片（解析后显示） ---
        self.info_card = ColoredBox(
            bg_color=COLORS['card'],
            orientation='vertical', size_hint_y=None, height=0,
            padding=[16, 12]
        )
        self.info_title_label = Label(
            text="", font_size='15sp', font_name=self.font_name,
            color=COLORS['text'], halign='left', valign='middle',
            size_hint_y=None, height='28dp'
        )
        self.info_title_label.bind(size=self.info_title_label.setter('text_size'))
        self.info_card.add_widget(self.info_title_label)
        self.info_detail_label = Label(
            text="", font_size='13sp', font_name=self.font_name,
            color=COLORS['text_light'], halign='left', valign='middle',
            size_hint_y=None, height='22dp'
        )
        self.info_detail_label.bind(size=self.info_detail_label.setter('text_size'))
        self.info_card.add_widget(self.info_detail_label)
        content.add_widget(self.info_card)

        # --- 状态日志区域 ---
        log_label = Label(
            text="运行日志：",
            font_size='13sp', font_name=self.font_name,
            color=COLORS['text_light'], halign='left',
            size_hint_y=None, height='24dp'
        )
        log_label.bind(size=log_label.setter('text_size'))
        content.add_widget(log_label)

        log_card = ColoredBox(
            bg_color=(0.94, 0.94, 0.96, 1),
            orientation='vertical', size_hint_y=None, height='160dp',
            padding=[16, 10]
        )
        log_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.log_label = Label(
            text=self.status_text,
            font_size='13sp', font_name=self.font_name,
            color=COLORS['text'],
            size_hint_y=None,
            text_size=(Window.width - 64, None),
            halign='left', valign='top',
            padding=[4, 4]
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        log_scroll.add_widget(self.log_label)
        log_card.add_widget(log_scroll)
        content.add_widget(log_card)

        # --- 清空按钮 ---
        clear_btn = Button(
            text="清空",
            font_size='14sp', font_name=self.font_name,
            background_color=COLORS['danger'],
            color=(1, 1, 1, 1),
            background_normal='',
            size_hint_y=None, height='44dp'
        )
        clear_btn.bind(on_press=self.on_clear)
        content.add_widget(clear_btn)

        # --- 底部信息 ---
        footer = Label(
            text="v1.0  |  视频保存到 Download 目录",
            font_size='11sp', font_name=self.font_name,
            color=COLORS['text_light'],
            halign='center', valign='middle',
            size_hint_y=None, height='28dp'
        )
        footer.bind(size=footer.setter('text_size'))
        content.add_widget(footer)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.video_info = None
        self.bind(status_text=self._update_log)

        return root

    def _update_log(self, instance, value):
        self.log_label.text = value

    def log(self, msg):
        current = self.status_text
        if current == "准备就绪，请粘贴分享链接":
            self.status_text = msg
        else:
            self.status_text = current + "\n" + msg

    def on_clear(self, instance):
        self.url_input.text = ""
        self.status_text = "准备就绪，请粘贴分享链接"
        self.video_info = None
        self.download_btn.disabled = True
        self.info_card.height = 0
        self.info_title_label.text = ""
        self.info_detail_label.text = ""

    def on_parse(self, instance):
        text = self.url_input.text.strip()
        if not text:
            self._show_toast("请输入链接")
            return
        self.parse_btn.disabled = True
        self.status_text = "正在解析..."
        t = threading.Thread(target=self._do_parse, args=(text,))
        t.daemon = True
        t.start()

    def _do_parse(self, text):
        try:
            url = self._extract_url(text)
            if not url:
                Clock.schedule_once(lambda dt: self._parse_error("未找到有效链接"), 0)
                return

            self.log(f"提取链接: {url}")

            if '/is/' in url:
                self.log("检测到短链接，正在解析...")
                resolved = self._resolve_short_url(url)
                if resolved:
                    url = resolved
                    self.log(f"解析成功: {url}")

            self.log("正在获取视频信息...")
            info = self._get_video_info(url)

            if info:
                self.video_info = {
                    'url': url,
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', '')
                }
                Clock.schedule_once(self._parse_success, 0)
            else:
                Clock.schedule_once(
                    lambda dt: self._parse_error("无法获取视频信息"), 0
                )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._parse_error(f"解析出错: {str(e)}"), 0
            )

    def _parse_success(self, dt):
        info = self.video_info
        self.log("解析成功!")
        self.log(f"标题: {info['title']}")
        if info['duration']:
            m, s = divmod(int(info['duration']), 60)
            self.log(f"时长: {m}分{s}秒")
        if info['uploader']:
            self.log(f"作者: {info['uploader']}")

        # 显示信息卡片
        self.info_card.height = '64dp'
        self.info_title_label.text = info['title']
        detail = ""
        if info['duration']:
            m, s = divmod(int(info['duration']), 60)
            detail += f"时长: {m}分{s}秒  "
        if info['uploader']:
            detail += f"作者: {info['uploader']}"
        self.info_detail_label.text = detail

        self.parse_btn.disabled = False
        self.download_btn.disabled = False

    def _parse_error(self, msg):
        self.log(f"错误: {msg}")
        self.parse_btn.disabled = False

    def on_download(self, instance):
        if not self.video_info:
            self._show_toast("请先解析视频")
            return
        self.download_btn.disabled = True
        self.log("\n开始下载视频...")
        t = threading.Thread(target=self._do_download)
        t.daemon = True
        t.start()

    def _do_download(self):
        try:
            url = self.video_info['url']
            title = self._sanitize_filename(self.video_info['title'])

            # 下载目录
            if platform == 'android':
                download_dir = '/storage/emulated/0/Download'
            else:
                download_dir = os.path.join(os.path.expanduser('~'), 'Download')

            if not os.path.exists(download_dir):
                download_dir = os.getcwd()

            output_path = os.path.join(download_dir, f"{title}.mp4")
            self.log(f"保存到: {output_path}")

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
                        lambda dt: self._download_error("下载失败"), 0
                    )
            except ImportError:
                self._simple_download(url, output_path)

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._download_error(f"下载出错: {str(e)}"), 0
            )

    def _simple_download(self, url, output_path):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13)'}
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            video_urls = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', resp.text)
            if video_urls:
                self.log("找到视频地址，开始下载...")
                r = requests.get(video_urls[0], headers=headers, stream=True, timeout=120)
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
        self.log(f"下载成功!")
        self.log(f"大小: {size / 1024 / 1024:.2f} MB")
        self.log(f"位置: {path}")
        self.download_btn.disabled = False
        self._show_toast("下载完成!")

    def _download_error(self, msg):
        self.log(f"下载失败: {msg}")
        self.download_btn.disabled = False

    def _show_toast(self, msg):
        """显示 Toast 提示"""
        from kivy.uix.popup import Popup
        popup = Popup(
            title="提示",
            content=Label(text=msg, font_size='16sp',
                         text_size=(280, None)),
            size_hint=(None, None), size=(300, 150),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)

    # ============================================================
    # 工具方法
    # ============================================================
    def _extract_url(self, text):
        match = re.search(r'(https?://[^\s`<>"\']+)', text)
        if match:
            return match.group(1).rstrip('`')
        return None

    def _resolve_short_url(self, short_url):
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
        try:
            try:
                import yt_dlp
                ydl_opts = {'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info
            except ImportError:
                pass

            headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 13)'}
            resp = requests.get(url, headers=headers, timeout=15)
            title_match = re.search(r'<title>([^<]+)</title>', resp.text)
            title = title_match.group(1) if title_match else ''
            title = title.replace(' - 今日头条', '').strip()
            return {'title': title, 'duration': 0, 'uploader': ''}
        except:
            return None

    def _sanitize_filename(self, name):
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        name = name.strip(' .')
        if len(name) > 50:
            name = name[:50]
        return name or "video"


if __name__ == '__main__':
    ToutiaoDownloaderApp().run()
