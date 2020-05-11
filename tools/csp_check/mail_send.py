# coding=utf-8

import os
import click
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


@click.command()
@click.option(
    "--user-email",
    "-y",
    envvar="user_email",
    required=False,
    default=None,
    type=click.STRING,
    help="user_email",
    metavar="user_email",
)
@click.option(
    "--smtp-pwd",
    "-s",
    envvar="smtp_pwd",
    required=False,
    default=None,
    type=click.STRING,
    help="smtp_pwd",
    metavar="smtp_pwd",
)
@click.option(
    "--report-path",
    "-r",
    envvar="report_path",
    required=False,
    default=None,
    type=click.STRING,
    help="report_path",
    metavar="report_path",
)
def main(user_email, smtp_pwd, report_path):
    """Configure the project according to the config file."""
    send_email_2_revcer(user_email, smtp_pwd, report_path)


def mail_report(mail_subject, mail_body, sender_pw, recver, attachments=[]):
    """Send email to recver by SSL."""

    smtpHost = 'smtp.ym.163.com'
    smtpPort = '25'
    sslPort = '994'
    fromMail = 'bot@rt-thread.org'
    username = 'bot@rt-thread.org'
    toMail = recver
    password = sender_pw

    # init mail
    encoding = 'utf-8'
    message = MIMEMultipart()
    message['Subject'] = Header(mail_subject, encoding)
    mail = MIMEText(mail_body.encode(encoding), 'plain', encoding)
    mail['From'] = fromMail
    mail['To'] = toMail
    mail['Date'] = formatdate()

    message.attach(mail)

    if len(attachments) != 0:
        for item in attachments:
            try:
                att = MIMEBase('application', 'octet-stream')
                att.set_payload(open(item, 'rb').read())
                encoders.encode_base64(att)
                att.add_header(
                    'Content-Disposition', 'attachment; filename="%s"' % os.path.basename(item))
                message.attach(att)
            except Exception as ex:
                print("===> Exception: %s" % (str(ex)))

    try:
        # ssl
        smtp = smtplib.SMTP_SSL(smtpHost, sslPort)
        smtp.ehlo()
        smtp.login(username, password)

        # send mail
        smtp.sendmail(fromMail, toMail, message.as_string())
        smtp.close()
        print('Email has been sent to %s successfully.' % toMail)
    except Exception as e:
        print(e)


def send_email_2_revcer(user_email, sender_pw, report_path):
    """send email to recver."""

    attachments = []

    file = report_path
    print(file)
    if os.path.exists(file):
        attachments.append(file)

    # subject and body
    mail_subject = "test result"
    mail_body = "sync log"

    print("User email: %s." % user_email)
    print(sender_pw)
    mail_report(mail_subject, mail_body, sender_pw, user_email, attachments)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('final error message: {0}\t'.format(e.message))
        exit(1)