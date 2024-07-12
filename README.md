
# CS50 Finance

## Background

If you’re not quite sure what it means to buy and sell stocks (i.e., shares of a company), head [here](https://www.investopedia.com/terms/s/stock.asp) for a tutorial.

You’re about to implement C$50 Finance, a web app via which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks’ actual prices and portfolios’ values, it will also let you buy (okay, “buy”) and sell (okay, “sell”) stocks by querying for stocks’ prices.

Indeed, there are tools (one is known as IEX) that let you download stock quotes via their API (application programming interface) using URLs like `https://api.iex.cloud/v1/data/core/quote/nflx?token=API_KEY`. Notice how Netflix’s symbol (NFLX) is embedded in this URL; that’s how IEX knows whose data to return. That link won’t actually return any data because IEX requires you to use an API key, but if it did, you’d see a response in JSON (JavaScript Object Notation) format like this:

## Getting Started

Log into cs50.dev, click on your terminal window, and execute `cd` by itself. You should find that your terminal window’s prompt resembles the below:

$

Next execute:

```
wget https://cdn.cs50.net/2024/x/psets/9/finance.zip
```

in order to download a ZIP called finance.zip into your codespace.

Then execute:

```
unzip finance.zip
```

to create a folder called finance. You no longer need the ZIP file, so you can execute:

```
rm finance.zip
```

and respond with “y” followed by Enter at the prompt to remove the ZIP file you downloaded.

Now type:

```
cd finance
```

followed by Enter to move yourself into (i.e., open) that directory. Your prompt should now resemble the below:

```
finance/ $
```

Execute `ls` by itself, and you should see a few files and folders:

```
app.py  finance.db  helpers.py  requirements.txt  static/  templates/
```

If you run into any trouble, follow these same steps again and see if you can determine where you went wrong!

## Running

Start Flask’s built-in web server (within finance/):

```
$ flask run
```

Visit the URL outputted by flask to see the distribution code in action. You won’t be able to log in or register, though, just yet!

Within finance/, run `sqlite3 finance.db` to open finance.db with sqlite3. If you run `.schema` in the SQLite prompt, notice how finance.db comes with a table called users. Take a look at its structure (i.e., schema). Notice how, by default, new users will receive $10,000 in cash. But if you run `SELECT * FROM users;`, there aren’t (yet!) any users (i.e., rows) therein to browse.

Another way to view finance.db is with a program called phpLiteAdmin. Click on finance.db in your codespace’s file browser, then click the link shown underneath the text “Please visit the following link to authorize GitHub Preview”. You should see information about the database itself, as well as a table, users, just like you saw in the sqlite3 prompt with .schema.

## Understanding

### app.py

Open up app.py. Atop the file are a bunch of imports, among them CS50’s SQL module and a few helper functions. More on those soon.

After configuring Flask, notice how this file disables caching of responses (provided you’re in debugging mode, which you are by default in your code50 codespace), lest you make a change to some file but your browser not notice. Notice next how it configures Jinja with a custom “filter,” usd, a function (defined in helpers.py) that will make it easier to format values as US dollars (USD). It then further configures Flask to store sessions on the local filesystem (i.e., disk) as opposed to storing them in...

Thereafter are a whole bunch of routes, only two of which are fully implemented: login and logout. Read through the implementation of login first. Notice how it uses db.execute (from CS50’s library) to query finance.db. And notice how it uses check_password_hash to compare hashes of users’ passwords. Also notice how login “remembers” that a user is logged in by storing his or her user_id, an INTEGER, in session. That way, any of this file’s routes can check which user, if any, is logged in. Finally, noti...

Notice how most routes are “decorated” with `@login_required` (a function defined in helpers.py too). That decorator ensures that, if a user tries to visit any of those routes, he or she will first be redirected to login so as to log in.

Notice too how most routes support GET and POST. Even so, most of them (for now!) simply return an “apology,” since they’re not yet implemented.

### helpers.py

Next take a look at helpers.py. Ah, there’s the implementation of apology. Notice how it ultimately renders a template, apology.html. It also happens to define within itself another function, escape, that it simply uses to replace special characters in apologies. By defining escape inside of apology, we’ve scoped the former to the latter alone; no other functions will be able (or need) to call it.

Next in the file is login_required. No worries if this one’s a bit cryptic, but if you’ve ever wondered how a function can return another function, here’s an example!

Thereafter is lookup, a function that, given a symbol (e.g., NFLX), returns a stock quote for a company in the form of a dict with two keys: price, whose value is a float; and symbol, whose value is a str, a canonicalized (uppercase) version of a stock’s symbol, irrespective of how that symbol was capitalized when passed into lookup.

Please note. If you began this problem in 2023, note that lookup no longer returns a key of name, so be sure that you remove that from any query that expects it. No name needs to be displayed on any page.

Last in the file is usd, a short function that simply formats a float as USD (e.g., 1234.56 is formatted as $1,234.56).

### requirements.txt

Next take a quick look at requirements.txt. That file simply prescribes the packages on which this app will depend.

## License

MIT License
