import os
import cv2
import pytesseract
from PIL import Image
import numpy as np
import difflib
from tqdm import tqdm
import concurrent.futures
import queue

# 配置Tesseract路径（根据实际安装路径修改）
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def calculate_similarity(text1, text2):
    """计算两段文本的相似度"""
    seq = difflib.SequenceMatcher(None, text1, text2)
    return seq.ratio()

def extract_text_from_image(img):
    """从图像中提取文本"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang='chi_sim+eng')
    return text.strip()

def save_screenshot(frame, count, save_dir):
    """保存截图"""
    filename = os.path.join(save_dir, f"screenshot_{count:04d}.png")
    cv2.imwrite(filename, frame)
    return filename

def process_video_segment(video_path, save_dir, start_frame, end_frame, min_interval, max_interval, segment_id, jump_interval):
    """处理视频片段
    Args:
        jump_interval: 跳帧间隔，控制处理帧的频率
                      例如设置为10表示每10帧处理1帧
    """
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    last_text = ""
    last_screenshot_count = start_frame
    count = start_frame
    
    # 为每个片段创建单独进度条
    pbar = tqdm(total=end_frame-start_frame, 
               desc=f"片段 {segment_id} 进度", 
               unit="帧",
               position=segment_id)
    
    while cap.isOpened() and count <= end_frame:
        ret, frame = cap.read()
        if not ret or count > end_frame:
            break
            
        if count % jump_interval != 0:
            count += 1
            continue
            
        # 更新进度条
        pbar.update(jump_interval)
        pbar.set_postfix_str(f"当前帧: {count}/{end_frame}\n\n")
        
        # 处理当前帧
        if count - last_screenshot_count < min_interval:
            count += 1
            continue
            
        current_text = extract_text_from_image(frame)
        if not current_text:
            count += 1
            continue
            
        needs_screenshot = False
        if not last_text:
            needs_screenshot = True
        else:
            similarity = calculate_similarity(last_text, current_text)
            if similarity < 0.25 or (count - last_screenshot_count >= max_interval):
                needs_screenshot = True
                
        if needs_screenshot:
            save_screenshot(frame, count, save_dir)
            last_text = current_text
            last_screenshot_count = count
            
        count += 1
        
    cap.release()
    pbar.close()
    return f"片段 {segment_id} 处理完成: {start_frame}-{end_frame} 帧"

def process_video(video_path, save_dir, min_interval=15, max_interval=150, workers=12, jump_interval=5):
    """多线程处理视频文件
    Args:
        video_path: 视频文件路径
        save_dir: 截图保存目录
        min_interval: 最小截图间隔帧数，避免连续截图，默认15帧
        max_interval: 最大截图间隔帧数，强制截图间隔，默认120帧
        workers: 线程数，默认12，将视频分割为对应数量的片段
        jump_interval: 跳帧间隔，处理视频时跳过的帧数，默认10帧(即每10帧处理1帧)
                      增大此值可提高处理速度但可能错过关键帧
                      减小此值可提高精度但会降低处理速度
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"开始处理视频: {video_path}")
    print(f"总帧数: {total_frames}, FPS: {fps}\n\n")
    
    # 计算每个线程处理的帧范围
    frames_per_worker = total_frames // workers
    segments = []
    for i in range(workers):
        start = i * frames_per_worker
        end = (i + 1) * frames_per_worker - 1 if i < workers - 1 else total_frames - 1
        segments.append((start, end))
    
    # 使用线程池处理各视频片段
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i, (start, end) in enumerate(segments):
            futures.append(executor.submit(
                process_video_segment,
                video_path,
                save_dir,
                start,
                end,
                min_interval,
                max_interval,
                i,
                jump_interval
            ))
        
        # 等待所有片段完成
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    
    print(f"\n\n视频处理完成，保存截图到: {save_dir}")

if __name__ == "__main__":
    # 创建输出目录
    os.makedirs("save", exist_ok=True)
    
    # 处理videos目录下的所有视频
    video_dir = "videos"
    for filename in os.listdir(video_dir):
        if filename.lower().endswith(('.mp4', '.avi', '.mov')):
            video_path = os.path.join(video_dir, filename)
            process_video(video_path, "save", workers=12)  # 使用12个线程
