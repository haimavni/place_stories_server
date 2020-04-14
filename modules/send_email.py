import requests

api_token = "669gxifj8b1r5y71qcvcei0wu"
user_name = "haimavni"
from_address = "info@gbstories.org"

def send_xml(xml):
    headers = {'Content-Type': 'application/xml'}
    requests.post('http://www.my-website.net/xml', data=xml, headers=headers) 
    
def create_xml(campaign_name="",from_address=from_address,):
    template = '''
    <InfoMailClient>
        <SendEmails>
            <User>
                <Username>{USERNAME}</Username>
                <Token>{API_TOKEN}</Token>
            </User>
            <Message>
                <CampaignName>{campain_name}</CampaignName>
                <FromAddress>{from_address}</FromAddress>
                <FromName>{from_name}</FromName>
                <Subject>{subject}</Subject>
                <Body>{body}</Body>
            </Message>
            <Recipients>
                <!--<Group id="1" />-->
                <Email address="example1@example.com" fname="David" lname="Cohen" />
                <Email address="example2@example.com" var1="fun" var4="tel aviv" />
                <Email address="example2@example.com" />
            </Recipients>
            <Attachments>
                <Attachment name="Example" url="http://example.co.il/uploads/users/4/1.pdf"/>
            </Attachments>
        </SendEmails>
    </InfoMailClient>    
    '''