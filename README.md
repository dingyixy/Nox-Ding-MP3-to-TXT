# MP3 批量转 TXT · Nox-Ding
下载程序：请前往本仓库的 [Releases](../../releases) 页面，下载完整离线版 ZIP。
一款面向 Windows 的本地音频转文字工具，适合整理 AI 配音、课程讲解和中文语音资料。支持批量添加音频或文件夹，将识别结果保存为同名简体中文 TXT。音频在本机处理，无需 API Key，不上传音频。

## 功能

- 支持 MP3、WAV、M4A、FLAC、AAC、OGG、WMA。
- 批量转换、自选输出目录、显示当前文件识别进度。
- 已有同名 TXT 自动另存，避免覆盖。
- 停止时保留已识别文字，再次处理可跳过已完成文件。
- 基于 faster-whisper，支持 base、small、medium、large-v3 模型，使用 CPU 识别。
- 界面带有 **Nox-Ding** 署名。

## 使用

完整解压 Windows 离线包，双击 `MP3批量转TXT.exe`，添加音频，选择输出目录，点击“开始转换”。

离线包包含运行环境和 small 模型；其他模型首次使用需要联网下载，保存在程序目录下的 `models` 文件夹。源码包不包含运行环境或模型。

## 从源码运行

建议使用 Windows 64 位 Python 3.12（需包含 Tkinter）。在源码目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

首次运行需下载所选模型。网络连接失败时请检查网络或代理设置。

## 说明

- 面向中文音频，输出简体中文；人名、数字、外语及工具名可能识别错误，请校对重要内容。
- “继续”指跳过已完成的音频；中途停止的单个文件下次会从头识别。
- 运行速度取决于模型大小、音频长度和电脑配置。
- 第三方识别引擎和模型并非本项目原创，各自许可证见对应项目及随包许可证文件。

## 致谢

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [PyAV](https://github.com/PyAV-Org/PyAV)
- [OpenCC Python](https://github.com/yichen0831/opencc-python)
