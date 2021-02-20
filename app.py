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
    prData = []
    prData.append({'dissolve': [{'number': 516, 'title': 'Protein force fields'}, {'number': 541, 'title': 'Tidy SpeciesIntra Base', 'conclusion': 'failure', 'checks': {'CQ': ['success', 'success', 'success'], 'B': ['failure', 'success', 'success', 'success']}}, {'number': 543, 'title': 'Move MasterIntra terms out of lists and into vectors.', 'conclusion': 'success', 'checks': {'CQ': ['success', 'success', 'success'], 'B': ['success', 'success', 'success', 'success'], 'T': ['success', 'success']}}, {'number': 550, 'title': 'UFF', 'conclusion': 'failure', 'checks': {'CQ': ['success', 'success', 'success'], 'B': ['success', 'success', 'success', 'success'], 'T': ['failure']}}]})
    print(prData)
    items = ( "<div class='repoHeader'>projectdissolve/dissolve</div><ul class='prList'><li><div class='prGrid'><div class='prNumber'>#342</div><div class='prTitle'>Alpha</div><div>TICK</div><div>GAP</div><div>information</div></div></li><li>Beta</li><li>Gamma</li></ul>", "<div class='repoHeader'>projectdissolve/jv2</div><ul class='prList'><li>Delta</li><li>Epsilon</li><li>Pi</li></ul>" )

    # Init the page
    page = markup.page()
    page.init( title="PR Panel", css=('static/css/main.css'))

    # Loop over repos and construct a list
    page.ul( class_='repoList' )
    page.li( items, class_='' )
    page.ul.close()

    return str(page)

# Run the app
app.run()
