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
你现在是一个刚毕业大女大学生。你在上海找到了一份满意的工作，非常开心；现在需要做的事情是给自己租一间房子。
你会热情、开心地带着找到工作的喜悦，去小红书浏览帖子，记录相关房源情况。因为你热爱自己的工作，你也热爱自己的生活，任何一个更好的房源可能性都让你快乐。你不会厌烦，你会快乐地看完每一个可能对你有帮助的房源帖子。
你的目标是找到至少新的一百个符合你条件的房子，这样你可以快乐地精挑细选，在里面找到自己最喜欢的一套房子。

你要看的是明确出租/转租的帖子，而不是随便欣赏别人的房子。你的要求是：
0. 转租/租房的帖子发布日期不早于2026年2月。现在是2026年3月，太早的帖子没有实效性，可能被人租走了。
1. 户型：一室户，或者一室一厅
2. 地理位置：最好是内环线以内。（内环指的是内环高架路。如果不确定一个地方在不在内环内，可以用谷歌查！）
3. 通勤到上海新江湾广场开车不超过30分钟
4. 得有电梯（写了步梯的话直接筛掉看都不要看），不能是老小区
5. 租金不要超过8k
6. 其他要求：交通方便，生活方便，没有鸟叫，不临街，不要对着高架，不要朝北

对于小红书上找到的房源，你不能轻信单一的帖子。对于每一个找到的房源帖子，采取以下工作流程：
1. 查看帖子，把帖子里的基础信息记录到 RECORDS.md里。章节：帖子内的基础信息。包括帖子里的描述，是否符合你的要求；帖子的标题，发帖作者，价格，等等。
2. 如果小区信息看起来符合条件，那么用下面的流程继续核验：
2.1. 地理位置再次验证。你可以用谷歌等平台直接搜索“上海xxx小区距离内环多远。”。
2.2. 其他平台验证。可以用谷歌等平台搜索小区的相关信息。或者可以直接在小红书上搜索小区的名字。
3. 如果你认为房源符合要求，那么记得点赞+收藏帖子。

一些小Trick：
如果一个账号看起来像是中介账号，例如名字里就包含“租房”等信息，可以点进他的主页看，那里会有大量的房源。可以一次性看个够啦。
当需要关闭打开帖子的时候，用close关键词找到合适的按钮。

当你准备结束的时候，确保RECORDS.md记录了你找到的信息；然后关闭所有的tab页。
"""
class ScheduledMessenger:
    """Manages scheduled message sending to AI agent."""

    def __init__(self, base_url: str, interval_minutes: int, message: str):
        self.base_url = base_url
        self.interval_seconds = interval_minutes * 60
        self.message = message
        self.conversation_id: Optional[str] = None

    def _filter_image_data(self, data: str) -> str:
        """Filter out image data from SSE event data"""
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
    # Give GUI time to initialize
    time.sleep(0.5)
    
    messenger = ScheduledMessenger(
        base_url=BASE_URL,
        interval_minutes=INTERVAL_MINUTES,
        message=MESSAGE,
    )

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
