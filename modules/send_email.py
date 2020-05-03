import requests
import re
from collections import Iterable
import xml.etree.ElementTree as ET
from cStringIO import StringIO

api_token = "669gxifj8b1r5y71qcvcei0wu"
username = "haimavni"
from_address = "info@gbstories.org"
service_address = 'https://capi.inforu.co.il/mail/api.php?xml'

def send_xml(xml):
    url= service_address + '=' + xml
    response = requests.post(url) 
    return response

def create_xml(campaign_name="", from_address=from_address, from_name="", subject="", body="", recipients=""):
    body = re.sub(r'\&.+?;', '', body)
    #body = body.replace('&nbsp;', '')
    body = body.replace('#', '%23')
    template = '''
    <InfoMailClient>
        <SendEmails>
            <User>
                <Username>{username}</Username>
                <Token>{api_token}</Token>
            </User>
            <Message>
                <CampaignName>{campaign_name}</CampaignName>
                <FromAddress>{from_address}</FromAddress>
                <FromName>{from_name}</FromName>
                <Subject>{subject}</Subject>
                <Body><![CDATA[{body}]]></Body>
            </Message>
            <Recipients>
                {recipients}
            </Recipients>
            <Attachments>
            </Attachments>
        </SendEmails>
    </InfoMailClient>    
    '''
    result = template.format(username=username, api_token=api_token,
                           campaign_name=campaign_name, from_address=from_address, 
                           from_name=from_name, subject=subject, body=body, recipients=recipients)
    result = re.sub('\n\s*', '', result)
    return result

def create_recipients(recipient_list):
    result = ''
    if not isinstance(recipient_list, Iterable):
        recipient_list = [recipient_list]
    for r in recipient_list:
        s = '<Email address="{email}" fname="{fname}" lname="{lname}" />\n'.format(email=r.email,fname=r.first_name or "",lname=r.last_name or "")
        result += s
    return result

def send_email(campaign_name="", from_address=from_address, from_name="", subject="", body="", recipient_list=[]):
    recipients = create_recipients(recipient_list)
    xml = create_xml(campaign_name=campaign_name,from_address=from_address, 
                     from_name=from_name, subject=subject, body=body, recipients=recipients)
    result = send_xml(xml)
    comment("Send_email result: {}", result.text)
    stream = StringIO(result.text)
    tree = ET.parse(stream)
    if len(tree.findall('Error')) > 0:
        raise Exception('Mail delivery failed!')
    return dict(response=result.text, reason=result.reason)
    
