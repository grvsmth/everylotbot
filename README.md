# every tree bot

This is a fork of the *everylotbot* library by Neil Freeman.  It was created by [Angus B. Grieve-Smith](https://github.com/grvsmth), [Timm Dapper](https://github.com/tdapper), [Laura Silver](http://knish.me/author/) and [Elber Carneiro](https://www.linkedin.com/in/elbercarneiro) for the [2016 Trees Count! Data Jam](http://treescountdatajam.devpost.com/) sponsored by the New York City Parks Department.

*everytreebot* supports a Twitter bot that posts Google Streetview pictures of every property in an SQLite database.  It is currently running at [@everytreenyc](https://twitter.com/everytreenyc).

Existing instances of everylotbot: <a href="https://twitter.com/everylotnyc">@everylotnyc</a>, <a href="https://twitter.com/everylotchicago">@everylotchicago</a>, <a href="https://twitter.com/everylotsf">@everylotsf</a> and <a href="https://twitter.com/everylotla">@everylotla</a>. Since maps are instruments of power, these bots is a way of generating a tension between two different modes establishing power in urban space. [Read more about that](http://fakeisthenewreal.org/everylot/).

## What you'll need

Set up will be easier with at least a basic familiarity with the command line.

* A fresh Twitter account and a Twitter app, with registered keys
* A Google Streetview API token.
* A SQLite db with a row for every address you're interested in
* A place to run the bot (like a dedicated server or an Amazon AWS EC2 instance)

### Twitter keys

Creating a Twitter account should be straightforward. To create a Twitter app, register at [apps.twitter.com/](http://apps.twitter.com/). Once you have an app, you'll need to register your account with the app. [Twitter has details](https://dev.twitter.com/oauth/overview/application-owner-access-tokens).

Once you have the keys, save them in a file called `bots.yaml` that looks like this:

```yaml
apps:
    everylot:
        consumer_key: 123456890123456890
        consumer_secret: 123456890123456890123456890123456890
users:
    example_user_name:
        key: 123456890123456890-123456890123456890123456890123456890
        secret: 1234568901234568901234568901234568901234568
        app: everylot
```

Change `example_user_name` to your Twitter account screen name. The app name can also be anything you want.

This file can be in `json` format, if you wish.

### Streetview key

Visit the [Google Street View Image API](https://developers.google.com/maps/documentation/streetview/) page and click get a key.

Once you have the key, save it on its own line in your `bots.yaml` file like so:
```yaml
streetview: 123ABC123ABC123ABC123ABC
```

### Address database

Now, you'll need an SQLite database of trees.  For @everytreebot we exported a CSV from New York City's [Socrata site](https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh/data).  Here are the fields that we use in the bot:

* For general tracking:
** tree_id

* For composing the tweets:
** address
** health
** spc_common
** spc_latin
** status
** steward
** zip_city

* For Google Street View lookups:
** address
** boroname
** latitude
** longitude
** state
** zip_city

* We will need to add a column so that we don't tweet the same tree over and over again:
** tweeted

* We will also need an index unless you have a very small database or lots of spare time

Convert that CSV to SQLite using the SQLite command line:
````
sqlite3 trees.db

.mode csv
.import trees.csv
ALTER TABLE trees ADD COLUMN "tweeted" TEXT default "0";
CREATE INDEX i ON trees (tree_id);"
````

### Test the bot

Install this repository:
````
> git clone https://github.com/grvsmth/everytreebot.git
> cd everylotbot
````

For this step, make your new Twitter private.

You'll now have a command available called `everylot`. It works like this:
```
everylot SCREEN_NAME DATABASE.db --config bots.yaml
```

This will look in `DATABASE.db` for a table called lots, then sort that table by `id` and grab the first untweeted row.
It will check where Google thinks this address is, and make sure it's close to the coordinates in the table. Then it wil use the address (or the coordinates, if they seem more reliable) to find a Streetview image, then post a tweet with this image to `SCREEN_NAME`'s timeline. It will need the authorization keys in `bots.yaml` to do all this stuff.

`everylot` will, by default, try to use `address`, `city` and `state` fields from the database to search Google, then post to Twitter just the `address` field.

You can customize this based on the lay out of your database and the results you want. `everylot` has two options just for this:
* `--search-format` controls how address will be generated when searching Google
* `--print-format` controls how the address will be printed in the tweet

The default `search-format` is `{address}, {city}, {state}`, and the default `print-format` is `{address}`.

Search Google using the `address` field and the knowledge that all our data is in Kalamazoo, Michigan:
````
everylot everylotkalamazoo ./kalamazoo.db --config ./bots.yaml --search-format '{address}, Kalamazoo, MI'
````

Search Google using an address broken-up into several fields:
````
everylot everylotwallawalla walla2.db --config bots.yaml \
    --search-format '{address_number} {street_direction} {street_name} {street_suffix}, Walla Walla, WA'
````

In practice, you want to do the same thing when posting to Twitter, but you leave off the city and state because that's obvious to your followers:
````
everylot everylotwallawalla walla2.db --config bots.yaml \
    --search-format '{address_number} {street_direction} {street_name} {street_suffix}, Walla Walla, WA' \
    --print-format '{address_number} {street_direction} {street_name} {street_suffix}'
````

Include the property ID in the tweet, in brackets:
````
everylot everylotkalamazoo kalamazoo.db --config bots.yaml --search-format '{address}, Kalamazoo, MI \
    --print-format '{address} [{id}]'
````

While you're testing, it might be helpful to use the `--verbose` and `--dry-run` options. Also, use the `--id` option to force `everylot` to post a particular property.

````
everylot everylotpoughkeepsie pkpse.db --config bots.json --verbose --dry-run --id 12345
```

### A place for your bot to live

Now, you just need a place for the bot to live. This needs to be a computer that's always connected to the internet, and that you can set up to run tasks for you. You could use a virtual server hosted at a vendor like Amazon AWS, Linode or DigitalOcean, or space on a web server.

Put the `bots.yaml` file and your database in the same folder on your server, then download this repository and install it as above.

Next, you want to set up the bot to tweet regularly. If this is a Linux machine, you can do this with crontab:
```
crontab -e
1,31 * * * * $HOME/.local/bin/everylot screen_name $HOME/path/to/lots.db -s '{address} Anytown USA'
```

(Note that you can omit the `bots.yaml` config file argument if it's located in the home directory.)

### Walkthrough for Baltimore

This walks through the steps of creating an example bot. It uses text-based command line commands, but most of these tasks could be done in programs with graphic interfaces.

First step is to find the data: google "Baltimore open data", search for parcels on [data.baltimorecity.gov](https://data.baltimorecity.gov).

````bash
# Also works to download through the browser and unzip with the GUI
> curl -G https://data.baltimorecity.gov/api/geospatial/rb22-mgti \
    -d method=export -d format=Shapefile -o baltimore.zip
> unzip baltimore.zip
Archive:  baltimore.zip
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shp
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shx
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.dbf
  inflating: geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.prj

# Get a simpler name
> mv geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shp baltimore.shp
> mv geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.shx baltimore.shx
> mv geo_export_9f6b494d-b617-4065-a8e7-23adb09350bc.dbf baltimore.dbf

# Find the address and ID fields. It looks like we'll want to use a combination of
# blocknum and parcelnum to get a unique ID for each property
> ogrinfo baltimore.shp baltimore -so
INFO: Open of `baltimore.shp'
      using driver `ESRI Shapefile' successful.
...
parcelnum: String (254.0)
...
blocknum: String (254.0)
fulladdr: String (254.0)
...

# Create an SQLite database, reprojecting the geometries to WGS84. Keep only the desired fields
> ogr2ogr -f SQLite baltimore_raw.db baltimore.shp baltimore -t_srs EPSG:4326
    -nln baltimore -select parcelnum,blocknum,fulladdr

# Convert feature centroid to integer latitude, longitude
# Pad the block number and parcel number so sorting works
# Result will have these columns: id, address, lon, lat, tweeted
> ogr2ogr -f SQLite baltimore.db baltimore_raw.db -nln lots -nlt NONE -dialect sqlite
    -sql "WITH A as (
        SELECT blocknum,
        parcelnum,
        fulladdr AS address,
        ST_Centroid(GeomFromWKB(Geometry)) centroid
        FROM baltimore
        WHERE blocknum IS NOT NULL AND parcelnum IS NOT NULL
    ) SELECT (substr('00000' || blocknum, -5, 5)) || (substr('000000000' || parcelnum, -9, 9)) AS id,
    address,
    ROUND(X(centroid), 5) lon,
    ROUND(Y(centroid), 5) lat,
    0 tweeted
    FROM A;"

# Add indexes and clean up sqlite database.
> sqlite3 baltimore.db "CREATE INDEX i ON lots (id);"
> sqlite3 baltimore.db "DELETE FROM lots WHERE id = '' OR id IS NULL; VACUUM"

> everylot everylotbaltimore baltimore.db --search-format "{address}, Baltimore, MD"
````
