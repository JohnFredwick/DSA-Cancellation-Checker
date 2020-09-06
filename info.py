#################################################################
#                                                               #
# Update the following variables with your own personal details #
#                                                               #
#################################################################


########################### DSA DATA ############################

# Driving license number (Example: ABCDE0123456F78GH)
licenceNumber = ""

# Application reference number (Found in confirmation email after booking)
referenceNumber = ""


########################## EMAIL DATA ###########################

# The email addresses you wish to send notifications to
emailAddresses = [""]

# Subject of email sent
emailSubject = "DSA Cancellations"

# Enter your email account details here so that the script can send emails
emailUsername = ""
emailPassword = ""

# Change this to your own mail provider's SMTP server
emailSMTPserver = "smtp-mail.outlook.com"
# Outlook: smtp-mail.outlook.com
# Gmail: smtp.gmail.com
# Yahoo Mail: smtp.mail.yahoo.com


########################### APP DATA ############################

# Time in seconds between checks for cancellations
refreshInterval = 30

# Path to chrome driver for Selenium to work
chromeDriverPath = "chromedriver85.exe"
