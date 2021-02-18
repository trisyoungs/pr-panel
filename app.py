import flask
from github import Github
from components import GitHubPRPanel
import os
from MarkupPy import markup

# Create our Flask app
app = flask.Flask(__name__)
app.config["DEBUG"] = True

# Create a Github object with our personal access token which we take from an environment
# variable named GITHUB_TOKEN
gh = Github(os.getenv("GITHUB_TOKEN"))
prget = GitHubPRPanel.GitHubPRPanel(gh)

# Set up a stage map to allow us to condense a set of checks (named, e.g., after their Azure displayName)
stageMap = { "CQ": ".*Code Quality Checks.*", "B": ".*Build.*", "T": ".*Tests.*" }


@app.route('/', methods=['GET'])
def home():
    #prData = {}
    #prData["dissolve"] = prget.getPRData("disorderedmaterials/dissolve", stageMap)
    items = ( "Item one", "Item two", "Item three", "Item four" )
    paras = ( "This was a fantastic list.", "And now for something completely different." )
    images = ( "thumb1.jpg", "thumb2.jpg", "more.jpg", "more2.jpg" )

    p = markup.page()
    p.init( title="My title",
               css=( 'one.css', 'two.css' ),
               header="Something at the top",
               footer="The bitter end." )

    p.ul( class_='mylist' )
    p.li( items, class_='myitem' )
    p.ul.close( )

    p.p( paras )
    p.img( src=images, width=100, height=80, alt="Thumbnails" )

    return str(p)
    #print(p.html())
    #return "<h1>SOME TEST SHITddd</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"

# Run the app
app.run()
