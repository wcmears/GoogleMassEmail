# GoogleMassEmail

NOTE THAT TO USE THIS YOU MUST GENERATE A CREDENTIALS.JSON FILE WITH OAUTH CREDENTIALS INSIDE OF A GOOGLE PROJECT AND REPLACE THE ONE THAT I HAVE HERE. Here is a reference on how to do it:
Creating project: https://cloud.google.com/resource-manager/docs/creating-managing-projects
Creating credentials: https://developers.google.com/workspace/guides/create-credentials

Written to take a google sheet with a list of emails and peoples names, along with a google doc with a message to be sent to all of those people, and mail merge/send emails. Most of the code in this repo is a combination of https://github.com/googleworkspace/python-samples/tree/main/docs/mail-merge and https://github.com/googleworkspace/python-samples/tree/main/gmail/snippet/send%20mail. I simply combined the two and generalized things to make it easy for anyone that wants to send mass emails. Here are a sample sheet and a sample doc to try with this code: 

https://docs.google.com/spreadsheets/d/18H2aYiN0_TqobcF7yk2O4t1CzrvHv3aPMxoJ9W-t6Y4/edit#gid=0

https://docs.google.com/document/d/1SawO9t2PZ88qCrD50UR5Ja6xsXnHjCDpk96_s2rInIk/edit