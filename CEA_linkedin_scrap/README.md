# LinkedIn Influencers Scraper

This is a Node.js application that can be used to scrape LinkedIn post of influencers and posts from a keyword search. It allows you to login to your LinkedIn account, collect your session cookies, and use them to scrape the posts you are interested in.


## Setup
Clone this repository to your local machine.

Make sure you have node installed. 

Run `npm install` to install the required dependencies.

You can call add your credential in the login.js file. This will create a saved-cookie.json file in the root directory of the project. This file will be used to store your session cookies after you login.

## Usage
The application can be used in the following way:

First, you need to login to your LinkedIn account by adding your credentials to the login(username, password) function in the login.js file. This function takes in your LinkedIn username and password, and returns your session cookies. Execute the following command `node login.js`. If it success you should see the saved-cookie.json file.

Next, you can use the getInfluencersPost(JSessionID, li_at, page) function to scrape the posts of the influencers you are interested in. 

This function takes in the JSESSIONID and li_at cookies returned by the login() function, as well as the page number you want to scrape. To scrapp the posts execute `node .` or `node index.js`. You should see the 2 new JSON files with the post of the week `influenceurs-posts-p0.json` and `keyword_posts-p0.json` .
