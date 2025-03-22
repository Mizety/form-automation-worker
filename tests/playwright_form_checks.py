import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from form_playwright import FormData, automate_form_fill_new
 

async def remove_user_data_dir(directory):
    import shutil
    if os.path.exists(directory):
        shutil.rmtree(directory)


if __name__ == "__main__":
    asyncio.run(automate_form_fill_new(FormData(
        id="Variant Test 1",
        country_of_residence="Germany",
        email="test@test.com",
        full_legal_name="John Doe",
        company_name="Example Corp",
        company_you_represent="nmp",
        infringing_urls=["https://maps.app.goo.gl/dAYT5CocEvWCy1QW6"],
        is_related_to_media=False, # deprecated, its present but not visible
        question_one="This content violates...",
        question_two="The specific text...",
        question_three="Additional details...",
        confirm_form=True,
        send_notice_to_author=True, # deprecated
        signature="John Doe",
        is_child_abuse_content=True,
        remove_child_abuse_content=True
    ), False))

    asyncio.run(automate_form_fill_new(FormData(
            id="Variant Test 2",
            country_of_residence="Germany",
            email="test@test.com",
            full_legal_name="John Doe",
            company_name="Example Corp",
            company_you_represent="nmp",
            infringing_urls=["https://maps.app.goo.gl/dAYT5CocEvWCy1QW6"],
            is_related_to_media=False, # deprecated, its present but not visible
            question_one="This content violates...",
            question_two="The specific text...",
            question_three="Additional details...",
            confirm_form=False,
            send_notice_to_author=False, # deprecated
            signature="John Doe",
            is_child_abuse_content=False,
            remove_child_abuse_content=False
        ), False))
    asyncio.run(automate_form_fill_new(FormData(
            id="Variant Test 3 with full map link",
            country_of_residence="Germany",
            email="test@test.com",
            full_legal_name="John Doe",
            company_name="Example Corp",
            company_you_represent="nmp",
            infringing_urls=["https://maps.app.goo.gl/dAYT5CocEvWCy1QW6", "https://www.google.com/maps/contrib/102614850577731744343/place/ChIJRYcmrSFxsEcRwfSHxlsSV8I/@52.4077888,9.6600101,12z/data=!4m6!1m5!8m4!1e1!2s102614850577731744343!3m1!1e1?hl=de&entry=ttu&g_ep=EgoyMDI1MDMxOS4xIKXMDSoJLDEwMjExNDUzSAFQAw%3D%3D"],
            is_related_to_media=False, # deprecated, its present but not visible
            question_one="This content violates...",
            question_two="The specific text...",
            question_three="Additional details...",
            confirm_form=False,
            send_notice_to_author=False, # deprecated
            signature="John Doe",
            is_child_abuse_content=False,
            remove_child_abuse_content=False
        ), False))
    


    
