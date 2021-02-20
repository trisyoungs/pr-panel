import flask, os, re
from github import Github
from MarkupPy import markup

# Create our Flask app
app = flask.Flask(__name__)
app.config["DEBUG"] = True

# Create a Github object with our personal access token which we take from an environment
# variable named GITHUB_TOKEN
gh = Github(os.getenv("GITHUB_TOKEN"))

# Set up a stage map to allow us to condense a set of checks (named, e.g., after their Azure displayName)
stageMap = { "CQ": ".*Code Quality Checks.*", "B": ".*Build.*", "T": ".*Tests.*" }

def getPRData(userRepo, stageMap):
    """Get PR data for a specific user/repo"""
    repo = None
    try:
        repo = gh.get_repo(userRepo)
    except:
        print(f"Couldn't retrieve repo data for '{userRepo}'.\n")
        return

    # Obtain PR info for this repo, and extract the info we want
    pulls = repo.get_pulls(state='open', sort='created', base='develop')

    # If there are no open PRs, can exit now without appending anything to the list
    if len(list(pulls)) == 0:
        return

    # Extract data from the array
    prInfo = []
    for pr in pulls:
        # Store basic information
        newInfo = {}
        newInfo["number"] = pr.number
        newInfo["title"] = pr.title

        # Get checks information, and create a simplified representation to store
        checksInfo = {}
        last_commit = [commit for commit in pr.get_commits()][-1]
        check_suites = last_commit.get_check_suites()
        for cs in check_suites:
            # Is a general conclusion for the check suite available
            if cs.conclusion and not "conclusion" in newInfo:
                newInfo["conclusion"] = cs.conclusion;

            # Extract data from individual check runs
            for cr in cs.get_check_runs():
                # Does this check run match any mapping in the stageMap?
                for stageName,pattern in stageMap.items():
                    if not re.match(pattern, cr.name):
                        continue

                    # What is the status / result of this stage?
                    if cr.status == "queued" or cr.status == "in_progress":
                        status = cr.status
                    else:
                        status = cr.conclusion

                    # Append this check run to our stage info
                    if stageName in checksInfo:
                        checksInfo[stageName].append(status)
                    else:
                        checksInfo[stageName] = [ status ]

        # Add check run information to the list
        if checksInfo:
            newInfo["checks"] = checksInfo
        prInfo.append(newInfo)

    return prInfo

def prDataToHTML(prData, page, oneLiner):
    # Start a list for the active PRs in this repo
    page.ul(class_="prList")

    # Loop over PRs
    for pr in prData:
        # Reset variables
        renderStatusChecks = True

        # Header line (PR number, title, status)
        html = oneLiner.div(f"#{pr['number']}", class_="prNumber")
        html += oneLiner.div(pr['title'], class_="prTitle")
        if not "conclusion" in pr:
            html += oneLiner.div(class_="iconUnknown")
        elif pr['conclusion'] == "success":
            html += oneLiner.div(class_="iconSuccess")
            renderStatusChecks = False
        elif pr['conclusion'] == "failure":
            html += oneLiner.div(class_="iconFailure")
        elif pr['conclusion'] == "in_progress":
            html += oneLiner.div(class_="iconInProgress")

        # The test # TODO:

        # Add a list item
        page.li(oneLiner.div(html, class_="prGrid"))

    page.ul.close()


@app.route('/', methods=['GET'])
def home():
    prData = {}
    prData["disorderedmaterials/dissolve"] = getPRData("disorderedmaterials/dissolve", stageMap)
    #prData["disorderedmaterials/dissolve"] = [{'number': 516, 'title': 'Protein force fields'}, {'number': 541, 'title': 'Tidy SpeciesIntra Base', 'conclusion': 'failure', 'checks': {'CQ': ['success', 'success', 'success'], 'B': ['failure', 'success', 'success', 'success']}}, {'number': 543, 'title': 'Move MasterIntra terms out of lists and into vectors.', 'conclusion': 'success', 'checks': {'CQ': ['success', 'success', 'success'], 'B': ['success', 'success', 'success', 'success'], 'T': ['success', 'success']}}, {'number': 550, 'title': 'UFF', 'conclusion': 'failure', 'checks': {'CQ': ['success', 'success', 'success'], 'B': ['success', 'success', 'success', 'success'], 'T': ['failure']}}]
    #print(prData)
    items = ( "<div class='repoHeader'>projectdissolve/dissolve</div><ul class='prList'><li><div class='prGrid'><div class='prNumber'>#342</div><div class='prTitleg'>Alpha</div><div>TICK</div><div>GAP</div><div>information</div></div></li><li>Beta</li><li>Gamma</li></ul>", "<div class='repoHeader'>projectdissolve/jv2</div><ul class='prList'><li>Delta</li><li>Epsilon</li><li>Pi</li></ul>" )

    # Init the page
    ol = markup._oneliner()
    page = markup.page()
    page.init( title="PR Panel", css=('static/css/main.css'))

    # Loop over repos in the dict and generate html for its PRs
    for repoName,prs in prData.items():
        # Draw header
        page.div(repoName, class_="repoHeader")
        print(prs)
        prDataToHTML(prs, page, ol)

    return str(page)

# Run the app
app.run()
