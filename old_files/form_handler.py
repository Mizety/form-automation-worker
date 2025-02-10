# import random
# import sys
# import time
# from playwright.async_api import async_playwright
# import logging
# import re
# from dataclasses import dataclass, field
# from typing import List, Optional, Dict, Any
# import asyncio

# from config import Config

# logging.basicConfig(
#     level=getattr(logging, Config.LOG_LEVEL),
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(Config.LOG_FILE),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
# logger = logging.getLogger(__name__)

# @dataclass
# class FormData:
#     country_of_residence: str = field(metadata={"alias": "countryOfResidence"})
#     is_child_abuse_content: bool = field(metadata={"alias": "isChildAbuseContent"})
#     remove_child_abuse_content: bool = field(metadata={"alias": "removeChildAbuseContent"})
#     full_legal_name: str = field(metadata={"alias": "fullLegalName"})
#     company_name: str = field(metadata={"alias": "CompanyName"})
#     company_you_represent: str = field(metadata={"alias": "CompanyYouRepresent"})
#     email: str
#     infringing_urls: List[str] = field(metadata={"alias": "InfringingUrls"})
#     is_related_to_media: bool = field(metadata={"alias": "isRelatedToMedia"})
#     question_one: str = field(metadata={"alias": "QuestionOne"})
#     question_two: str = field(metadata={"alias": "QuestionTwo"})
#     question_three: str = field(metadata={"alias": "QuestionThree"})
#     confirm_form: bool = field(metadata={"alias": "confirmForm"})
#     signature: str
#     id: str
#     status: Optional[str] = None
#     error: Optional[str] = None
#     retry_attempts: Optional[int] = field(default=None, metadata={"alias": "retryAtempts"})
#     created_at: Optional[str] = field(metadata={"alias": "createdAt"}, default=None)
#     updated_at: Optional[str] = field(metadata={"alias": "updatedAt"}, default=None)


# class HumanBehavior:
#     """Class to handle human-like behavior patterns"""
    
#     @staticmethod
#     async def natural_delay(min_ms: int = 100, max_ms: int = 500) -> None:
#         """Add a random delay between actions"""
#         await asyncio.sleep(random.uniform(min_ms/1000, max_ms/1000))

#     @staticmethod
#     def generate_natural_curve(start: tuple, end: tuple, control_points: int = 3) -> List[tuple]:
#         """Generate a natural mouse movement curve using Bezier curve"""
#         points = [start]
        
#         # Generate random control points
#         for _ in range(control_points):
#             x = start[0] + (end[0] - start[0]) * random.uniform(0.2, 0.8)
#             y = start[1] + (end[1] - start[1]) * random.uniform(0.2, 0.8)
#             points.append((x, y))
        
#         points.append(end)
#         return points

#     @staticmethod
#     def get_random_scroll_amount() -> int:
#         """Generate a random scroll amount"""
#         return random.randint(50, 100)

# class BrowserConfig:
#     """Class to handle browser configuration and anti-detection measures"""
    
#     @staticmethod
#     def get_browser_config() -> Dict[str, Any]:
#         return {
#             "args": [
#                 '--disable-blink-features=AutomationControlled',
#                 '--disable-features=IsolateOrigins,site-per-process',
#                 '--disable-site-isolation-trials',
#                 f'--window-size={random.randint(1024, 1920)},{random.randint(768, 1080)}',
#                 '--disable-dev-shm-usage',
#                 '--no-sandbox',
#                 '--disable-setuid-sandbox'
#             ]
#         }

#     @staticmethod
#     def get_context_config() -> Dict[str, Any]:
#         viewport_width = random.randint(1024, 1920)
#         viewport_height = random.randint(768, 1080)
        
#         return {
#             # "viewport": {"width": viewport_width, "height": viewport_height},
#             "user_agent": BrowserConfig.get_random_user_agent(),
#             "has_touch": random.choice([True, False]),
#             "is_mobile": random.choice([True, False]),
#             "device_scale_factor": random.choice([1, 1.5, 2]),
#             "locale": random.choice(['de-DE']),
#             "timezone_id": random.choice(['Europe/Berlin', 'Europe/London', 'America/New_York']),
#             "permissions": ['geolocation'],
#             "color_scheme": random.choice(['light', 'dark']),
#             "reduced_motion": random.choice(['reduce', 'no-preference'])
#         }

#     @staticmethod
#     def get_random_user_agent() -> str:
#         user_agents = [
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
#             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
#             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
#             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
#         ]
#         return random.choice(user_agents)

# class LegalFormFiller:
#     def __init__(self, page):
#         self.page = page
#         self.errors = []
#         self.human = HumanBehavior()

#     async def human_type(self, selector: str, text: str) -> None:
#         """Simulates human-like typing with variable delays and occasional mistakes"""
#         try:
#             element = await self.page.query_selector(selector)
#             if not element:
#                 raise Exception(f"Element not found: {selector}")

#             await self.human.natural_delay(200, 500)
            
#             for char in text:
#                 # Simulate typing mistakes (5% chance)
#                 if random.random() < 0.05:
#                     mistake_char = random.choice('qwertyuiopasdfghjklzxcvbnm')
#                     await element.type(mistake_char, delay=random.randint(50, 150))
#                     await self.human.natural_delay(200, 400)
#                     await element.press('Backspace')
#                     await self.human.natural_delay(100, 300)

#                 await element.type(char, delay=random.randint(50, 150))
                
#                 # Occasional pause while typing
#                 if random.random() < 0.1:
#                     await self.human.natural_delay(200, 400)

#         except Exception as e:
#             logger.error(f"Error in human_type: {str(e)}")
#             raise

#     async def human_click(self, selector: str, force: bool = False) -> None:
#         """Simulates human-like clicking with natural mouse movement"""
#         try:
#             element = await self.page.query_selector(selector)
#             if not element:
#                 raise Exception(f"Element not found: {selector}")

#             # Get element position
#             box = await element.bounding_box()
#             if not box:
#                 raise Exception(f"Could not get bounding box for: {selector}")

#             # Calculate start and end positions
#             start_x, start_y = await self.page.evaluate('() => [window.mouseX || 0, window.mouseY || 0]')
#             end_x = box['x'] + random.uniform(5, box['width'] - 5)
#             end_y = box['y'] + random.uniform(5, box['height'] - 5)

#             # Generate natural mouse movement curve
#             curve_points = self.human.generate_natural_curve((start_x, start_y), (end_x, end_y))

#             # Execute mouse movement
#             for point in curve_points:
#                 await self.page.mouse.move(point[0], point[1])
#                 await self.human.natural_delay(10, 30)

#             # Hover briefly before clicking
#             await self.human.natural_delay(100, 300)
            
#             # Use element.click() instead of mouse.click()
#             await element.click(force=force)

#         except Exception as e:
#             logger.error(f"Error in human_click: {str(e)}")
#             raise

#     async def natural_scroll(self, direction: str = 'down') -> None:
#         """Simulates natural scrolling behavior"""
#         try:
#             scroll_amount = self.human.get_random_scroll_amount()
#             steps = random.randint(5, 10)
            
#             for _ in range(steps):
#                 amount = scroll_amount // steps
#                 if direction == 'down':
#                     await self.page.evaluate(f'window.scrollBy(0, {amount})')
#                 else:
#                     await self.page.evaluate(f'window.scrollBy(0, -{amount})')
#                 await self.human.natural_delay(50, 100)

#         except Exception as e:
#             logger.error(f"Error in natural_scroll: {str(e)}")
#             raise

#     @staticmethod
#     def is_eu_member(country):
#         eu_countries = {
#             'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
#             'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
#             'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta',
#             'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia',
#             'Spain', 'Sweden', 'Deutschland'
#         }
#         return country in eu_countries

#     @staticmethod
#     def is_special_country(country):
#         special_countries = {
#             'Germany', 'Deutschland'
#         }
#         return country in special_countries

#     async def fill_form(self, data: FormData) -> None:
#         try:
#             # Initial page interaction delay
#             await self.human.natural_delay(100, 400)

#             # Natural scroll before country selection
#             await self.natural_scroll('down')

#             # Country selection
#             country_name = "Deutschland"
#             await self.human_click('div.sc-select')
#             await self.human.natural_delay(300, 600)
            
#             country_option = self.page.locator('li[role="option"]').filter(
#                 has_text=re.compile(f"^{re.escape(country_name)}$"))
#             await country_option.first.click()
#             await self.human_click('div.sc-select')
#             eu = self.is_eu_member(country_name)
#             await self.human.natural_delay(300, 600)
#             # Handle child abuse content section with natural behavior
#             if eu and data.is_child_abuse_content:
#                 await self.natural_scroll('down')
#                 await self.human_click("input#confirm_violate_csae_laws--confirm", force=True)
#                 await self.human.natural_delay(500, 1000)

#             # Fill personal information
#             if eu and data.is_child_abuse_content and data.remove_child_abuse_content:
#                 await self.human_click("input#confirm_to_report_anonymous--confirm", force=True)
#                 await self.human.natural_delay(300, 600)
#                 await self.human_type('#full_name_not_required', data.full_legal_name)
#                 await self.human.natural_delay(300, 600)
#                 await self.human_type('#contact_email_not_required', data.email)
#             else:
#                 await self.human_type('#full_name', data.full_legal_name)
#                 await self.human_type('#contact_email_noprefill', data.email)
#             await self.human_type('#companyname', data.company_name)
#             await self.human_type('#representedrightsholder', data.company_you_represent)
            
#             variant = self.is_special_country(country_name)
#             if variant:
#                 country_name_english = "Germany"
#                 # German form does not have some fields
#                 search_query = f'input[name="url_box3_geo_{country_name_english.lower()}"]'

#                 for i, url in enumerate(data.infringing_urls):
#                     locate = self.page.locator(search_query)
#                     if i == 0:
#                         await locate.fill(url)
#                     else:
#                         specifier = ''
#                         sub_specifier = '_2'
#                         if i > 1:
#                             specifier = f'_{i}'
#                             sub_specifier = f'_{i+1}'
#                         search_sub_query = f'input[name="url_box3_googlemybusiness{sub_specifier}"]'
#                         add_checkbox = self.page.locator(f'input#add_another_url_checkbox{specifier}--add')
#                         await add_checkbox.check(force=True)
#                         await self.page.fill(search_sub_query, url)
#             else:
#                 url_fields = self.page.locator("div.field.inline-branch input[name='url_box3']")

#                 # Ensure the number of input fields matches the number of URLs
#                 for i, url in enumerate(data.infringing_urls):
#                     if i < url_fields.count():
#                         await url_fields.nth(i).fill(url)  # Fill the existing field
#                     else:
#                         add_additional = self.page.locator("a.add-additional").first  # Click "Add additional field" button
#                         await add_additional.click(force=True)
#                         await self.page.locator("div.field.inline-branch input[name='url_box3']").nth(i).fill(
#                             url)  # Fill new field
#                 if data.is_related_to_media:
#                      ugcy = self.page.locator("label[for='is_geo_ugc_imagery--yes']")
#                      await ugcy.click(force=True)
#                 else:
#                     ugcn = self.page.locator("label[for='is_geo_ugc_imagery--no']")
#                     await ugcn.click(force=True)


#             # Fill explanations
#             await self.page.fill('#legalother_explain_googlemybusiness_not_germany', data.question_one)
#             await self.page.fill('#legalother_quote', data.question_two)
#             await self.page.fill('#legalother_quote_googlemybusiness_not_germany', data.question_three)

#             # Handle confirmation and signature
#             if data.confirm_form:
#                 lcs = self.page.locator("input#legal_consent_statement--agree")
#                 await lcs.click(force=True)

#             await self.page.fill('#signature', data.signature)

#             logger.info("Form filled successfully")

#         except Exception as e:
#             logger.error(f"Error filling form: {str(e)}")
#             self.errors.append({
#                 'message': f"Error filling form: {str(e)}",
#                 'data': str(e)
#             })
#             raise
#     async def submit_form(self):
#         try:
#             await self.page.click('button.submit-button')
#             await self.page.wait_for_selector('.confirmation-message:not(.hidden)', timeout=10000)
#             logger.info("Form submitted successfully")
#             return True
#         except Exception as e:
#             logger.error(f"Error submitting form: {str(e)}")
#             self.errors.append(
#                 {
#                     'message': f"Error submitting form: {str(e)}",
#                     'data': str(e)
#                 }
#             )
#             raise

#     async def select_language(self, language):
#         try:
#             # Click to open the language selector dropdown
#             language_selector = self.page.locator('div.language-selector-select.sc-select')
#             await language_selector.click()

#             language_option = self.page.locator('li[role="option"][aria-label="Deutsch"]')
#             # print(language_option)
#             await language_option.first.click()

#             # Wait for dropdown to close
#             await self.page.wait_for_selector('div.language-selector-select[aria-expanded="false"]', timeout=5000)
#             logger.info(f"Selected language: {language}")

#         except Exception as e:
#             self.errors.append({
#                 'message': f"Failed to select language: {language}",
#                 'data': str(e)
#             })
#             logger.error(f"Failed to select language: {str(e)}")

#     async def select_language(self, language):
#         try:
#             # Click to open the language selector dropdown
#             language_selector = self.page.locator('div.language-selector-select.sc-select')
#             await language_selector.click()

#             language_option = self.page.locator('li[role="option"][aria-label="Deutsch"]')
#             # print(language_option)
#             await language_option.first.click()

#             # Wait for dropdown to close
#             await self.page.wait_for_selector('div.language-selector-select[aria-expanded="false"]', timeout=5000)
#             logger.info(f"Selected language: {language}")

#         except Exception as e:
#             self.errors.append({
#                 'message': f"Failed to select language: {language}",
#                 'data': str(e)
#             })
#             logger.error(f"Failed to select language: {str(e)}")

# # class LegalFormFiller:
# #     def __init__(self, page):
# #         self.page = page
# #         self.errors = []

# #     async def human_type(self, selector, text):
# #             """Simulates human-like typing with variable delays"""
# #             element = await self.page.query_selector(selector)
# #             if element:
# #                 # Random initial delay before typing
# #                 await self.page.wait_for_timeout(random.randint(100, 300))
                
# #                 for char in text:
# #                     await element.type(char, delay=random.randint(50, 150))
# #                     # Occasional longer pause while typing
# #                     if random.random() < 0.1:
# #                         await self.page.wait_for_timeout(random.randint(100, 300))
# #     async def human_click(self, selector, force=False):
# #         """Simulates human-like clicking with mouse movement"""
# #         element = await self.page.query_selector(selector)
# #         if element:
# #             # Get element position
# #             box = await element.bounding_box()
# #             if box:
# #                 # Move mouse to random position within element
# #                 x = box['x'] + random.uniform(5, box['width'] - 5)
# #                 y = box['y'] + random.uniform(5, box['height'] - 5)
                
# #                 # Move mouse with human-like motion
# #                 await self.page.mouse.move(x, y, steps=random.randint(5, 10))
# #                 await self.page.wait_for_timeout(random.randint(50, 150))
# #                 await self.page.mouse.click(x, y, force=force)

# #     async def select_country(self, country_name):
# #         try:
# #             await self.page.click('div.sc-select')  # Open dropdown
# #             country_name = country_name.capitalize()
# #             # Use an exact match regex to avoid partial matches
# #             country_option = self.page.locator('li[role="option"]').filter(
# #                 has_text=re.compile(f"^{re.escape(country_name)}$"))
# #             await country_option.first.click()  # Click the exact match

# #             await self.page.wait_for_selector('div.sc-select[aria-expanded="false"]', timeout=5000)
# #             logger.info(f"Selected country: {country_name}")
# #             await self.page.click('div.sc-select')  # Close dropdown
# #         except Exception as e:
# #             self.errors.append(
# #                     {
# #                         'message': f"Failed to select country: {country_name}",
# #                         'data': str(e)
# #                     }
# #               )
# #             logger.error(f"Failed to select country: {str(e)}")

#     # async def select_language(self, language):
#     #     try:
#     #         # Click to open the language selector dropdown
#     #         language_selector = self.page.locator('div.language-selector-select.sc-select')
#     #         await language_selector.click()

#     #         language_option = self.page.locator('li[role="option"][aria-label="Deutsch"]')
#     #         # print(language_option)
#     #         await language_option.first.click()

#     #         # Wait for dropdown to close
#     #         await self.page.wait_for_selector('div.language-selector-select[aria-expanded="false"]', timeout=5000)
#     #         logger.info(f"Selected language: {language}")

#     #     except Exception as e:
#     #         self.errors.append({
#     #             'message': f"Failed to select language: {language}",
#     #             'data': str(e)
#     #         })
#     #         logger.error(f"Failed to select language: {str(e)}")

#     # async def fill_form(self, data: FormData) -> None:
#     #     try:

#     #         # Select language
#     #         await self.select_language("Deutsch")
#     #         await self.page.wait_for_timeout(1000)

#     #         # Select country
#             # country_name = "Deutschland" # data.country_of_residence, we are only targeting Germany.
#             # for attempt in range(5):
#             #     try:
#             #         await self.select_country(country_name)
#             #         country_name = country_name.capitalize()

#             #         if attempt == 4:
#             #             country_name = country_name.upper()
#             #         if attempt == 3:
#             #             country_name = country_name.lower()
#             #         break
#             #     except Exception as e:
#             #         logger.warning(f"Failed to select country: {str(e)}. Retrying...")

#     #         eu = self.is_eu_member(country_name)
#     #         # Handle child abuse content section
#     #         if eu and data.is_child_abuse_content:
#     #             confim_cbc = self.page.locator("input#confirm_violate_csae_laws--confirm")
#     #             await confim_cbc.check(force=True)

#     #         # Fill personal information
#     #         if eu and data.is_child_abuse_content and data.remove_child_abuse_content:
#     #             confirm_anc = self.page.locator("input#confirm_to_report_anonymous--confirm")
#     #             await confirm_anc.click(force=True)
#     #             await self.page.fill('#full_name_not_required', data.full_legal_name)
#     #             await self.page.fill('#contact_email_not_required', data.email)
#     #         else:
#     #             await self.page.fill('#full_name', data.full_legal_name)
#     #             await  self.page.fill('#contact_email_noprefill', data.email)

#     #         await self.page.fill('#companyname', data.company_name)
#     #         await self.page.fill('#representedrightsholder', data.company_you_represent)

#             # variant = self.is_special_country(country_name)

#             # if variant:
#             #     country_name_english = "Germany"
#             #     # German form does not have some fields
#             #     search_query = f'input[name="url_box3_geo_{country_name_english.lower()}"]'

#             #     for i, url in enumerate(data.infringing_urls):
#             #         locate = self.page.locator(search_query)
#             #         if i == 0:
#             #             await locate.fill(url)
#             #         else:
#             #             specifier = ''
#             #             sub_specifier = '_2'
#             #             if i > 1:
#             #                 specifier = f'_{i}'
#             #                 sub_specifier = f'_{i+1}'
#             #             search_sub_query = f'input[name="url_box3_googlemybusiness{sub_specifier}"]'
#             #             add_checkbox = self.page.locator(f'input#add_another_url_checkbox{specifier}--add')
#             #             await add_checkbox.check(force=True)
#             #             await self.page.fill(search_sub_query, url)
#             # else:
#             #     url_fields = self.page.locator("div.field.inline-branch input[name='url_box3']")

#             #     # Ensure the number of input fields matches the number of URLs
#             #     for i, url in enumerate(data.infringing_urls):
#             #         if i < url_fields.count():
#             #             await url_fields.nth(i).fill(url)  # Fill the existing field
#             #         else:
#             #             add_additional = self.page.locator("a.add-additional").first  # Click "Add additional field" button
#             #             await add_additional.click(force=True)
#             #             await self.page.locator("div.field.inline-branch input[name='url_box3']").nth(i).fill(
#             #                 url)  # Fill new field
#             #     if data.is_related_to_media:
#             #          ugcy = self.page.locator("label[for='is_geo_ugc_imagery--yes']")
#             #          await ugcy.click(force=True)
#             #     else:
#             #         ugcn = self.page.locator("label[for='is_geo_ugc_imagery--no']")
#             #         await ugcn.click(force=True)


#             # # Fill explanations
#             # await self.page.fill('#legalother_explain_googlemybusiness_not_germany', data.question_one)
#             # await self.page.fill('#legalother_quote', data.question_two)
#             # await self.page.fill('#legalother_quote_googlemybusiness_not_germany', data.question_three)

#             # # Handle confirmation and signature
#             # if data.confirm_form:
#             #     lcs = self.page.locator("input#legal_consent_statement--agree")
#             #     await lcs.click(force=True)

#             # await self.page.fill('#signature', data.signature)

#             # logger.info("Form filled successfully")

#         # except Exception as e:
#         #     logger.error(f"Error filling form: {str(e)}")
#         #     self.errors.append(
#         #         {
#         #             'message': f"Error filling form: {str(e)}",
#         #             'data': str(e)
#         #         }
#         #     )
#         #     raise

#     # async def submit_form(self):
#     #     try:
#     #         await self.page.click('button.submit-button')
#     #         await self.page.wait_for_selector('.confirmation-message:not(.hidden)', timeout=10000)
#     #         logger.info("Form submitted successfully")
#     #         return True
#     #     except Exception as e:
#     #         logger.error(f"Error submitting form: {str(e)}")
#     #         self.errors.append(
#     #             {
#     #                 'message': f"Error submitting form: {str(e)}",
#     #                 'data': str(e)
#     #             }
#     #         )
#     #         raise

# async def automate_form_fill(data: FormData):
#     playwright = await async_playwright().start()
    
#     try:
#         # Initialize browser with anti-detection configuration
#         browser = await playwright.chromium.launch(
#             headless=False,
#             **BrowserConfig.get_browser_config()
#         )
        
#         # Create context with enhanced configuration
#         context = await browser.new_context(**BrowserConfig.get_context_config())
        
#         # Add anti-automation scripts
#         await context.add_init_script("""
#             // Mask automation indicators
#             Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
#             Object.defineProperty(navigator, 'plugins', {
#                 get: () => Array(Math.floor(Math.random() * 7) + 1).fill().map(() => ({
#                     name: Math.random().toString(36).slice(2),
#                     description: Math.random().toString(36).slice(2),
#                     filename: Math.random().toString(36).slice(2)
#                 }))
#             });
            
#             // Add random screen properties
#             # Object.defineProperty(window, 'screenX', {get: () => Math.floor(Math.random() * 100)});
#             # Object.defineProperty(window, 'screenY', {get: () => Math.floor(Math.random() * 100)});
            
#             // Track mouse position
#             window.mouseX = 0;
#             window.mouseY = 0;
#             document.addEventListener('mousemove', (e) => {
#                 window.mouseX = e.clientX;
#                 window.mouseY = e.clientY;
#             });
#         """)

#         # Create page and navigate
#         page = await context.new_page()
        
#         # Add random mouse movements
#         await page.evaluate("""
#             setInterval(() => {
#                 const event = new MouseEvent('mousemove', {
#                     clientX: Math.random() * window.innerWidth,
#                     clientY: Math.random() * window.innerHeight,
#                     bubbles: true
#                 });
#                 document.dispatchEvent(event);
#             }, 1000);
#         """)

#         # Navigate to form with random timing
#         await page.goto(Config.FORM_URL, wait_until='networkidle')
#         await asyncio.sleep(random.uniform(2, 4))

#         # Initialize and execute form filling
#         form_filler = LegalFormFiller(page)
#         await form_filler.fill_form(data)
        
#         # Add final delay before submission
#         await asyncio.sleep(random.uniform(1, 2))
#         await form_filler.submit_form()
        
#         # Wait for confirmation with timeout
#         await page.wait_for_timeout(random.randint(8000, 12000))

#     except Exception as e:
#         logger.error(f"Error automating form fill: {str(e)}")
#         raise
#     finally:
#         await browser.close()
#         await playwright.stop()

# def main():
#     # Testing data. Replace with actual data
#     print("comment this to run the script")
#     return
#     # with sync_playwright() as p:
#     #     browser = p.chromium.launch(headless=False)
#     #     page = browser.new_page()
#     #
#     #     # Navigate to form
#     #     page.goto(Config.FORM_URL)
#     #
#     #
#     #     form_data = FormData(
#     #         countryOfResidence="germany",
#     #         isChildAbuseContent=True,
#     #         removeChildAbuseContent=True,
#     #         fullLegalName="John Doe",
#     #         companyName="Example Corp",
#     #         companyYouRepresent="",
#     #         email="john@example.com",
#     #         infringingUrls=["https://example.com/page1", "https://example.com/page2", "https://example.com/page2","https://example.com/page2"],
#     #         isRelatedToMedia=True,
#     #         questionOne="This content violates...",
#     #         questionTwo="The specific text...",
#     #         questionThree="Additional details...",
#     #         confirmForm=True,
#     #         signature="John Doe"
#     #     )

#         # form_filler = LegalFormFiller(page)
#         # form_filler.fill_form(form_data)
#         #
#         # # Optional: Wait for manual review before submitting
#         # page.pause()
#         #
#         # browser.close()


# if __name__ == "__main__":
#     main()