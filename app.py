import flask, re, toml
from github import Github
from airium import Airium

# Parse the configuration file
config = toml.load('config.toml')

# Create our Flask app
app = flask.Flask(__name__)
#app.config["DEBUG"] = True

# Create a Github object with our personal access token which we take from an environment
# variable named GITHUB_TOKEN
gh = Github(config['token'])

def getPRData(userRepo, test=False):
    """Get PR data for a specific user/repo"""
    if test:
        return [ {'number': 516, 'title': 'Protein force fields'}, {'number': 541, 'title': 'Tidy SpeciesIntra Base', 'conclusion': 'failure', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['failure', 'success', 'success', 'success']}}, {'number': 543, 'title': 'Move MasterIntra terms out of lists and into vectors.', 'conclusion': 'success', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['success', 'success', 'success', 'success'], 'Test': ['success', 'success']}}, {'number': 550, 'title': 'UFF', 'conclusion': 'failure', 'checks': {'QC': ['success', 'success', 'success'], 'Build': ['success', 'success', 'success', 'success'], 'Test': ['failure']}}]

    repo = None
    try:
        repo = gh.get_repo(userRepo)
    except:
        print(f"Couldn't retrieve repo data for '{userRepo}'.\n")
        return []

    # Obtain PR info for this repo, and extract the info we want
    pulls = repo.get_pulls(state='open', sort='created', direction='asc', base='develop')

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
                for stage in config['stage']:
                    if not re.match(stage['re'], cr.name):
                        continue

                    # What is the status / result of this stage?
                    if cr.status == "queued" or cr.status == "in_progress":
                        status = cr.status
                    else:
                        status = cr.conclusion

                    # Append this check run to our stage info
                    if stage['name'] in checksInfo:
                        checksInfo[stage['name']].append(status)
                    else:
                        checksInfo[stage['name']] = [ status ]

        # Add check run information to the list
        if checksInfo:
            newInfo["checks"] = checksInfo
        prInfo.append(newInfo)

    return prInfo

def prDataToHTML(prData, page):
    # Start a list for the active PRs in this repo
    with page.body().ul(class_="prList"):

        # Loop over PRs
        for pr in prData:
            # Reset variables
            showStatusChecks = True

            # Start a new list item and grid
            with page.li().div(class_="prGrid"):

                # Header line (PR number, title, status)
                # -- Number
                with page.div(class_="prNumberContainer").div(class_="prNumber"):
                    page(f"#{pr['number']}")

                # -- Title
                with page.div(class_="prTitle"):
                    page(pr['title'])

                # -- Status Icon
                if not "conclusion" in pr:
                    page.div(class_="prStatusContainer").div(class_="prStatus iconUnknown")
                elif pr['conclusion'] == "success":
                    page.div(class_="prStatusContainer").div(class_="prStatus iconSuccess")
                    showStatusChecks = False
                elif pr['conclusion'] == "failure":
                    page.div(class_="prStatusContainer").div(class_="prStatus iconFailure")
                elif pr['conclusion'] == "in_progress":
                    page.div(class_="prStatusContainer").div(class_="prStatus iconInProgress")
                else:
                    page.div(class_="prStatusContainer").div(class_="prStatus iconUnknown")

                # Status checks line
                if showStatusChecks:
                    # Add on the first div (empty), and open the next one
                    page.div(class_="checkBlank")
                    with page.div(class_="prChecks"):
                        # Do we have checks to go through?
                        if "checks" in pr:
                            # Loop over checks
                            for check,results in pr["checks"].items():
                                # Add stage indicator
                                with page.div(class_="checkName"):
                                    page(check)

                                # Draw check indicators in sequence
                                for result in results:
                                    with page.div(class_="checkStatusContainer"):
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
                        else:
                            with page.div(class_="checkStatus"):
                                page("No checks have been run for this PR.")

@app.route('/', methods=['GET'])
def home():
    # Set up the page
    page = Airium()
    page('<!DOCTYPE html>')
    with page.html():
        with page.head():
            page.title("PR Panel")
            page.link(rel="stylesheet", href='static/css/main.css')
            page.meta(http_equiv="refresh", content="120")

    # Loop over defined repos
    for repo in config['repo']:
        # Add header
        with page.body().div(class_="repoHeader"):
            page(repo['id'])

        # Get PR data for the repo
        prs = []
        try:
            prs = getPRData(repo['id'])
        except:
            with page.body().div():
                page("Failed to get PR info for this repo.")

        if len(prs):
            prDataToHTML(prs, page)

    # Need to tweak the generated html slightly to change the string "http_equiv" to "http-equiv" - we couldn't
    # do this earlier as the '-' is interpreted as a minus in the key.
    html = str(page).replace("http_equiv", "http-equiv")

    return html

# Run the app
app.run()
