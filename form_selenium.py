import os
import random
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time
from config import Config
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
import capsolver

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
    remove_child_abuse_content: bool = field(metadata={"alias": "removeChildAbuseContent"})
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


class FormFiller:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.errors = []

    @staticmethod
    def is_eu_member(country):
        eu_countries = {
            'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
            'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
            'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta',
            'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia',
            'Spain', 'Sweden', 'Deutschland'
        }
        return country in eu_countries

    @staticmethod
    def is_special_country(country):
        special_countries = {
            'Germany', 'Deutschland'
        }
        return country in special_countries

    def select_country(self, country_name):
        try:
            # Open dropdown
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.sc-select'))).click()
            
            country_name = country_name.capitalize()
            # Find country option using exact match
            country_options = self.driver.find_elements(By.CSS_SELECTOR, 'li[role="option"]')
            for option in country_options:
                if option.text.strip() == country_name:
                    option.click()
                    break
            
            # Wait for dropdown to close
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.sc-select[aria-expanded="false"]')))
            logger.info(f"Selected country: {country_name}")
            
        except Exception as e:
            self.errors.append({
                'message': f"Failed to select country: {country_name}",
                'data': str(e)
            })
            logger.error(f"Failed to select country: {str(e)}")
            raise

    def select_language(self, language):
        try:
            language_selector = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'div.language-selector-select.sc-select')))
            language_selector.click()

            language_option = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'li[role="option"][aria-label="Deutsch"]')))
            language_option.click()

            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div.language-selector-select[aria-expanded="false"]')))
            logger.info(f"Selected language: {language}")

        except Exception as e:
            self.errors.append({
                'message': f"Failed to select language: {language}",
                'data': str(e)
            })
            logger.error(f"Failed to select language: {str(e)}")

    def click_checkbox(self, selector):
        """Helper method to safely click checkboxes using JavaScript"""
        checkbox = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        self.driver.execute_script("arguments[0].click(); arguments[0].checked = true;", checkbox)

    def fill_form(self, data: FormData):
        try:
            # Select language
            self.select_language("Deutsch")
            time.sleep(1)  # Replace with explicit wait if possible

            # Select country
            country_name = "Deutschland"
            for attempt in range(5):
                try:
                    self.select_country(country_name)
                    country_name = country_name.capitalize()
                    if attempt == 4:
                        country_name = country_name.upper()
                    if attempt == 3:
                        country_name = country_name.lower()
                    break
                except Exception as e:
                    logger.warning(f"Failed to select country: {str(e)}. Retrying...")

            eu = self.is_eu_member(country_name)
            
            # Handle child abuse content section
            if eu and data.is_child_abuse_content:
                self.click_checkbox("input#confirm_violate_csae_laws--confirm")

            # Fill personal information
            if eu and data.is_child_abuse_content and data.remove_child_abuse_content:
                self.click_checkbox("input#confirm_to_report_anonymous--confirm")
                self.driver.find_element(By.CSS_SELECTOR, '#full_name_not_required').send_keys(data.full_legal_name)
                self.driver.find_element(By.CSS_SELECTOR, '#contact_email_not_required').send_keys(data.email)
            else:
                self.driver.find_element(By.CSS_SELECTOR, '#full_name').send_keys(data.full_legal_name)
                self.driver.find_element(By.CSS_SELECTOR, '#contact_email_noprefill').send_keys(data.email)

            self.driver.find_element(By.CSS_SELECTOR, '#companyname').send_keys(data.company_name)
            self.driver.find_element(By.CSS_SELECTOR, '#representedrightsholder').send_keys(data.company_you_represent)

            variant = self.is_special_country(country_name)

            if variant:
                country_name_english = "Germany"
                search_query = f'input[name="url_box3_geo_{country_name_english.lower()}"]'

                for i, url in enumerate(data.infringing_urls):
                    if i == 0:
                        self.driver.find_element(By.CSS_SELECTOR, search_query).send_keys(url)
                    else:
                        specifier = ''
                        sub_specifier = '_2'
                        if i > 1:
                            specifier = f'_{i}'
                            sub_specifier = f'_{i+1}'
                        search_sub_query = f'input[name="url_box3_googlemybusiness{sub_specifier}"]'
                        self.click_checkbox(f'input#add_another_url_checkbox{specifier}--add')
                        self.driver.find_element(By.CSS_SELECTOR, search_sub_query).send_keys(url)
            else:
                url_fields = self.driver.find_elements(By.CSS_SELECTOR, "div.field.inline-branch input[name='url_box3']")

                # Ensure the number of input fields matches the number of URLs
                for i, url in enumerate(data.infringing_urls):
                    if i < len(url_fields):
                        url_fields[i].send_keys(url)  # Fill the existing field
                    else:
                        add_additional = self.driver.find_element(By.CSS_SELECTOR, "a.add-additional").first  # Click "Add additional field" button
                        add_additional.click()
                        self.driver.find_element(By.CSS_SELECTOR, "div.field.inline-branch input[name='url_box3']").send_keys(
                            url)  # Fill new field
            
            if data.is_related_to_media:
                self.click_checkbox("input#is_geo_ugc_imagery--yes")
            else:
                 self.click_checkbox("input#is_geo_ugc_imagery--no")
        

            # Fill explanations
            self.driver.find_element(By.CSS_SELECTOR, '#legalother_explain_googlemybusiness_not_germany').send_keys(data.question_one)
            self.driver.find_element(By.CSS_SELECTOR, '#legalother_quote').send_keys(data.question_two)
            self.driver.find_element(By.CSS_SELECTOR, '#legalother_quote_googlemybusiness_not_germany').send_keys(data.question_three)

            # Handle send notice to author
            if(data.send_notice_to_author):
                self.click_checkbox("input#fwd_notice_consent--disagree")

            # Handle confirmation and signature
            if data.confirm_form:
                self.click_checkbox("input#legal_consent_statement--agree")

            # Fill signature
            self.driver.find_element(By.CSS_SELECTOR, '#signature').send_keys(data.signature)
            logger.info("Form filled successfully")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            self.errors.append({
                'message': f"Error filling form: {str(e)}",
                'data': str(e)
            })
            raise

    def submit_form(self):
        try:
            # More specific CSS selector targeting the exact button classes
            submit_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button.submit-button.material2-button.material2-button--filled')))
            
            try:
                submit_button.click()
                logger.info("Clicked submit button")
                # Wait for success message or redirect
                success_indicator = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.confirmation-message:not(.hidden)'))
                )
                logger.info("Form submitted successfully")
                
            except TimeoutException:
                logger.info("Timeout occurred - likely due to captcha")
                # Try submitting again
                try:
                    time.sleep(10)
                    submit_button.click()
                    # Wait for success message with a longer timeout
                    success_indicator = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.confirmation-message:not(.hidden)'))
                    )
                    logger.info("Form submitted successfully after captcha")
                except Exception as e:
                    logger.error(f"Failed to submit form after captcha: {str(e)}")
                    raise
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            self.errors.append({
                'message': f"Error submitting form: {str(e)}",
                'data': str(e)
            })
            raise

    def capsolver_captcha(self):
        capsolver.api_key = Config.CAPSOLVER_API_KEY
        solution = capsolver.solve({
            "type": "ReCaptchaV2TaskProxyLess",
            "websiteURL": Config.FORM_URL,
            "websiteKey": Config.CAPSOLVER_WEBSITE_KEY,
            # "isInvisible": True
        })

        token = solution["gRecaptchaResponse"]
        print(solution)
        if token:
            # Switch to the reCAPTCHA iframe first
            iframe = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'iframe[title="reCAPTCHA"]')))
            self.driver.switch_to.frame(iframe)
            
            # Set the token
            script = """
            document.getElementById('recaptcha-token').value = arguments[0];
            """
            self.driver.execute_script(script, token)
            
            # Switch back to default content
            self.driver.switch_to.default_content()
            
            # Now set the response in the main frame
            script = """
            document.querySelector('[name="g-recaptcha-response"]').value = arguments[0];
            """
            self.driver.execute_script(script, token)
            
            logger.info("Captcha token set successfully")
            return token
        else:
            logger.error("Failed to solve captcha")
            return None

    def get_errors(self) -> List[Dict[str, str]]:
        return self.errors

async def automate_form_fill_new(data: FormData):
    chrome_options = Options()
    # Enhanced anti-detection options
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--mute-audio')
    
    # Random window size to avoid detection
    window_width = random.randint(1050, 1200)
    window_height = random.randint(800, 1000)
    chrome_options.add_argument(f'--window-size={window_width},{window_height}')
    
    # Add random user agent
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    # Additional stealth options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('prefs', {
        'credentials_enable_service': False,
        'profile.password_manager_enabled': False,
        'profile.default_content_setting_values.notifications': 2,
        'intl.accept_languages': 'en-US,en',
    })
    extension_path = os.path.abspath('./extension')
    chrome_options.add_argument(f'--load-extension={extension_path}')
    # Initialize the driver with automatic ChromeDriver management
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # Apply stealth settings
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        run_on_insecure_origins=True
    )
    
    try:
        # Add random delays between actions
        def random_delay():
            time.sleep(random.uniform(1, 3))
        
        driver.get(Config.FORM_URL)
        random_delay()
        
        # Initialize form filler
        form_filler = FormFiller(driver)
        
        
        # Fill and submit form
        form_filler.fill_form(data)
        form_filler.submit_form()
        
    finally:
        # Clean up
        driver.quit()

def main():
    print("Starting form automation... no you didn't get it call me correctly.")

    return;

if __name__ == "__main__":
    main()