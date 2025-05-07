# 微信聊天记录视频截图工具

## 功能说明
本工具用于自动从微信聊天记录录屏视频中提取截图，具有以下特点：
- 智能识别视频中的文本变化，自动截取关键帧
- 多线程处理大幅提升处理速度(默认12线程)
- 实时进度显示，直观了解处理进度
- 确保截图内容连续性，自动跳过相似度高的帧

## 安装依赖
1. 安装Python依赖：
```bash
pip install -r requirements.txt
```

2. 安装Tesseract OCR（文字识别必需）：
- Windows: 下载安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- Mac: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

3. 下载中文语言包：
- 下载 `chi_sim.traineddata` 放到 Tesseract 的 tessdata 目录

## 使用说明
1. 将微信聊天记录视频放入 `videos` 目录
2. 运行程序：
```bash
python main.py
```
3. 截图将保存在 `save` 目录中，命名格式为 `screenshot_XXXX.png` (XXXX为帧号)

## 参数调整
- `min_interval`: 最小截图间隔帧数(默认15)
- `max_interval`: 最大截图间隔帧数(默认200)
- `workers`: 线程数(默认12)
- `similarity_threshold`: 文本相似度阈值(默认0.25，低于此值视为新内容)
- 如需修改Tesseract路径，取消注释并修改 `pytesseract.pytesseract.tesseract_cmd`
- 可在main.py中调整process_video()的参数值

## 高级用法
1. 直接调用处理函数：
```python
from main import process_video
process_video("your_video.mp4", "output_dir", min_interval=20, max_interval=150, workers=8)
```

## 注意事项
1. 确保视频分辨率清晰，文字可识别
2. 中文识别需要安装中文语言包
3. 首次运行可能需要调整以下参数以获得最佳效果：
   - 帧间隔(min_interval/max_interval)
   - 相似度阈值
   - 线程数(根据CPU核心数调整)
