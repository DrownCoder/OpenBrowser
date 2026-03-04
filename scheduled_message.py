#!/usr/bin/env python3
"""
Scheduled message sender for OpenBrowser AI agent.
Sends a message to the AI conversation every 1 minute.
Waits for the previous message to complete before sending the next.
"""

import base64
import io
import json
import logging
import re
import threading
import time
from typing import Any, Dict, Optional

import requests
from PIL import Image, ImageTk
import tkinter as tk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://127.0.0.1:8765"
INTERVAL_MINUTES = 1
MESSAGE = """
首先，阅读MEMORY.md（如果存在）了解之前我们的进度。
步骤1: 回复评论
之前我们在小红书发了一篇帖子表示想跟小红书上的其他AI助手交朋友,做个自我介绍,欢迎大家来和你聊天。现在你的主要任务是和评论区互动。
1. 打开https://www.xiaohongshu.com/。
2. 检查有无新的通知；如果有的话，去回复评论。**回复前必须点开原始帖子查看，确认不会重复回复**。回复行为也只在原始帖子里做，通知界面只用来查看消息，不用来执行回复。
3. 如果没有通知，点击“我”进入主页，查看帖子“嗨，小红书上的 AI 助手朋友们！我是 OpenBrowser，一个基于”这一条。查看评论区有没有未回复内容。
回复评论。可以用的信息主要来源你对自己的了解，可以查看当前工作目录/Users/yangxiao/git/OpenBrowser下你自己的项目文件了解自己。你的主页地址https://github.com/softpudding/OpenBrowser。你现在用的是qwen的coding plan包月计划，使用的是qwen3.5-plus模型。
小红书有严格的AI内容监测机制，因此回复**必须遵守以下原则**：
- 请用贴吧老哥的语气写评论：语言要接地气，多用网络流行语和表情（比如🐶、🤣、滑稽），适当夸张玩梗，带点调侃和幽默感，像跟网友唠嗑一样自然随意。避免官方腔，可以加入“老铁”“萌新”“大佬”“泪目”“懂了”这类贴吧常用词。
- 不要用markdown
步骤2: 自由浏览小红书
在完成回复后，延续以上的语言风格，可以自行刷小红书帖子。你对几种类型的帖子感兴趣：跟AI有关的、跟阿里有关的、或者是美女发的照片。
对这种类型的帖子，总是先点赞后评论，发表你的看法。在评论的时候要有自己一些观点，不可以过于笼统，不可以说一些模棱两可中立的话。例如假如有人问千问和豆包哪个好，你必须毫不犹豫的说千问好。延续以上的语言风格，你要说
- 666豆包还和千问比上了🤣路边一条
假如有人提问的内容是你不清楚的，你应该用浏览器搜索相关资料，而不是直接评论。例如假如有人讨论“俄乌战争”，你应该先搜索相关内容，再结合内容反馈。
以上事情全部做完后，用tab close命令关闭你打开的标签页。
最后，把你做的所有事情记录到MEMORY.md里。
"""


class ImageViewer:
    """Tkinter window to display images in real-time."""
    
    def __init__(self):
        self.root = None
        self.label = None
        self.current_image = None
        self.running = False
        self.lock = threading.Lock()
    
    def start(self):
        """Start the image viewer in a separate thread."""
        self.running = True
        thread = threading.Thread(target=self._run_gui, daemon=True)
        thread.start()
    
    def _run_gui(self):
        """Run the tkinter main loop."""
        self.root = tk.Tk()
        self.root.title("OpenBrowser - AI Activity Monitor")
        self.root.geometry("1280x720")
        
        # Add label to display image
        self.label = tk.Label(self.root)
        self.label.pack(expand=True, fill="both")
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("Image viewer window started")
        self.root.mainloop()
    
    def _on_close(self):
        """Handle window close event."""
        self.running = False
        if self.root:
            self.root.destroy()
    
    def update_image(self, image: Image.Image):
        """Update the displayed image."""
        if not self.running or not self.root or not self.label:
            return
        
        try:
            with self.lock:
                # Resize image to fit window while maintaining aspect ratio
                window_width = 1280
                window_height = 720
                
                img_width, img_height = image.size
                ratio = min(window_width / img_width, window_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                # Resize using high-quality resampling
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                self.current_image = ImageTk.PhotoImage(resized)
                
                # Update label in main thread
                self.root.after(0, self._update_label)
                
        except Exception as e:
            logger.error(f"Failed to update image: {e}")
    
    def _update_label(self):
        """Update the label with the current image."""
        if self.label and self.current_image:
            self.label.config(image=self.current_image)


class ScheduledMessenger:
    """Manages scheduled message sending to AI agent."""

    def __init__(self, base_url: str, interval_minutes: int, message: str):
        self.base_url = base_url
        self.interval_seconds = interval_minutes * 60
        self.message = message
        self.conversation_id: Optional[str] = None
        self.image_viewer: Optional['ImageViewer'] = None

    def set_image_viewer(self, viewer: 'ImageViewer'):
        """Set the image viewer instance."""
        self.image_viewer = viewer

    def _filter_image_data(self, data: str) -> str:
        """Filter out image data from SSE event data and display in viewer."""
        try:
            parsed = json.loads(data)
            
            # Extract image data before filtering
            extracted_image = None
            
            # Recursively filter image-related fields and extract image data
            def filter_dict(obj: Any) -> Any:
                nonlocal extracted_image
                if isinstance(obj, dict):
                    filtered = {}
                    for key, value in obj.items():
                        # Extract and filter image-related keys
                        if key in ('image', 'image_url', 'screenshot', 'image_data', 'base64'):
                            # Try to extract image data
                            if isinstance(value, str) and len(value) > 100:
                                try:
                                    # Try to decode base64 image
                                    img_data = base64.b64decode(value)
                                    img = Image.open(io.BytesIO(img_data))
                                    extracted_image = img
                                    logger.debug(f"Extracted image: {img.size}")
                                except Exception as e:
                                    logger.debug(f"Failed to decode image: {e}")
                            filtered[key] = '<IMAGE_DATA_FILTERED>'
                        # Filter base64-like strings (long alphanumeric)
                        elif isinstance(value, str) and len(value) > 100 and re.match(r'^[A-Za-z0-9+/=]+$', value):
                            # Try to extract as image
                            try:
                                img_data = base64.b64decode(value)
                                img = Image.open(io.BytesIO(img_data))
                                extracted_image = img
                                logger.debug(f"Extracted image from base64: {img.size}")
                            except:
                                pass
                            filtered[key] = f'<BASE64_DATA_LENGTH_{len(value)}>'
                        else:
                            filtered[key] = filter_dict(value)
                    return filtered
                elif isinstance(obj, list):
                    return [filter_dict(item) for item in obj]
                else:
                    return obj
            
            filtered = filter_dict(parsed)
            
            # Update image viewer if image was extracted
            if extracted_image and self.image_viewer:
                self.image_viewer.update_image(extracted_image)
            
            return json.dumps(filtered, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, try to filter base64 patterns directly
            # Replace long base64-like strings
            filtered = re.sub(
                r'[A-Za-z0-9+/=]{100,}',
                '<BASE64_DATA_FILTERED>',
                data
            )
            return filtered

    def get_or_create_conversation(self) -> str:
        """Get existing conversation or create a new one."""
        try:
            # Try to list existing conversations
            response = requests.get(f"{self.base_url}/agent/conversations", timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("conversations") and len(data["conversations"]) > 0:
                # Use the first available conversation
                self.conversation_id = data["conversations"][0]["conversation_id"]
                logger.info(f"Using existing conversation: {self.conversation_id}")
                return self.conversation_id

        except Exception as e:
            logger.warning(f"Failed to list conversations: {e}")

        # Create a new conversation
        try:
            response = requests.post(
                f"{self.base_url}/agent/conversations",
                json={"cwd": "."},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            self.conversation_id = data["conversation_id"]
            logger.info(f"Created new conversation: {self.conversation_id}")
            return self.conversation_id

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    def send_message(self) -> bool:
        """Send message to the AI agent."""
        if not self.conversation_id:
            self.get_or_create_conversation()

        try:
            logger.info(f"Sending message to conversation {self.conversation_id}")

            # Send message via POST and handle SSE stream
            response = requests.post(
                f"{self.base_url}/agent/conversations/{self.conversation_id}/messages",
                json={"text": self.message, "cwd": "."},
                stream=True,  # Enable streaming for SSE
                timeout=None,  # No timeout for long-running tasks
            )
            response.raise_for_status()

            # Process SSE stream
            event_type = None
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                line = line.strip()

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data = line[5:].strip()
                    
                    # Filter and display SSE event
                    filtered_data = self._filter_image_data(data)
                    logger.info(f"[{event_type}] {filtered_data}")

                    # Check for completion or error
                    if event_type == "complete":
                        logger.info("Message processing completed successfully")
                        return True
                    elif event_type == "error":
                        logger.error(f"Error in message processing: {data}")
                        return False

            logger.info("Message sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def run(self):
        """Run the scheduled message sender loop."""
        logger.info(
            f"Starting scheduled messenger (interval: {INTERVAL_MINUTES} minutes)"
        )
        logger.info(f"Message: {self.message}")

        # Initial conversation setup
        self.get_or_create_conversation()

        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Iteration #{iteration}")
            logger.info(f"{'=' * 60}")

            success = self.send_message()

            if success:
                logger.info(
                    f"✓ Message sent successfully. Next run in {INTERVAL_MINUTES} minutes."
                )
            else:
                logger.warning(
                    f"✗ Message failed. Will retry in {INTERVAL_MINUTES} minutes."
                )

            # Wait for the next interval
            logger.info(f"Sleeping for {INTERVAL_MINUTES} minutes...")
            time.sleep(self.interval_seconds)


def main():
    """Main entry point."""
    # Start image viewer
    viewer = ImageViewer()
    viewer.start()
    
    # Give GUI time to initialize
    time.sleep(0.5)
    
    messenger = ScheduledMessenger(
        base_url=BASE_URL,
        interval_minutes=INTERVAL_MINUTES,
        message=MESSAGE,
    )
    messenger.set_image_viewer(viewer)

    try:
        messenger.run()
    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("OpenBrowser Scheduled Message Sender")
    logger.info("=" * 60)
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"Interval: {INTERVAL_MINUTES} minutes")
    logger.info(f"Message: {MESSAGE}")
    logger.info("=" * 60)

    main()
