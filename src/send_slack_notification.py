import json
import shlex
import urllib2
import logging
import os

# Mapping CloudFormation status codes to colors for Slack message attachments
# Status codes from http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html
STATUS_COLORS = {
    'CREATE_COMPLETE': 'good',
    'CREATE_IN_PROGRESS': 'good',
    'CREATE_FAILED': 'danger',
    'DELETE_COMPLETE': 'good',
    'DELETE_FAILED': 'danger',
    'DELETE_IN_PROGRESS': 'good',
    'ROLLBACK_COMPLETE': 'warning',
    'ROLLBACK_FAILED': 'danger',
    'ROLLBACK_IN_PROGRESS': 'warning',
    'UPDATE_COMPLETE': 'good',
    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': 'good',
    'UPDATE_IN_PROGRESS': 'good',
    'UPDATE_ROLLBACK_COMPLETE': 'warning',
    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': 'warning',
    'UPDATE_ROLLBACK_FAILED': 'danger',
    'UPDATE_ROLLBACK_IN_PROGRESS': 'warning'
}

# List of properties from ths SNS message that will be included in a Slack message
SNS_PROPERTIES_FOR_SLACK = [
    'Timestamp',
    'StackName'
]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
SLACK_MSG_TEXT = os.environ['SLACK_MSG_TEXT']
SLACK_MSG_USER = os.environ['SLACK_MSG_USER']
SLACK_MSG_EMOJI = os.environ['SLACK_MSG_EMOJI']
SLACK_WEB_HOOK_URL = os.environ['SLACK_WEB_HOOK_URL']


def handler(event, context):

    # records = event['Records']
    # first_record = records[0]
    # sns = first_record['Sns']
    # sns_message = sns['Message']
    sns_message = event['Records'][0]['Sns']['Message']

    # using shlex to split the cfn message into a dictionary
    cfn_msg_dict = dict(token.split('=', 1) for token in shlex.split(sns_message))

    # ignore messages that do not pertain to the Stack as a whole
    if not cfn_msg_dict['ResourceType'] == 'AWS::CloudFormation::Stack':
        return

    message_to_slack = get_message_for_slack(cfn_msg_dict)
    data = json.dumps(message_to_slack)
    req = urllib2.Request(SLACK_WEB_HOOK_URL, data, {'Content-Type': 'application/json'})
    urllib2.urlopen(req)

    return {'message': 'Notified'}


def get_message_for_slack(cfn_msg_dict):
    attachment = get_attachment(cfn_msg_dict)
    message_to_slack = {
        'icon_emoji': SLACK_MSG_EMOJI,
        'username': SLACK_MSG_USER,
        'text': SLACK_MSG_TEXT,
        'attachments': attachment,
        'channel': SLACK_CHANNEL
    }
    return message_to_slack


def get_attachment(cfn_msg_dict):
    title = "Stack: {} has reached status {}".format(cfn_msg_dict['StackName'], cfn_msg_dict['ResourceStatus'])
    color = STATUS_COLORS.get(cfn_msg_dict['ResourceStatus'], '#000000')
    attachment = [{
        'fallback': SLACK_MSG_TEXT,
        'title': title,
        'fields': get_fields_for_attachment(cfn_msg_dict),
        'color': color,
    }]
    return attachment


def get_fields_for_attachment(cfn_msg_dict):
    fields = []
    for k, v in cfn_msg_dict.items():
        if k in SNS_PROPERTIES_FOR_SLACK:
            fields.append({"title": k, "value": v, "short": "true"})
    return fields
