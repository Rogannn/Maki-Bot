# Maki-Bot
Web-based Inquiry Chatbot using NLP with Tensorflow for DHVSU Admission Inquiries


Run launcher.py to use

To login in admin side, use this account:
- username: admin1
- password: Samplepassword123

# How to install and use
- Make sure that you have Python and pip installed on your computer and the path is configured.
1. Download the zip file
2. Unzip the file to a path you desire.
3. Open cmd(in administrator mode to be sure).
4. Type and enter the path to the file ex. cd C:\Users\Rogel\desktop\Maki-Bot-main
- Install the external python libraries (its on you if you want to use virtual environment or not)
6. Type and enter pip install -r requirements.txt
- Download the nltk(optional)
7. Type and enter nltk.download('popular')
- Access the website
8. Type and enter server.py
9. Type in your browser's url the server.

# Current problems occuring when running Maki Bot:
They only appear for certain reasons that can be easily avoided (this might just be happening specifically because of my 8 year old laptop).
1. When applicant logins using google account, it will trigger a early token warning. This problem might only happen specifically on my laptop.

- REASON: If the date and time of the device used to launch is not sync, the token warning will get triggered. My laptop's date and time always gets out of sync whenever I use ccleaner to clean my cache. 

- FIX: re-sync date and time.
