import asyncio
import random
import sys
from playwright.async_api import async_playwright, TimeoutError as TimeoutException
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional
import os
from config import Config
from discord_notification import notify_to_discord, notify_to_discord_with_failed_content

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FormData:
    country_of_residence: str = field(metadata={"alias": "countryOfResidence"})
    is_child_abuse_content: bool = field(metadata={"alias": "isChildAbuseContent"})
    remove_child_abuse_content: bool = field(metadata={"alias": "removeChildAbuseContent"}) # If we are removing anonymously or not. Its a bit misleading. Please check documentation.
    full_legal_name: str = field(metadata={"alias": "fullLegalName"})
    company_name: str = field(metadata={"alias": "CompanyName"})
    company_you_represent: str = field(metadata={"alias": "CompanyYouRepresent"})
    email: str
    infringing_urls: List[str] = field(metadata={"alias": "InfringingUrls"})
    is_related_to_media: bool = field(metadata={"alias": "isRelatedToMedia"})
    question_one: str = field(metadata={"alias": "QuestionOne"})
    question_two: str = field(metadata={"alias": "QuestionTwo"})
    question_three: str = field(metadata={"alias": "QuestionThree"})
    confirm_form: bool = field(metadata={"alias": "confirmForm"})
    send_notice_to_author: bool = field(metadata={"alias": "sendNoticeToAuthor"})
    signature: str
    id: str
    status: Optional[str] = None
    error: Optional[str] = None
    retry_attempts: Optional[int] = field(default=None, metadata={"alias": "retryAtempts"})
    created_at: Optional[str] = field(metadata={"alias": "createdAt"}, default=None)
    updated_at: Optional[str] = field(metadata={"alias": "updatedAt"}, default=None)


class LegalFormFiller:
    def __init__(self, page):
        self.page = page
        self.errors = []

    async def select_country(self, country_name):
        try:
            await self.page.click('div.sc-select')  # Open dropdown
            country_name = country_name.capitalize()
            # Use an exact match regex to avoid partial matches
            country_option = self.page.locator('li[role="option"]').filter(
                has_text=re.compile(f"^{re.escape(country_name)}$"))
            await country_option.first.click()  # Click the exact match

            await self.page.wait_for_selector('div.sc-select[aria-expanded="false"]', timeout=5000)
            logger.info(f"Selected country: {country_name}")
            await self.page.click('div.sc-select')  # Close dropdown
        except Exception as e:
            self.errors.append(
                    {
                        'message': f"Failed to select country: {country_name}",
                        'data': str(e)
                    }
              )
            logger.error(f"Failed to select country: {str(e)}")
            raise

    async def handle_child_abuse_content(self, is_child_abuse_content, remove_child_abuse_content):
        """Handle child abuse content section of the form."""
        try:
            if is_child_abuse_content:
                confirm_cbc = self.page.locator("input#confirm_violate_csae_laws--confirm")
                await confirm_cbc.scroll_into_view_if_needed()
                await confirm_cbc.check(force=True)
                
                if remove_child_abuse_content:
                    confirm_anc = self.page.locator("input#confirm_to_report_anonymous--confirm")
                    await confirm_anc.scroll_into_view_if_needed()
                    await confirm_anc.click(force=True)
                    
            logger.info("Child abuse content section handled successfully")
        except Exception as e:
            self.errors.append({
                'message': "Failed to handle child abuse content section",
                'data': str(e)
            })
            logger.error(f"Failed to handle child abuse content section: {str(e)}")
            raise
    
    async def fill_personal_info(self, full_legal_name, email, is_anonymous=False):
        """Fill personal information section of the form."""
        try:
        
            name_locator = self.page.locator('#full_name')
            await name_locator.scroll_into_view_if_needed()
            await name_locator.fill(full_legal_name)
            
            if not is_anonymous:
                email_locator = self.page.locator('#contact_email_noprefill')
                await email_locator.scroll_into_view_if_needed()
                await email_locator.fill(email)
                
            logger.info("Personal information filled successfully")
        except Exception as e:
            self.errors.append({
                'message': "Failed to fill personal information",
                'data': str(e)
            })
            logger.error(f"Failed to fill personal information: {str(e)}")
            raise
    
    async def fill_company_info(self, company_name, company_you_represent):
        """Fill company information section of the form."""
        try:
            company_name_locator = self.page.locator('#companyname')
            await company_name_locator.scroll_into_view_if_needed()
            await company_name_locator.fill(company_name)
            
            company_represent_locator = self.page.locator('#representedrightsholder')
            await company_represent_locator.scroll_into_view_if_needed()
            await company_represent_locator.fill(company_you_represent)
            
            logger.info("Company information filled successfully")
        except Exception as e:
            self.errors.append({
                'message': "Failed to fill company information",
                'data': str(e)
            })
            logger.error(f"Failed to fill company information: {str(e)}")
            raise
    
    async def fill_infringing_urls(self, urls, is_german_variant=True):
        """Fill infringing URLs section of the form."""
        try:
            search_query = 'input[name="url_box3_geo_reviews"]'
                
            for i, url in enumerate(urls):
                    locate = self.page.locator(search_query)
                    if i == 0:
                        await locate.fill(url)
                    else:
                        add_checkbox = self.page.locator('div[data-frd-identifier="IDENTIFIER_LEGAL_REMOVALS_TARGET"]').locator("a.add-additional").first
                        
                        if await add_checkbox.is_visible():
                            await add_checkbox.click(force=True)
                        else:
                            logger.warning("Add additional URL button is not visible")
                        
                        url_field = self.page.locator(search_query).nth(i)
                        if await url_field.is_visible():
                            await url_field.fill(url)
                        else:
                            logger.warning(f"URL input field {i} is not visible")
            logger.info(f"Filled {len(urls)} infringing URLs successfully")
        except Exception as e:
            self.errors.append({
                'message': "Failed to fill infringing URLs",
                'data': str(e)
            })
            logger.error(f"Failed to fill infringing URLs: {str(e)}")
            raise
    
    async def handle_media_related_question(self, is_related_to_media):
        """Handle the question about media relation. It is marked as deprecated."""
        try:
            if is_related_to_media:
                ugcyes = self.page.locator("label[for='is_geo_ugc_imagery--yes']")
                if await ugcyes.is_visible():
                    await ugcyes.click(force=True)
            else:
                ngcno = self.page.locator("label[for='is_geo_ugc_imagery--no']")
                if await ngcno.is_visible():
                    await ngcno.click(force=True)
                    
            logger.info(f"Media relation question answered: {is_related_to_media}")
        except Exception as e:
            self.errors.append({
                'message': "Failed to handle media relation question",
                'data': str(e)
            })
            logger.error(f"Failed to handle media relation question: {str(e)}")
            raise
    
    async def fill_explanations(self, question_one, question_two, question_three, is_german_variant=True):
        """Fill explanation text areas in the form."""
        try:
            suffix = "" if is_german_variant else "_not_germany"
            
            query_q1 = f'textarea#legalother_explain_googlemybusiness{suffix}'
            q1_locator = self.page.locator(query_q1)
            await q1_locator.scroll_into_view_if_needed()
            await q1_locator.fill(question_one)
            
            q2_locator = self.page.locator('textarea#legalother_quote')
            await q2_locator.scroll_into_view_if_needed()
            await q2_locator.fill(question_two)
            
            query_q3 = f'textarea#legalother_quote_googlemybusiness{suffix}'
            q3_locator = self.page.locator(query_q3)
            await q3_locator.scroll_into_view_if_needed()
            await q3_locator.fill(question_three)
            
            logger.info("Explanations filled successfully")
        except Exception as e:
            self.errors.append({
                'message': "Failed to fill explanations",
                'data': str(e)
            })
            logger.error(f"Failed to fill explanations: {str(e)}")
            raise
    
    async def handle_consent_and_signature(self, send_notice_to_author, confirm_form, signature):
        """Handle consent checkboxes and signature field."""
        try:
            if confirm_form:
                lcs = self.page.locator("input#legal_consent_statement--agree")
                await lcs.scroll_into_view_if_needed()
                await lcs.click(force=True)
            
            signature_locator = self.page.locator('#signature')
            await signature_locator.scroll_into_view_if_needed()
            await signature_locator.fill(signature)
            
            logger.info("Consent and signature handled successfully")
        except Exception as e:
            self.errors.append({
                'message': "Failed to handle consent and signature",
                'data': str(e)
            })
            logger.error(f"Failed to handle consent and signature: {str(e)}")
            raise

    async def fill_form(self, data: FormData, screenshot_path: str = None, variantGermany: bool = True, type: int = 1) -> None:
        try:
            # Select country
            country_name = "Deutschland"  # We are only targeting Germany
            for attempt in range(5):
                try:
                    await self.select_country(country_name)
                    break
                except Exception as e:
                    if attempt == 3:
                        country_name = country_name.lower()
                    elif attempt == 4:
                        country_name = country_name.upper()
                    logger.warning(f"Failed to select country: {str(e)}. Retrying...")

            await self.page.wait_for_timeout(3000)
            
            # Handle child abuse content section
            await self.handle_child_abuse_content(data.is_child_abuse_content, data.remove_child_abuse_content)
            
            await self.page.wait_for_timeout(1000)
            
            # Fill personal information
            is_anonymous = data.is_child_abuse_content and data.remove_child_abuse_content
            await self.fill_personal_info(data.full_legal_name, data.email, is_anonymous)
            
            # Fill company information
            await self.fill_company_info(data.company_name, data.company_you_represent)
            
            await self.page.wait_for_timeout(1000)
            
            # Fill infringing URLs
            await self.fill_infringing_urls(data.infringing_urls, is_german_variant= (variantGermany))
            
            # Handle media related question
            try:
                await self.handle_media_related_question(data.is_related_to_media)
            except Exception as e:
                logger.error(f"Media related question not visible, its marked as deprecated.")
            
            await self.page.wait_for_timeout(1000)
            
            # Fill explanations
            await self.fill_explanations(
                data.question_one, 
                data.question_two, 
                data.question_three, 
                is_german_variant=variantGermany
            )
            
            await self.page.wait_for_timeout(1000)
            
            # Handle consent and signature
            await self.handle_consent_and_signature(
                data.send_notice_to_author,
                data.confirm_form,
                data.signature
            )

            logger.info("Form filled successfully but yet to submit")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            await self.page.screenshot(path=screenshot_path)
            notify_to_discord("Error filling form", str(e), screenshot_path, type=type)
            self.errors.append({
                'message': f"Error filling form: {str(e)}",
                'data': str(e)
            })
            raise

    async def submit_form(self, screenshot_path: str = None):
        try:
            submit_button = self.page.locator('button.submit-button')
            confirmation_message = self.page.locator('.confirmation-message:not(.hidden)')
                
            try:
                await submit_button.scroll_into_view_if_needed()
                await submit_button.click()
                await confirmation_message.wait_for(timeout=10000)
                logger.info("Form submitted successfully")
            except TimeoutException:
                logger.info("Timeout occurred - likely due to captcha")
                # Try submitting again
                try:
                    await self.page.wait_for_timeout(15000)
                    await submit_button.scroll_into_view_if_needed()
                    await submit_button.click()
                    await confirmation_message.wait_for(timeout=12000)
                    logger.info("Form submitted successfully after captcha")
                except Exception as e:
                    await self.page.screenshot(path=screenshot_path)
                    notify_to_discord("Error submitting form", str(e), screenshot_path)
                    logger.error(f"Failed to submit form after captcha: {str(e)}")
                    raise
                 
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            self.errors.append(
                {
                    'message': f"Error submitting form: {str(e)}",
                    'data': str(e)
                }
            )
            raise

async def automate_form_fill_new(data: FormData, submit_form: bool = True):

    # Get absolute path to extension directory
    extension_path = os.path.abspath('./extension')
    user_data_dir = os.path.abspath('./users/user_data' + data.id)
    
    user_agent_strings = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=Config.BROWSER_HEADLESS,
            args=[f'--disable-extensions-except={extension_path}',
                f'--load-extension={extension_path}',   
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
        )
    
        # Add browser extension
        
        try:
            page = await browser.new_page()
            urls = []
            for url in data.infringing_urls:
                newUrl = await check_url(url, page, data.id , type = 1 if submit_form else 2) 
                if newUrl != "":
                    urls.append(newUrl)
                else:
                    logger.warning(f"No valid url found for {url}")
                    notify_to_discord("Invalid url found, will continue with next url for ID: " + data.id, type= 1 if submit_form else 2)
            data.infringing_urls = urls

            if len(data.infringing_urls) == 0:
                logger.error(f"No valid urls found for {data.id}")
                notify_to_discord("No valid urls found for ID: " + data.id, type= 1 if submit_form else 2)
                raise Exception(f"No valid urls found for {data.id}")
            # Navigate to form
            await page.goto(Config.FORM_URL, wait_until='networkidle')
            await page.wait_for_timeout(1000)  # Ensure page is fully loaded
            form_filler = LegalFormFiller(page)
            await form_filler.fill_form(data, screenshot_path="images/type_1_"+data.id+".png", variantGermany=Config.VARIANT_GERMANY, type = 1 if submit_form else 2)
            await page.wait_for_timeout(2000)
            if submit_form:
                await form_filler.submit_form(screenshot_path="images/type_2_"+data.id+".png")
            message = " Successfully completed form for: " + data.id
            notify_to_discord(message , type= 1 if submit_form else 2)
            # await page.pause()

        except Exception as e:
            logger.error(f"Error automating form fill: {str(e)}")
            notify_to_discord_with_failed_content(f"Error automating form fill: {str(e)}", True, data.id, [] , type = 1 if submit_form else 2)
            raise
        finally:
            await browser.close()
            await playwright.stop()
    except Exception as e:
        logger.error(f"Error automating form fill: {str(e)}")
        raise
    finally:
        await remove_user_data_dir(user_data_dir)

async def check_url(url, page, id, type: int = 1) -> str:
    try:
        if "https://maps.app.goo.gl" in url:
            return url
        elif "https://www.google.com/maps/reviews" in url or "https://www.google.com/maps/contrib" in url:
            await page.goto(url)
            await page.wait_for_timeout(1000)
            # we need to check if cookie detected is present and if so, click on it 
            cookie_detected = page.locator('input[value="Alle akzeptieren"]')
            if await cookie_detected.count() > 0 and await cookie_detected.first.is_visible():
                await cookie_detected.first.click(force=True)
            
            await page.click('button.PP3Y3d', force=True)
            await page.wait_for_timeout(1000)
            
            await page.click('div.fxNQSd', force=True) 
            await page.wait_for_timeout(1000)
            
            url_locator = page.locator('input.vrsrZe')
            url = await url_locator.input_value()
            logger.info(f"URL: {url}")
            if url.startswith("https://maps.app.goo.gl/"):
                return url
            else:
                return ""
        else:
            return ""
    except Exception as e:
        logger.error(f"Error checking url: {str(e)}")
        await page.screenshot(path=f"images/type_3_{id}.png")
        notify_to_discord("Error checking url", str(e), f"images/type_3_{id}.png", type=type)
        return ""  # Return empty string on error, not False


async def remove_user_data_dir(directory):
    import shutil
    if os.path.exists(directory):
        shutil.rmtree(directory)

def main():
    # Testing data. Replace with actual data
    print("comment this to run the script")
    # asyncio.run(automate_form_fill_new(FormData(
    #     id="1234567890",
    #     country_of_residence="Germany",
    #     email="test@test.com",
    #     full_legal_name="John Doe",
    #     company_name="Example Corp",
    #     company_you_represent="nmp",
    #     infringing_urls=["https://maps.app.goo.gl/dAYT5CocEvWCy1QW6", "https://maps.app.goo.gl/dAYT5CocEvWCy1QW6"],
    #     is_related_to_media=False, # deprecated, its present but not visible
    #     question_one="This content violates...",
    #     question_two="The specific text...",
    #     question_three="Additional details...",
    #     confirm_form=True,
    #     send_notice_to_author=True, # deprecated
    #     signature="John Doe",
    #     is_child_abuse_content=True,
    #     remove_child_abuse_content=True
    # ), False))
    return


if __name__ == "__main__":
    main()
    # notify_to_discord("Test", "Test", "images/type_3_1234567890.png")
    # notify_to_discord("Passed ", )