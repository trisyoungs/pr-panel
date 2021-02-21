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
stageMap = { "QC": ".*Code Quality Checks.*", "Build": ".*Build.*", "Test": ".*Tests.*" }

def getPRData(userRepo, stageMap, test=False):
    """Get PR data for a specific user/repo"""
    if test:
        return [ {'number': 516, 'title': 'Protein force fields'}, {'number': 541, 'title': 'Tidy SpeciesIntra Base', 'conclusion': 'failure', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['failure', 'success', 'success', 'success']}}, {'number': 543, 'title': 'Move MasterIntra terms out of lists and into vectors.', 'conclusion': 'success', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['success', 'success', 'success', 'success'], 'Test': ['success', 'success']}}, {'number': 550, 'title': 'UFF', 'conclusion': 'failure', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['success', 'success', 'success', 'success'], 'Test': ['failure']}}]

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
        showStatusChecks = True

        # Start a new list item and grid
        page.li()
        page.div(class_="prGrid")

        # Header line (PR number, title, status)
        # -- Number
        page.div(class_="prNumberContainer")
        page.div(f"#{pr['number']}", class_="prNumber")
        page.div.close()
        # -- Title
        page.div(pr['title'], class_="prTitle")
        # -- Status Icon
        page.div(class_="prStatusContainer")
        if not "conclusion" in pr:
            page.div("", class_="prStatus iconUnknown")
        elif pr['conclusion'] == "success":
            page.div("", class_="prStatus iconSuccess")
            showStatusChecks = False
        elif pr['conclusion'] == "failure":
            page.div("", class_="prStatus iconFailure")
        elif pr['conclusion'] == "in_progress":
            page.div("", class_="prStatus iconInProgress")
        else:
            page.div("", class_="prStatus iconUnknown")
        page.div.close()

        # Status checks line
        if showStatusChecks:
            # Add on the first div (empty), and open the next one
            page.div("", class_="checkBlank")
            page.div(class_="prChecks")

            # Do we have checks to go through?
            if "checks" in pr:
                # Loop over checks
                for check,results in pr["checks"].items():
                    # Add stage indicator
                    page.div(check, class_="checkName")

                    # Draw check indicators in sequence
                    for result in results:
                        page.div(class_="checkStatusContainer")
                        if result == "queued":
                            page.img(src="static/img/queued.svg", class_="checkIcon")
                        elif result == "in_progress":
                            page.img(src="static/img/in_progress.svg", class_="checkIcon")
                        elif result == "skipped":
                            page.img(src="static/img/skipped.svg", class_="checkIcon")
                        elif result == "success":
                            page.img(src="static/img/success.svg", class_="checkIcon")
                        elif result == "failure":
                            page.img(src="static/img/failure.svg", class_="checkIcon")
                        else:
                            page.img(src="static/img/unknown.svg", class_="checkIcon")
                        page.div.close()
            else:
                page.span("No checks have been run for this PR.", class_="checkStatus")

        # Close our elements
        page.div.close()
        page.li.close()

    page.ul.close()


@app.route('/', methods=['GET'])
def home():
    prData = {}
    prData["disorderedmaterials/dissolve"] = getPRData("disorderedmaterials/dissolve", stageMap, True)

    # Init the page
    ol = markup._oneliner()
    page = markup.page()
    page.init( title="PR Panel", css=('static/css/main.css'))

    # Loop over repos in the dict and generate html for its PRs
    for repoName,prs in prData.items():
        # Draw header
        page.div(repoName, class_="repoHeader")
        prDataToHTML(prs, page, ol)

    return str(page)

# Run the app
app.run()
