# Xenosaga Enemy Database
This is a modern, mobile optimized web application that hosts a searchable and sortable database of all the enemies in the Xenosaga PS2 series. Every enemy has detailed stats, weaknesses, loot drops, etc. 

Each game has been split into its own separate table/tab for organization.

## Framework
This website's frontend uses a mix of:

* [Dash Open Source](https://dash.plotly.com/) for the layout and HTML structures.
* [Dash AG-Grid](https://dash.plotly.com/dash-ag-grid) for the grid/table.

## How To Use
Each column in the grid can be resized, filtered, and sorted as you'd like. 

Clicking anywhere on a row will make a modal pop up that contains that selected enemy's stats.

## Data Sources
The data comes from the following sources, which I extracted using BeautifulSoup 4 and regex (except for Episode 2, which I had to do manually):

* Episode I https://gamefaqs.gamespot.com/ps2/519264-xenosaga-episode-i-der-wille-zur-macht/faqs/22927
** Items https://www.xenoserieswiki.org/wiki/List_of_Items_(XS1)
* Episode II https://www.ign.com/articles/2005/04/06/xenosaga-episode-ii-jenseits-von-gut-und-bose-enemy-faq-545281
** Items https://www.xenoserieswiki.org/wiki/List_of_Items_(XS2)
* Episode III https://gamefaqs.gamespot.com/ps2/929933-xenosaga-episode-iii-also-sprach-zarathustra/faqs/45192

I used ChatGPT to craft the regexes for me.

## Getting Started

### Docker
1. `docker pull strayingfromthepath:ludex`
2. `docker run ludex`

### Python
1. `git clone https://github.com/perfectly-preserved-pie/ludex.git`
2. `uv pip install .`
3. `gunicorn -b 0.0.0.0:80 --workers=4 --preload app:server`
