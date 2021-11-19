# Maki-Bot
Web-based Inquiry Chatbot using NLP with Tensorflow for DHVSU Admission Inquiries


Run launcher.py to use

To login in admin side, use this account:
- username: sample admin
- password: 123


# Current problems occuring when running Maki Bot:
They only appear for certain reasons that can be easily avoided (this might just be happening specifically because of my 8 year old laptop).
1. When applicant logins using google account, it will trigger a early token warning. This problem might only happen specifically on my laptop.

- REASON: If the date and time of the device used to launch is not sync, the token warning will get triggered. My laptop's date and time always gets out of sync whenever I use ccleaner to clean my cache. 

- FIX: re-sync date and time.

# If the device used for this system used the "self-learning" feature for the first time, the new chosen question and answer will not take effect at first. But after the second time the feature gets used again, the previous chosen question and answer and another new chosen question and answer will take effect. Don't misunderstand that this issue will always persist, it will only persist when the feature is used in the device for the first time. 
