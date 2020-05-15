import os
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


def main():
    """Configure the project according to the config file."""
    if 'SMTP_PWD' in os.environ and 'USER_EMAIL' in os.environ and "FROM_EMAIL" in os.environ:
        smtp_pwd = os.environ['SMTP_PWD']
        user_email = os.environ['USER_EMAIL']
        report_path = "report.html"
        send_email_2_revcer(user_email, smtp_pwd, report_path)
    else:
        print("Can't send email, Please set env 'SMTP_PWD', 'USER_EMAIL', 'FROM_EMAIL'.")

    try:
        with open("report.html", "r") as f:
            report_cont = f.read()
        if report_cont.find("failed results-table-row") != -1:
            print("\nChip support package test failed, please check it and repair!")
            exit(1)
    except Exception as e:
        print("\nError message : {0}.".format(e))


def mail_report(mail_subject, mail_body, sender_pw, recver, attachments=[]):
    """Send email to recver by SSL."""

    smtp_host = 'smtp.ym.163.com'
    smtp_port = '25'
    ssl_port = '994'

    from_mail = os.environ["FROM_EMAIL"]
    user_name = os.environ["FROM_EMAIL"]

    to_mail = recver
    password = sender_pw

    # init mail
    encoding = 'utf-8'
    message = MIMEMultipart()
    message['Subject'] = Header(mail_subject, encoding)
    mail = MIMEText(mail_body.encode(encoding), 'plain', encoding)
    mail['From'] = from_mail
    mail['To'] = to_mail
    mail['Date'] = formatdate()

    message.attach(mail)

    if len(attachments) != 0:
        for item in attachments:
            try:
                att = MIMEBase('application', 'octet-stream')
                att.set_payload(open(item, 'rb').read())
                encoders.encode_base64(att)
                att.add_header(
                    'Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(item)))
                message.attach(att)
            except Exception as ex:
                print("===> Exception: {0}".format(str(ex)))

    try:
        # ssl
        smtp = smtplib.SMTP_SSL(smtp_host, ssl_port)
        smtp.ehlo()
        smtp.login(user_name, password)

        # send mail
        smtp.sendmail(from_mail, to_mail, message.as_string())
        smtp.close()
        print('\nEmail has been sent successfully.')
    except Exception as e:
        print("\nError message : {0}.".format(e))



def send_email_2_revcer(user_email, sender_pw, report_path):
    """send email to recver."""

    attachments = []

    file = report_path
    if os.path.exists(file):
        attachments.append(file)

    # subject and body
    mail_subject = "test result"
    mail_body = "sync log"

    mail_report(mail_subject, mail_body, sender_pw, user_email, attachments)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('final error message: {0}\t'.format(e.message))
        exit(1)
