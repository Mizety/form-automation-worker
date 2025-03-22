import asyncio
from datetime import date, datetime
import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
from playwright.async_api import async_playwright, TimeoutError as TimeoutException
from config import Config

from discord_notification import notify_to_discord_with_failed_content

async def remove_user_data_dir(directory):
    import shutil
    if os.path.exists(directory):
        shutil.rmtree(directory)

class PlaywrightCheck:
    def __init__(self):
        self.browser = None
        self.page = None
        self.user_data_dir = None

    async def init_browser(self):
           # Get absolute path to extension directory
        extension_path = os.path.abspath('./extension')
        self.user_data_dir = os.path.abspath('./users/user_data' + str(random.randint(1, 1000000)))
        
        user_agent_strings = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=Config.BROWSER_HEADLESS,
            args=[f'--disable-extensions-except={extension_path}',
                f'--load-extension={extension_path}'   
                    '--disable-gpu',  # Prevents GPU-related crashes in Docker
                    '--disable-dev-shm-usage',  # Avoids crashes due to small /dev/shm
                    '--no-sandbox',  # Required for running as root inside Docker
                    '--disable-setuid-sandbox',  # Avoids permission issues
                    '--disable-blink-features=AutomationControlled',  # Prevents detection as bot
                    '--disable-infobars',  # Removes "Chrome is being controlled by automated test software"
                    '--ignore-certificate-errors',  # Useful if the VPS has SSL issues
                    '--allow-running-insecure-content'  # Avoids mixed content blocking
                ],
            user_agent=random.choice(user_agent_strings),
            locale="de-DE",
            viewport={"width": 1024, "height": 720 },
            # record_video_dir="videos-test",
            # record_video_size={
            #     "width": 1024,
            #     "height": 720
            # }
        )

    async def init_page(self):
        self.page = await self.browser.new_page()

    async def close_browser(self):
        await self.browser.close()
        await remove_user_data_dir(self.user_data_dir)

    async def test_links_integration(self, url):
        await self.page.goto(url)
        await self.page.wait_for_timeout(1000)
        checks = []
        checks_failed =  False
        url = ""
    
        try:
            cookie_detected = self.page.locator('input[value="Alle akzeptieren"]')
            if cookie_detected and await cookie_detected.first.is_visible():
                await cookie_detected.first.click(force=True)
            # check if following selectors are present, visible and clickable/enabled.
            try: 
                await self.page.click('button.PP3Y3d' , force=True)
                checks.append("✅ button.PP3Y3d is present, visible and clickable/enabled")
                await self.page.wait_for_timeout(1000)  
            except Exception as e:
                checks.append(" ❌ button.PP3Y3d is not present, visible or clickable/enabled")
                checks_failed = True
            try:
                await self.page.click('div.fxNQSd' , force=True)
                checks.append("✅ div.fxNQSd is present, visible and clickable/enabled")
                await self.page.wait_for_timeout(1000)
            except Exception as e:
                checks.append(" ❌ div.fxNQSd is not present, visible or clickable/enabled")
                checks_failed = True
            try:
                url_locator = self.page.locator('input.vrsrZe')
                url = await url_locator.input_value()
                checks.append("✅ input.vrsrZe is present, visible and clickable/enabled")
            except Exception as e:
                checks.append(" ❌ input.vrsrZe is not present, visible or clickable/enabled")
                checks_failed = True
        except Exception as e:
            print(f"Error: {e}")
 
        finally:
            content = await self.page.content()
            notify_to_discord_with_failed_content(content, checks_failed, url, checks)
          


    async def run_test(self, url):
        """Wrapper method to run all operations in sequence"""
        try:
            await self.init_browser()
            await self.init_page()
            try:
              await self.test_links_integration(url)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                await self.close_browser()
            
        except Exception as e:
            print(f"Error: {e}")
            

if __name__ == "__main__":
    check = PlaywrightCheck()
    asyncio.run(check.run_test("https://www.google.com/maps/contrib/102614850577731744343/place/ChIJRYcmrSFxsEcRwfSHxlsSV8I/@52.4077888,9.6600101,12z/data=!4m6!1m5!8m4!1e1!2s102614850577731744343!3m1!1e1?hl=de&entry=ttu&g_ep=EgoyMDI1MDMxOS4xIKXMDSoJLDEwMjExNDUzSAFQAw%3D%3D"))
