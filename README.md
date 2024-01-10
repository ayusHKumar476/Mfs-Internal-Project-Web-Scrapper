INTERNAL PROJECT - Jan 9th 2024

Problem Statement:
Write Python script(s) to scrape the following location details of all the stores located in the US
for the given list of websites. The output should be an excel file with the required details.
Most of the websites have a 'Store Locator' page, which lists down nearby locations when an
address/zip code is entered. You are free to explore and choose any other approach you like,
but make sure to capture all the US locations for the provided websites.

NOTE: Refer https://gist.github.com/erichurst/7882666 for lang/long/zip data.

Required Details:
1. Store Name
2. Street Address
3. City
4. State
5. Zip Code
6. Phone Number
7. Latitude
8. Longitude

Websites to Scrape:
1. Starbucks: https://www.starbucks.com/store-locator
2. Pizza Hut: https://locations.pizzahut.com/
3. Burger King: https://www.bk.com/store-locator
4. Verizon Wireless: https://www.verizon.com/stores

NEXT STEP:
Create a Django Application, where an user creates an account using an email address.
Upon logging in, the web page consists of a dropdown which lists all the provided websites.
If the user is an admin / superuser, he / she will use the drop down to select any store, for which
the Django Application will scrap the data for that store and save the data to the database.
For a regular user, upon choosing a website from the dropdown, the user then clicks the
'Submit' button. Clicking the submit button, all the available stores for the selected option will be
displayed. There will be a send mail option, which will send the list of store data to the
registered email address.

Improvements:
1. Implement asynchronous task scheduling using redis and celery to perform tasks
(scraping the website, sending emails to users ) in the background.
2. Use celery bit to automatically scrap the websites and update the database on a regular
interval.
3. Use multiple queues for different tasks. Like, one queue for sending the email and
another one to scrap the websites and update the database.
4. Perform filtration of results using Django ORM and elastic search.

Note: Please containerize the application with docker set-up.