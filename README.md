# code

```
OCR-Text-Recognition-Web/
├── app.py                 # Flask后端主程序   1
├── requirements.txt       # 依赖库    1
├── config.py              # API凭证配置（需加入.gitignore）
├── config_sample.py       # 配置示例文件   1
├── .gitignore             # Git忽略文件   1
├── static/
│   ├── css/
│   │   └── style.css      # 前端样式   1
│   ├── js/
│   │   └── script.js      # 前端交互逻辑   1
│   └── uploads/           # 临时存储上传图片（自动创建）
├── templates/
│   └── index.html         # 前端页面   1
├── README.md              # 项目说明文档
└── demo_video.mp4         # 5分钟以内的解说视频
```

# OCR文字识别系统 - 基于百度AI开放平台

> 一个简单易用的Web应用，利用百度OCR技术识别图片中的文字。

## 项目信息

| 项目 | 内容 |
|------|------|
| 学号 | 2024XXXXXXX |
| 姓名 | 张三 |
| 技术栈 | Python Flask + 百度OCR API + HTML/CSS/JS |

## 功能特点

- 📸 支持拖拽上传或点击上传图片
- 🎯 三种识别模式：标准版、高精度版、含位置信息版
- 📝 实时显示识别结果和行数统计
- 📋 一键复制识别文本
- 🎨 美观的现代化界面
- ⚡ 图片自动压缩优化，提升识别速度

## 快速开始

### 1. 获取百度API凭证

1. 访问 [百度AI开放平台](https://ai.baidu.com/)
2. 注册/登录账号
3. 进入控制台 → 创建应用（选择文字识别服务）
4. 获取 API Key 和 Secret Key

### 2. 安装依赖

```bash
pip install -r requirements.txt
