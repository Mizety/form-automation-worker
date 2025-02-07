import sys

from playwright.async_api import async_playwright
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from config import Config

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

    @staticmethod
    def is_eu_member(country):
        eu_countries = {
            'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
            'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
            'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta',
            'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia',
            'Spain', 'Sweden'
        }
        return country in eu_countries

    @staticmethod
    def is_special_country(country):
        special_countries = {
            'Germany',
        }
        return country in special_countries

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

    async def fill_form(self, data: FormData) -> None:
        try:
            # Select country
            country_name = data.country_of_residence
            for attempt in range(5):
                try:
                    await self.select_country(data.country_of_residence)
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
                confim_cbc = self.page.locator("input#confirm_violate_csae_laws--confirm")
                await confim_cbc.check(force=True)

            # Fill personal information
            if eu and data.is_child_abuse_content and data.remove_child_abuse_content:
                confirm_anc = self.page.locator("input#confirm_to_report_anonymous--confirm")
                await confirm_anc.click(force=True)
                await self.page.fill('#full_name_not_required', data.full_legal_name)
                await self.page.fill('#contact_email_not_required', data.email)
            else:
                await self.page.fill('#full_name', data.full_legal_name)
                await  self.page.fill('#contact_email_noprefill', data.email)

            await self.page.fill('#companyname', data.company_name)
            await self.page.fill('#representedrightsholder', data.company_you_represent)

            variant = self.is_special_country(country_name)

            if variant:
                # German form does not have some fields
                search_query = f'input[name="url_box3_geo_{country_name.lower()}"]'

                for i, url in enumerate(data.infringing_urls):
                    locate = self.page.locator(search_query)
                    if i == 0:
                        await locate.fill(url)
                    else:
                        specifier = ''
                        sub_specifier = '_2'
                        if i > 1:
                            specifier = f'_{i}'
                            sub_specifier = f'_{i+1}'
                        search_sub_query = f'input[name="url_box3_googlemybusiness{sub_specifier}"]'
                        add_checkbox = self.page.locator(f'input#add_another_url_checkbox{specifier}--add')
                        await add_checkbox.check(force=True)
                        await self.page.fill(search_sub_query, url)
            else:
                url_fields = self.page.locator("div.field.inline-branch input[name='url_box3']")

                # Ensure the number of input fields matches the number of URLs
                for i, url in enumerate(data.infringing_urls):
                    if i < url_fields.count():
                        await url_fields.nth(i).fill(url)  # Fill the existing field
                    else:
                        add_additional = self.page.locator("a.add-additional").first  # Click "Add additional field" button
                        await add_additional.click(force=True)
                        await self.page.locator("div.field.inline-branch input[name='url_box3']").nth(i).fill(
                            url)  # Fill new field
                if data.is_related_to_media:
                     ugcy = self.page.locator("label[for='is_geo_ugc_imagery--yes']")
                     await ugcy.click(force=True)
                else:
                    ugcn = self.page.locator("label[for='is_geo_ugc_imagery--no']")
                    await ugcn.click(force=True)


            # Fill explanations
            await self.page.fill('#legalother_explain_googlemybusiness_not_germany', data.question_one)
            await self.page.fill('#legalother_quote', data.question_two)
            await self.page.fill('#legalother_quote_googlemybusiness_not_germany', data.question_three)

            # Handle confirmation and signature
            if data.confirm_form:
                lcs = self.page.locator("input#legal_consent_statement--agree")
                await lcs.click(force=True)

            await self.page.fill('#signature', data.signature)

            logger.info("Form filled successfully")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            self.errors.append(
                {
                    'message': f"Error filling form: {str(e)}",
                    'data': str(e)
                }
            )
            raise

    async def submit_form(self):
        try:
            await self.page.click('button.submit-button')
            await self.page.wait_for_selector('.confirmation-message:not(.hidden)', timeout=10000)
            logger.info("Form submitted successfully")
            return True
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            self.errors.append(
                {
                    'message': f"Error submitting form: {str(e)}",
                    'data': str(e)
                }
            )
            raise

async def automate_form_fill(data: FormData):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=Config.BROWSER_HEADLESS)
    try:
        page = await browser.new_page()

        await page.context.grant_permissions(['geolocation'])
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })

        # Navigate to form
        await page.goto(Config.FORM_URL)

        form_filler = LegalFormFiller(page)
        await form_filler.fill_form(data)
        await page.wait_for_timeout(2000)
        await form_filler.submit_form()
        await page.wait_for_timeout(10000)

    except Exception as e:
        logger.error(f"Error automating form fill: {str(e)}")
        raise
    finally:
        await browser.close()
        await playwright.stop()

def main():
    # Testing data. Replace with actual data
    print("comment this to run the script")
    return
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False)
    #     page = browser.new_page()
    #
    #     # Navigate to form
    #     page.goto(Config.FORM_URL)
    #
    #
    #     form_data = FormData(
    #         countryOfResidence="germany",
    #         isChildAbuseContent=True,
    #         removeChildAbuseContent=True,
    #         fullLegalName="John Doe",
    #         companyName="Example Corp",
    #         companyYouRepresent="",
    #         email="john@example.com",
    #         infringingUrls=["https://example.com/page1", "https://example.com/page2", "https://example.com/page2","https://example.com/page2"],
    #         isRelatedToMedia=True,
    #         questionOne="This content violates...",
    #         questionTwo="The specific text...",
    #         questionThree="Additional details...",
    #         confirmForm=True,
    #         signature="John Doe"
    #     )

        # form_filler = LegalFormFiller(page)
        # form_filler.fill_form(form_data)
        #
        # # Optional: Wait for manual review before submitting
        # page.pause()
        #
        # browser.close()


if __name__ == "__main__":
    main()